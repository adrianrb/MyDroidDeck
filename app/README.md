# MyDroidDeck app

Native Android client in **Kotlin + Jetpack Compose (Material 3)**. Renders a grid
of deck buttons and (in progress) syncs profiles and dispatches actions to the
server over **REST**.

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

## Layout

- `src/main/java/com/mydroiddeck/app/` — `MainActivity`, `model/`, `net/`, `ui/`
  (Compose screens live in `ui/`, theme in `ui/theme/`)
- `src/main/res/` — `values/` is **pt-BR (default)**, `values-en/` English
- Base server URL is in `net/ApiClient.kt` (`10.0.2.2:8000` for the emulator)
