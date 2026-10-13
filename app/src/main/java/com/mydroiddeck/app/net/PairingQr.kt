package com.mydroiddeck.app.net

import java.net.URLDecoder

/** Server URL + pairing code read from the QR the admin "Parear novo" page shows. */
data class PairingQr(val serverUrl: String, val code: String)

/** URI scheme/target the server encodes: `mydroiddeck://pair?url=…&code=…`. */
private const val PAIRING_SCHEME = "mydroiddeck"
private const val PAIRING_TARGET = "pair"

/**
 * Parses the pairing payload the server's *Dispositivos → Parear novo* page
 * encodes. Returns `null` for anything else, so scanning an unrelated QR code
 * leaves the form untouched instead of filling it with junk. The URL is
 * normalized/validated with the same rules as the typed-in field.
 *
 * Values are percent-decoded with `URLDecoder`, which also turns `+` into a
 * space; the server escapes `+` as `%2B`, so real values survive the trip.
 */
fun parsePairingQr(text: String): PairingQr? {
    val trimmed = text.trim()
    val schemeEnd = trimmed.indexOf("://")
    if (schemeEnd <= 0) return null
    if (!trimmed.substring(0, schemeEnd).equals(PAIRING_SCHEME, ignoreCase = true)) return null

    val rest = trimmed.substring(schemeEnd + 3)
    val queryStart = rest.indexOf('?')
    if (queryStart < 0) return null
    if (!rest.substring(0, queryStart).trimEnd('/').equals(PAIRING_TARGET, ignoreCase = true)) {
        return null
    }

    val parameters = parseQuery(rest.substring(queryStart + 1))
    val serverUrl = parameters["url"]?.let(::normalizeBaseUrl) ?: return null
    if (!isValidBaseUrl(serverUrl)) return null
    val code = parameters["code"]?.trim()
    if (code.isNullOrEmpty()) return null
    return PairingQr(serverUrl, code)
}

/** `a=1&b=2` → map with percent-decoded values; unusable pairs are skipped. */
private fun parseQuery(query: String): Map<String, String> =
    query.split('&')
        .mapNotNull { pair ->
            val separator = pair.indexOf('=')
            if (separator <= 0) return@mapNotNull null
            pair.substring(0, separator).decode() to pair.substring(separator + 1).decode()
        }
        .toMap()

/** Percent-decoder that keeps malformed sequences verbatim instead of throwing. */
private fun String.decode(): String =
    try {
        URLDecoder.decode(this, "UTF-8")
    } catch (_: IllegalArgumentException) {
        this
    }
