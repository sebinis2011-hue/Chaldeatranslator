# Android build notes

The Android module is built with JDK 17 and Gradle 8.9.

From Android Studio, open the repository root and sync the Gradle project. The CI build installs Android platform 35 and build-tools 35.0.0, then runs:

```bash
gradle :app:testDebugUnitTest
gradle :app:assembleDebug
```

The debug APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

The CI workflow installs only `platform-tools` through setup-android. It deliberately does not request the retired SDK package named `tools`.

This is a development skeleton. The native llama.cpp backend and model manager are not connected yet, so a successful debug build does not mean that AI translation is operational.
