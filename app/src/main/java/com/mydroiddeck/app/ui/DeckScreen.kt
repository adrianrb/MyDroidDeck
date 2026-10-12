package com.mydroiddeck.app.ui

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.mydroiddeck.app.R
import com.mydroiddeck.app.model.ActionRequest
import com.mydroiddeck.app.model.DeckButton
import com.mydroiddeck.app.model.DeckProfile
import com.mydroiddeck.app.net.ApiClient
import com.mydroiddeck.app.net.TokenStore
import com.mydroiddeck.app.ui.theme.MyDroidDeckTheme
import kotlinx.coroutines.launch
import retrofit2.HttpException

private const val GRID_COLUMNS = 4
private const val BUTTON_ICON_SIZE = 42
private const val BUTTON_CORNER_RADIUS = 16

/** Loads the profiles from the server and renders the selected one as a deck. */
@Composable
fun DeckScreen(
    onUnauthorized: () -> Unit = {},
    themeMode: ThemeMode = ThemeMode.SYSTEM,
    onThemeModeChange: (ThemeMode) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    var loading by remember { mutableStateOf(true) }
    var failed by remember { mutableStateOf(false) }
    var profiles by remember { mutableStateOf(emptyList<DeckProfile>()) }
    var selected by remember { mutableStateOf(0) }
    var status by remember { mutableStateOf<DeckStatus?>(null) }
    var lastLabel by remember { mutableStateOf<String?>(null) }
    var reloads by remember { mutableStateOf(0) }
    var showServerDialog by remember { mutableStateOf(false) }
    val icons = rememberDeckIconCache()
    val scope = rememberCoroutineScope()

    LaunchedEffect(reloads) {
        loading = true
        failed = false
        try {
            val loaded = ApiClient.api().listProfiles()
            profiles = loaded
            selected = firstProfileIndex(loaded).coerceAtLeast(0)
        } catch (e: HttpException) {
            // Revoked/expired token: drop it and re-pair.
            if (e.code() == 401) onUnauthorized() else failed = true
        } catch (_: Exception) {
            // Server unreachable; let the user retry.
            failed = true
        } finally {
            loading = false
        }
    }

    Column(modifier = modifier.fillMaxSize().padding(8.dp)) {
        when {
            loading -> LoadingState()
            failed -> ErrorState(
                onRetry = { reloads++ },
                onChangeServer = { showServerDialog = true },
            )
            profiles.isEmpty() -> MessageState(stringResource(R.string.deck_empty))
            else -> {
                val profile = profiles[selected.coerceIn(0, profiles.lastIndex)]
                DeckHeader(
                    name = profile.name,
                    withArrows = profiles.size > 1,
                    onPrevious = { selected = cycleProfileIndex(selected, profiles.size, -1) },
                    onNext = { selected = cycleProfileIndex(selected, profiles.size, 1) },
                    themeMode = themeMode,
                    onThemeModeChange = onThemeModeChange,
                    onEditServer = { showServerDialog = true },
                )
                LazyVerticalGrid(
                    columns = GridCells.Fixed(GRID_COLUMNS),
                    modifier = Modifier.weight(1f),
                    contentPadding = PaddingValues(4.dp),
                ) {
                    items(profile.buttons, key = { it.index }) { button ->
                        val label = buttonLabel(button)
                        DeckButtonCard(label = label, icon = icons.icon(button.action)) {
                            lastLabel = label
                            status = null
                            scope.launch {
                                status = try {
                                    statusOf(
                                        ApiClient.api().dispatch(
                                            ActionRequest(button.action, button.label),
                                        ),
                                    )
                                } catch (e: HttpException) {
                                    if (e.code() == 401) onUnauthorized()
                                    DeckStatus.FAILED
                                } catch (_: Exception) {
                                    DeckStatus.FAILED
                                }
                            }
                        }
                    }
                }
            }
        }
        StatusLine(status = status, label = lastLabel)
    }

    if (showServerDialog) {
        ServerUrlDialog(
            initialUrl = TokenStore.baseUrl,
            onDismiss = { showServerDialog = false },
            onConfirm = { url ->
                // Rebuilds the Retrofit client (ApiClient watches TokenStore) and
                // reloads. A different server will usually 401 -> re-pair.
                TokenStore.baseUrl = url
                showServerDialog = false
                reloads++
            },
        )
    }
}

