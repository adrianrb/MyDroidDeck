package com.mydroiddeck.app.net

/** Central place for network constants. */
object NetConfig {

    /**
     * The emulator maps the host machine to 10.0.2.2; a physical device needs
     * the server's LAN address instead (users change it on the pairing screen or
     * from the deck's Server dialog; it is persisted in [TokenStore.baseUrl]).
     *
     * Plain HTTP on the no-login installer's default port (56997): that build
     * serves no TLS and binds the LAN only when "Visivel na rede" is enabled.
     */
    const val DEFAULT_BASE_URL = "http://10.0.2.2:56997/"
}
