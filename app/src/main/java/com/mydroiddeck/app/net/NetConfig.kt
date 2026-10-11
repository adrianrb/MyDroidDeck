package com.mydroiddeck.app.net

/** Central place for network constants. */
object NetConfig {

    /**
     * The Android emulator maps the host machine to 10.0.2.2; a physical device
     * needs the server's LAN/reachable address instead (users change it on the
     * pairing screen; it is persisted in [TokenStore.baseUrl]).
     *
     * HTTPS by default: the server serves TLS with a self-signed dev certificate
     * (see server/deploy/gen-cert.sh) that this app trusts via
     * res/xml/network_security_config.xml.
     */
    const val DEFAULT_BASE_URL = "https://10.0.2.2:8000/"
}
