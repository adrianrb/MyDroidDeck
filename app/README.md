# MyDroidDeck app

Native Android client in **Kotlin + Jetpack Compose (Material 3)**. Loads the deck
profiles from the server over **REST** (`Authorization: Bearer`), renders them as a
grid of buttons (each with the target program's real icon) and dispatches the
tapped button's action.

## Build

Requires the Android SDK (`C:\desenv\Android\Sdk`) and JDK 17+.

```bash
./gradlew assembleDebug      # debug APK -> build/outputs/apk/debug/
./gradlew test               # JVM unit tests
```

Gradle 8.7, Android Gradle Plugin 8.5.2, Kotlin 1.9.24, Compose compiler 1.5.14.
Set `sdk.dir` in `local.properties` (or `ANDROID_HOME`) before building.

## Pairing

First launch shows a pairing screen. Enter the code shown at
`/admin/devices` (default dev code: **`pair-dev`**) and a device name; the server
returns a per-device token, stored locally and sent as `Authorization: Bearer` on
every REST call. A revoked token (401) drops the pairing and returns to the screen.

The screen also lets you change the **server URL** (persisted) — for a physical
device use the Windows host's LAN IP, e.g. `https://192.168.100.7:8000/` (the
emulator keeps `https://10.0.2.2:8000/`). See `server/README.md` for the LAN
port-forward setup on WSL2.

## Deck

- On start the deck calls `GET /profiles` and renders the selected profile as a
  4-column grid; with more than one profile, arrows switch between them
  (`ui/DeckScreen.kt`).
- Every button shows the **real icon of the program** behind it: the app fetches
  `GET /icon?action=<key>` once per action (`ui/DeckIcons.kt`) and falls back to
  the text label when the action has no icon (404).
- Tapping a button `POST`s its action and the footer reports the outcome
  ("Enviado", "Ação não configurada no servidor", "Falha ao enviar").
- Loading, "server unreachable" (with a **Tentar de novo** button) and "no
  profiles" states are handled explicitly; a 401 (revoked token) drops the pairing.
- **Tema**: the ◐ menu in the deck header switches between *seguir o sistema*,
  *claro* and *escuro*; the choice is persisted (`ui/ThemeMode.kt`).

## Layout

- `src/main/java/com/mydroiddeck/app/` — `MainActivity`, `model/`, `net/`, `ui/`
  (Compose screens live in `ui/`, theme in `ui/theme/`)
- `src/main/res/` — `values/` is **pt-BR (default)**, `values-en/` English
- Base server URL is in `net/ApiClient.kt` (`10.0.2.2:8000` for the emulator)