@Composable
private fun buttonLabel(button: DeckButton): String =
    button.label.ifBlank { stringResource(R.string.button_default_label, button.index + 1) }

@Composable
private fun StatusLine(status: DeckStatus?, label: String?) {
    val text = when (status) {
        null -> stringResource(R.string.status_ready)
        DeckStatus.SENT -> stringResource(R.string.deck_status_sent, label ?: "")
        DeckStatus.UNKNOWN -> stringResource(R.string.deck_status_unknown, label ?: "")
        DeckStatus.FAILED -> stringResource(R.string.deck_status_failed, label ?: "")
    }
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        modifier = Modifier.padding(top = 8.dp),
    )
}

/** Profile name (with arrows when there are several) plus the theme/server menus. */
@Composable
private fun DeckHeader(
    name: String,
    withArrows: Boolean,
    onPrevious: () -> Unit,
    onNext: () -> Unit,
    themeMode: ThemeMode,
    onThemeModeChange: (ThemeMode) -> Unit,
    onEditServer: () -> Unit,
) {
    Box(modifier = Modifier.fillMaxWidth().padding(horizontal = 4.dp)) {
        Row(
            modifier = Modifier.align(Alignment.Center),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (withArrows) {
                IconButton(onClick = onPrevious) { Text("\u25C0") }
            }
            Text(text = name, style = MaterialTheme.typography.titleMedium)
            if (withArrows) {
                IconButton(onClick = onNext) { Text("\u25B6") }
            }
        }
        Row(
            modifier = Modifier.align(Alignment.CenterEnd),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            ServerMenuButton(onClick = onEditServer)
            ThemeMenu(
                mode = themeMode,
                onModeChange = onThemeModeChange,
                modifier = Modifier,
            )
        }
    }
}

/** Opens the server-address dialog so the URL can change after pairing. */
@Composable
private fun ServerMenuButton(onClick: () -> Unit) {
    val description = stringResource(R.string.deck_server_button)
    IconButton(
        onClick = onClick,
        modifier = Modifier.semantics { contentDescription = description },
    ) {
        Text(text = "\u2699", style = MaterialTheme.typography.titleMedium)
    }
}

/** Light/dark switch: lets the deck follow the system or force a scheme. */
@Composable
private fun ThemeMenu(
    mode: ThemeMode,
    onModeChange: (ThemeMode) -> Unit,
    modifier: Modifier = Modifier,
) {
    var open by remember { mutableStateOf(false) }
    val description = stringResource(R.string.theme_button)

    Box(modifier = modifier) {
        IconButton(
            onClick = { open = true },
            modifier = Modifier.semantics { contentDescription = description },
        ) {
            Text(text = "\u25D0", style = MaterialTheme.typography.titleMedium)
        }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            ThemeMode.entries.forEach { option ->
                DropdownMenuItem(
                    text = { Text(stringResource(option.label())) },
                    leadingIcon = {
                        Text(if (option == mode) "\u2713" else " ", textAlign = TextAlign.Center)
                    },
                    onClick = {
                        onModeChange(option)
                        open = false
                    },
                )
            }
        }
    }
}

private fun ThemeMode.label(): Int = when (this) {
    ThemeMode.SYSTEM -> R.string.theme_system
    ThemeMode.LIGHT -> R.string.theme_light
    ThemeMode.DARK -> R.string.theme_dark
}

@Composable
private fun LoadingState() {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CircularProgressIndicator()
        Text(
            text = stringResource(R.string.deck_loading),
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 12.dp),
        )
    }
}

@Composable
private fun ErrorState(onRetry: () -> Unit, onChangeServer: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = stringResource(R.string.deck_error),
            textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.error,
        )
        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = onRetry) { Text(stringResource(R.string.deck_retry)) }
            OutlinedButton(onClick = onChangeServer) {
                Text(stringResource(R.string.deck_change_server))
            }
        }
    }
}

