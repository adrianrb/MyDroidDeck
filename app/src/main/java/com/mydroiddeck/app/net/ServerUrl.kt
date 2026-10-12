package com.mydroiddeck.app.net

/**
 * Normalises a server base URL typed by the user (pairing screen or the in-app
 * server dialog).
 *
 * - trims surrounding blanks;
 * - assumes `http://` when no scheme is given (the LAN / no-login server speaks
 *   plain HTTP; users usually just type `host:port`);
 * - guarantees a trailing slash so Retrofit resolves paths against it.
 *
 * Returns an empty string when there is nothing usable.
 */
fun normalizeBaseUrl(raw: String): String {
    val trimmed = raw.trim()
    if (trimmed.isEmpty()) return ""
    val withScheme = if (trimmed.contains("://")) trimmed else "http://$trimmed"
    return if (withScheme.endsWith("/")) withScheme else "$withScheme/"
}

/**
 * True when [raw] looks like a usable `http(s)://host[:port][/path]` base URL.
 * Deliberately permissive: it only rejects blanks and obvious typos (spaces,
 * missing host), leaving reachability to the actual request.
 */
fun isValidBaseUrl(raw: String): Boolean {
    val normalized = normalizeBaseUrl(raw)
    return normalized.isNotEmpty() && BASE_URL_PATTERN.matches(normalized)
}

/** `scheme://host` (host without spaces or slashes) plus an optional path. */
private val BASE_URL_PATTERN = Regex("^https?://[^\\s/]+(/.*)?$")
