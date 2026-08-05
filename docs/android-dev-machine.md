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

## 连 Nanexus API

App / 模拟器里 Base URL 使用后端真实 IP，例如：

```text
http://192.168.1.80:8000
```

（若 API 跑在本机 84，用本机局域网 IP 或 `http://10.0.2.2:8000` 仅适用于模拟器访问**本机**服务。）

开发期 HTTP 需在 AndroidManifest / network security config 允许 cleartext。

## 可选：系统级 JDK（需 sudo）

若希望 `apt` 安装：

```bash
sudo apt update
sudo apt install -y openjdk-17-jdk
```

当前用户空间 JDK 已足够开发。
