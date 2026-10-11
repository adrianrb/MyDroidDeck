package com.mydroiddeck.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.mydroiddeck.app.R
import com.mydroiddeck.app.model.DeckButton
import com.mydroiddeck.app.ui.theme.MyDroidDeckTheme

private const val GRID_COLUMNS = 4
private const val PLACEHOLDER_BUTTONS = 8

private fun placeholderButtons(): List<DeckButton> =
    List(PLACEHOLDER_BUTTONS) { index ->
        DeckButton(index = index, label = "", action = "action.$index")
    }

@Composable
fun DeckScreen(modifier: Modifier = Modifier) {
    val buttons = remember { placeholderButtons() }
    var lastAction by remember { mutableStateOf<String?>(null) }

    Column(modifier = modifier.fillMaxSize().padding(8.dp)) {
        LazyVerticalGrid(
            columns = GridCells.Fixed(GRID_COLUMNS),
            modifier = Modifier.weight(1f),
            contentPadding = PaddingValues(4.dp),
        ) {
            items(buttons, key = { it.index }) { button ->
                val label = button.label.ifBlank {
                    stringResource(R.string.button_default_label, button.index + 1)
                }
                DeckButtonCard(label = label, onClick = { lastAction = label })
            }
        }
        Text(
            text = lastAction?.let { stringResource(R.string.status_last_action, it) }
                ?: stringResource(R.string.status_ready),
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 8.dp),
        )
    }
}

@Composable
private fun DeckButtonCard(label: String, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .padding(4.dp)
            .aspectRatio(1f)
            .clickable(onClick = onClick),
    ) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text(
                text = label,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(8.dp),
            )
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun DeckScreenPreview() {
    MyDroidDeckTheme { DeckScreen() }
}
