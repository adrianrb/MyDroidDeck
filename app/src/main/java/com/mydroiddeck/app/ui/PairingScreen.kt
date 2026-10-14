package com.mydroiddeck.app.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
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
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import com.mydroiddeck.app.R
import com.mydroiddeck.app.model.PairRequest
import com.mydroiddeck.app.net.ApiClient
import com.mydroiddeck.app.net.TokenStore
import com.mydroiddeck.app.net.isValidBaseUrl
import com.mydroiddeck.app.net.normalizeBaseUrl
import com.mydroiddeck.app.net.parsePairingQr
import kotlinx.coroutines.launch

/**
 * First-run pairing: scans the QR code from the server's *Dispositivos → Parear
 * novo* page (the camera opens by itself), or takes the URL/code by hand.
 */
@Composable
fun PairingScreen(
    onPaired: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var code by remember { mutableStateOf("") }
    var deviceName by remember { mutableStateOf("") }
    var serverUrl by remember { mutableStateOf(TokenStore.baseUrl) }
    var error by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val errorMessage = stringResource(R.string.pairing_error)
    val badQrMessage = stringResource(R.string.pairing_qr_invalid)
    val scanPrompt = stringResource(R.string.pairing_scan_prompt)

    val scanner = rememberLauncherForActivityResult(ScanContract()) { result ->
        val scanned = result.contents
        if (scanned != null) {
            val pairing = parsePairingQr(scanned)
            if (pairing == null) {
                error = badQrMessage
            } else {
                serverUrl = pairing.serverUrl
                code = pairing.code
                error = null
            }
        }
    }
    val scanOptions = remember(scanPrompt) {
        ScanOptions()
            .setDesiredBarcodeFormats(ScanOptions.QR_CODE)
            .setPrompt(scanPrompt)
            .setBeepEnabled(false)
            .setOrientationLocked(false)
    }

    // First run: open the camera straight away, as the QR fills both fields.
    LaunchedEffect(Unit) {
        scanner.launch(scanOptions)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = stringResource(R.string.pairing_title),
            style = MaterialTheme.typography.headlineSmall,
        )
        Text(
            text = stringResource(R.string.pairing_hint),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(vertical = 8.dp),
        )
        OutlinedButton(
            onClick = { scanner.launch(scanOptions) },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(stringResource(R.string.pairing_scan_qr))
        }
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = serverUrl,
            onValueChange = { serverUrl = it },
            label = { Text(stringResource(R.string.pairing_server_url)) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = code,
            onValueChange = { code = it },
            label = { Text(stringResource(R.string.pairing_code)) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = deviceName,
            onValueChange = { deviceName = it },
            label = { Text(stringResource(R.string.pairing_device_name)) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        error?.let {
            Text(
                text = it,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(vertical = 8.dp),
            )
        }
        Button(
            onClick = {
                busy = true
                error = null
                // Persist the URL first so the temporary Retrofit instance hits the
                // server the user just typed.
                val normalized = normalizeBaseUrl(serverUrl)
                TokenStore.baseUrl = normalized
                scope.launch {
                    try {
                        val result = ApiClient.api().pair(
                            PairRequest(code = code.trim(), deviceName = deviceName.trim())
                        )
                        TokenStore.token = result.token
                        onPaired()
                    } catch (_: Exception) {
                        error = errorMessage
                    } finally {
                        busy = false
                    }
                }
            },
            enabled = !busy && code.isNotBlank() && deviceName.isNotBlank() &&
                isValidBaseUrl(serverUrl),
            modifier = Modifier.fillMaxWidth(),
        ) {
            if (busy) {
                CircularProgressIndicator(
                    modifier = Modifier.size(18.dp),
                    strokeWidth = 2.dp,
                    color = MaterialTheme.colorScheme.onPrimary,
                )
            } else {
                Text(stringResource(R.string.pairing_action))
            }
        }
    }
}
