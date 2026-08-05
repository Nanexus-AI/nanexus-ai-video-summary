# Android 开发机环境（192.168.1.84）

本机即 `andy-NucBox-K11` / `192.168.1.84`。因无 sudo 密码，组件安装在**用户目录**（未走 `apt`）。

## 已安装

| 组件 | 路径 |
|------|------|
| JDK 17 (Temurin) | `~/tools/jdk-17` |
| Android SDK | `~/Android/Sdk` |
| platform-tools / adb | `~/Android/Sdk/platform-tools` |
| Android Studio | `~/android-studio` |
| KVM | 系统已具备（`/dev/kvm` 可用，用户在 `kvm` 组） |

## 启动 Android Studio

图形桌面登录后任选：

```bash
android-studio
# 或
~/android-studio/bin/studio.sh
```

或在应用菜单打开 **Android Studio**。

首次打开若询问 SDK 位置，填：`/home/andy/Android/Sdk`。

## 环境变量

已写入 `~/.bashrc`。新开终端后可用：

```bash
java -version
adb version
sdkmanager --list_installed
emulator -list-avds
```

## Compose App（`android/`）

```bash
export JAVA_HOME=~/tools/jdk-17
export ANDROID_HOME=~/Android/Sdk
cd ~/Nanexus/nanexus_ai_video_summary/android
./gradlew assembleDebug
# app/build/outputs/apk/debug/app-debug.apk
```

Android Studio：打开仓库里的 `android/` 目录，选模拟器或真机 Run。

## 连 Nanexus API

| 客户端 | Base URL 示例 |
|--------|----------------|
| 模拟器 → 本机 API | `http://10.0.2.2:8000`（App 默认） |
| 真机 → 本机 API（84） | `http://192.168.1.84:8000` |
| 任意 → 其他主机 | 该主机局域网 IP + `:8000` |

API 需监听 `0.0.0.0`。App Settings 可改 Base URL 与 camera filter，并点 Save & test 打 `/health`。

开发期 HTTP 已在 Manifest / `network_security_config` 允许 cleartext。

## 可选：系统级 JDK（需 sudo）

若希望 `apt` 安装：

```bash
sudo apt update
sudo apt install -y openjdk-17-jdk
```

当前用户空间 JDK 已足够开发。
