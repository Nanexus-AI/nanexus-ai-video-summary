# Android development

This is the public source of truth for building and connecting the Nanexus AI Video Summary Android client. It consolidates the reusable guidance from the retired machine-specific setup note.

## Requirements

- JDK 17
- Android SDK Platform 35 and compatible Build Tools
- Android SDK Platform-Tools (`adb`)
- Android Emulator or a device with USB debugging enabled
- Android Studio is optional; the committed Gradle wrapper is the command-line entry point

The app is version `0.1.0`. The project declares Gradle 8.9, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, compile/target SDK 35, minimum SDK 26, and JVM target 17.

Install SDK components in any suitable local directory. Configure the environment without committing machine-specific paths:

```bash
export JAVA_HOME=<JDK_17_HOME>
export ANDROID_SDK_ROOT=<ANDROID_SDK_ROOT>
export ANDROID_HOME="$ANDROID_SDK_ROOT"
export PATH="$ANDROID_SDK_ROOT/platform-tools:$PATH"
```

Useful checks include `java -version`, `adb version`, `sdkmanager --list_installed`, and `emulator -list-avds`.

## Project structure

- `android/settings.gradle.kts` defines the `:app` module and dependency repositories.
- `android/build.gradle.kts` pins the Android and Kotlin plugins.
- `android/app/build.gradle.kts` defines SDK levels, build types, dependencies, and the app version.
- `android/app/src/main/` contains shared Kotlin, Compose UI, resources, and the base manifest.
- `android/app/src/debug/` permits cleartext traffic for trusted-network development.
- `android/app/src/release/` rejects cleartext traffic.
- `android/gradle/wrapper/` and `gradlew` provide the pinned Gradle entry point.

The app uses Jetpack Compose and consumes the Video Summary application API. It must not connect directly to PostgreSQL, Redis, MQTT, the model service, a camera/NVR, or Event Intelligence processor interfaces.

## Local configuration

Set the local Android SDK path in `android/local.properties` when required by Gradle or Android Studio:

```properties
sdk.dir=<ANDROID_SDK_ROOT>
```

`local.properties` is machine-local configuration. Do not commit it or place credentials, signing details, or private infrastructure information in it. Environment variables or Android Studio's SDK selection are alternatives.

The app's Settings screen stores the API base URL and optional camera filter in Android DataStore. **Save & test** checks the configured server's `/health` endpoint. That payload still includes legacy `ai_mode` for compatibility; current v1 provider selection is `model_provider` and must not be inferred from `ai_mode`. Authentication tokens, when used, are obtained through the Android keystore-backed token provider; do not hard-code tokens in Kotlin, Gradle, resources, or manifests.

## Build and test

From the repository root:

```bash
cd android
./gradlew testDebugUnitTest
./gradlew assembleDebug
```

For a local release build check:

```bash
./gradlew assembleRelease
```

Release packaging and signing policy are not supplied as public release automation. A distributable release must use an operator-controlled signing configuration. Keep keystores, key aliases, passwords, and signing property files outside version control; never add signing secrets to Gradle files or command history.

Typical local outputs are below `android/app/build/outputs/`, including `apk/debug/app-debug.apk` after `assembleDebug`. Gradle state and build directories are generated local data, and `*.apk` and `*.aab` are ignored by the repository. Do not commit or attach generated packages as source changes.

## API connectivity

### Debug emulator

Debug builds default to:

```text
http://10.0.2.2:8000
```

`10.0.2.2` is the Android Emulator alias for the development host. Start the Video Summary API on host port `8000`; the emulator can then reach it through this alias. Debug manifests allow cleartext HTTP for local or trusted-network development only.

### Physical device

A physical device cannot use the emulator alias. Configure an API URL that the device can reach over the same trusted network, for example a local DNS name and port. The API must listen on an appropriate host interface rather than only `127.0.0.1`, and host firewall rules must allow the intended device. Do not expose internal dependencies or open the API broadly merely to make device testing work.

### Release behavior

Release builds default to the non-routable placeholder `https://nanexus.invalid`. Configure a real deployer-controlled HTTPS Video Summary API URL in the app before use. Release manifests disable cleartext traffic, and the API client rejects a base URL that does not begin with `https://`.

The base URL is normalized with one trailing slash. The client calls Video Summary health and application endpoints beneath that origin, including v1 capabilities, Summary, Search, Chat, and subject-link flows plus retained compatibility endpoints. Clients should follow server-provided links and capability negotiation rather than constructing private Event Intelligence URLs.

## Trust and security boundary

Debug HTTP is acceptable only on a local machine, emulator path, or controlled trusted development network. External access is the deployer's responsibility and requires suitable HTTPS termination, authentication, authorization, firewalling, and access controls. This project does not provide a complete public-network security gateway.

Never place database, Redis, MQTT, processor, model-service, camera, or Event Intelligence service credentials in the app. Mobile clients receive only Video Summary client credentials and public application URLs appropriate to their role. See [Security](../SECURITY.md) and [Deployment](deployment.md).

## Troubleshooting

- **Gradle reports an unsupported Java version:** ensure `JAVA_HOME` and the IDE Gradle JDK both select JDK 17.
- **SDK 35 is missing:** install Android SDK Platform 35 and compatible Build Tools, then confirm `ANDROID_SDK_ROOT` or `local.properties` points to that SDK.
- **`adb` cannot find a device:** run `adb devices`, authorize USB debugging, or start an emulator. On Linux, confirm USB permissions or KVM acceleration as applicable.
- **Emulator cannot reach the API:** use `http://10.0.2.2:8000`, confirm the host API is running on port `8000`, and test the host's `/health` endpoint.
- **Physical device cannot reach the API:** use a trusted-network-reachable host name or address, bind the API to the intended interface, and inspect host/device firewall and network isolation. Do not use `10.0.2.2`.
- **Release rejects the URL:** use a valid HTTPS base URL. Cleartext HTTP is intentionally unavailable in Release.
- **Settings test fails:** remove path suffixes from the base URL, verify server reachability and credentials, and check that `/health` is available at that origin.
- **Dependency download fails:** Gradle requires access to Google, Maven Central, the Gradle Plugin Portal, and the wrapper distribution on a first clean build unless artifacts are already cached.

## Known limitations and release boundary

- The initial release is source-first; no project-published APK or AAB is currently provided.
- Public release signing and automated store publication are not configured here.
- Release deployments require an operator-provided HTTPS endpoint and external access controls.
- The Timeline and some server routes remain compatibility surfaces while Summary, Search, and asynchronous Chat use the v1 application API.
- Android integration depends on a compatible running Video Summary API and, for full integrated behavior, its separately operated Event Intelligence dependency.
