package com.mydroiddeck.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.mydroiddeck.app.R
import com.mydroiddeck.app.net.isValidBaseUrl
import com.mydroiddeck.app.net.normalizeBaseUrl

/**
 * Lets the user edit the server address after pairing (the pairing screen only
 * shows when there is no token). Confirms with the normalized URL.
 */
@Composable
fun ServerUrlDialog(
    initialUrl: String,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
) {
    var url by remember { mutableStateOf(initialUrl) }
    val valid = isValidBaseUrl(url)

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.server_dialog_title)) },
        text = {
            Column {
                Text(
                    text = stringResource(R.string.server_dialog_hint),
                    style = MaterialTheme.typography.bodySmall,
                )
                OutlinedTextField(
                    value = url,
                    onValueChange = { url = it },
                    label = { Text(stringResource(R.string.pairing_server_url)) },
                    singleLine = true,
                    isError = url.isNotBlank() && !valid,
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(normalizeBaseUrl(url)) },
                enabled = valid,
            ) {
                Text(stringResource(R.string.server_dialog_save))
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.server_dialog_cancel))
            }
        },
    )
}
