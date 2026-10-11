package com.mydroiddeck.app.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
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
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.mydroiddeck.app.R
import com.mydroiddeck.app.model.ActionRequest
import com.mydroiddeck.app.model.DeckButton
import com.mydroiddeck.app.model.DeckProfile
import com.mydroiddeck.app.net.ApiClient
import com.mydroiddeck.app.ui.theme.MyDroidDeckTheme
import kotlinx.coroutines.launch
import retrofit2.HttpException

private const val GRID_COLUMNS = 4
private const val BUTTON_ICON_SIZE = 40

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
            failed -> ErrorState(onRetry = { reloads++ })
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

/** Profile name (with arrows when there are several) plus the theme menu. */
@Composable
private fun DeckHeader(
    name: String,
    withArrows: Boolean,
    onPrevious: () -> Unit,
    onNext: () -> Unit,
    themeMode: ThemeMode,
    onThemeModeChange: (ThemeMode) -> Unit,
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
        ThemeMenu(
            mode = themeMode,
            onModeChange = onThemeModeChange,
            modifier = Modifier.align(Alignment.CenterEnd),
        )
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
private fun ErrorState(onRetry: () -> Unit) {
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
        Button(onClick = onRetry) { Text(stringResource(R.string.deck_retry)) }
    }
}

@Composable
private fun MessageState(message: String) {
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(text = message, textAlign = TextAlign.Center)
    }
}

/** A deck button: the program's real icon (when available) above its label. */
@Composable
private fun DeckButtonCard(label: String, icon: ImageBitmap?, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .padding(4.dp)
            .aspectRatio(1f)
            .clickable(onClick = onClick),
    ) {
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
                )
                Spacer(Modifier.height(4.dp))
            }
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium,
                textAlign = TextAlign.Center,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun DeckScreenPreview() {
    MyDroidDeckTheme { DeckScreen() }
}