@Composable
private fun MessageState(message: String) {
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(text = message, textAlign = TextAlign.Center)
    }
}

/** A deck button: a 3D "glass" key (like a real Stream Deck) with the program's icon. */
@Composable
private fun DeckButtonCard(label: String, icon: ImageBitmap?, onClick: () -> Unit) {
    val glass = glassPalette()
    val shape = RoundedCornerShape(BUTTON_CORNER_RADIUS.dp)
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (pressed) 0.94f else 1f,
        animationSpec = tween(durationMillis = 90),
        label = "buttonPress",
    )
    val haptics = LocalHapticFeedback.current

    Box(
        modifier = Modifier
            .padding(5.dp)
            .aspectRatio(1f)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
            }
            .shadow(
                elevation = if (pressed) 3.dp else 9.dp,
                shape = shape,
                clip = false,
                ambientColor = glass.shadow,
                spotColor = glass.shadow,
            )
            .clip(shape)
            .background(Brush.verticalGradient(listOf(glass.top, glass.bottom)))
            .border(1.dp, Brush.verticalGradient(listOf(glass.borderTop, glass.borderBottom)), shape)
            .clickable(
                interactionSource = interaction,
                indication = null,
                onClickLabel = label,
            ) {
                haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                onClick()
            },
        contentAlignment = Alignment.Center,
    ) {
        // Glass sheen: a highlight across the top and a shade along the bottom edge.
        Box(
            modifier = Modifier
                .matchParentSize()
                .background(
                    Brush.verticalGradient(
                        0f to glass.sheen,
                        0.5f to Color.Transparent,
                        0.82f to Color.Transparent,
                        1f to glass.bottomShade,
                    ),
                ),
        )
        Column(
            modifier = Modifier.fillMaxSize().padding(6.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            if (icon != null) {
                Image(
                    bitmap = icon,
                    contentDescription = null,
                    modifier = Modifier.size(BUTTON_ICON_SIZE.dp),
                    filterQuality = FilterQuality.High,
                )
            } else {
                MonogramBadge(label = label, backing = glass.iconBacking)
            }
            Spacer(Modifier.height(6.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurface,
                textAlign = TextAlign.Center,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

/** Fallback for actions without an icon: the label's initial in a glass circle. */
@Composable
private fun MonogramBadge(label: String, backing: Color) {
    val monogram = label.trim().take(1).uppercase().ifEmpty { "?" }
    Box(
        modifier = Modifier
            .size(BUTTON_ICON_SIZE.dp)
            .clip(CircleShape)
            .background(backing)
            .border(1.dp, Color.White.copy(alpha = 0.10f), CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = monogram,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onSurface,
        )
    }
}

/** Glass tokens for the deck keys, picked from the scheme currently in use. */
private data class GlassPalette(
    val top: Color,
    val bottom: Color,
    val borderTop: Color,
    val borderBottom: Color,
    val sheen: Color,
    val bottomShade: Color,
    val shadow: Color,
    val iconBacking: Color,
)

private val DarkGlass = GlassPalette(
    top = Color(0xFF4B4754),
    bottom = Color(0xFF232027),
    borderTop = Color(0x40FFFFFF),
    borderBottom = Color(0x0DFFFFFF),
    sheen = Color(0x24FFFFFF),
    bottomShade = Color(0x40000000),
    shadow = Color(0xFF000000),
    iconBacking = Color(0x1FFFFFFF),
)

private val LightGlass = GlassPalette(
    top = Color(0xFFFFFFFF),
    bottom = Color(0xFFE6E2EC),
    borderTop = Color(0xFFFFFFFF),
    borderBottom = Color(0x14000000),
    sheen = Color(0x59FFFFFF),
    bottomShade = Color(0x14000000),
    shadow = Color(0x59000000),
    iconBacking = Color(0x14000000),
)

@Composable
private fun glassPalette(): GlassPalette =
    if (MaterialTheme.colorScheme.background.luminance() < 0.5f) DarkGlass else LightGlass

@Preview(showBackground = true)
@Composable
private fun DeckScreenPreview() {
    MyDroidDeckTheme { DeckScreen() }
}
