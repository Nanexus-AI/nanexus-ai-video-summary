# Nanexus AI Video Summary

Frigate 之上的 AI 视频摘要 / 时间线 / 语义检索 / 问答（当前 **M2**）。

- 架构设计：[`docs/architecture.md`](docs/architecture.md)
- M0 总结：[`docs/m0-implementation.md`](docs/m0-implementation.md)
- M1 总结：[`docs/m1-implementation.md`](docs/m1-implementation.md)
- M2 总结：[`docs/m2-implementation.md`](docs/m2-implementation.md)
- Android 开发机环境：[`docs/android-dev-machine.md`](docs/android-dev-machine.md)
- Android Compose App：[`android/`](android/)（见下方「Android App」）

## 当前能力

- Docker：PostgreSQL（pgvector）+ Redis + Mosquitto
- `mqtt_listener`：`frigate/events` → 落库 → Redis 队列
- `ai_worker`：snapshot → OpenCLIP caption/embedding
- `summary_worker`：日终/队列预计算摘要（rule 或 LLM）
- API：
  - `GET /timeline` / `GET /summary/today`
  - `POST /search` / `POST /chat`
  - `GET /events/{id}/snapshot`
  - `GET /api/v1/summaries/{local_date}`（只读基座化预计算摘要）
  - `POST /api/v1/summaries/rebuild` / `GET /api/v1/summaries/jobs/{id}`
- 真实 Frigate：改 `.env` 后用 `scripts/import_frigate_events.py` 回填

## 快速开始

### 1. 基础设施

```bash
cp .env.example .env
docker compose up -d
```

### 2. Python 环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e .
```

### 3. 启动四个服务

```bash
source .venv/bin/activate
uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000
python -m services.mqtt_listener.main
python -m services.ai_worker.main
python -m services.summary_worker.main
```

### 4. 演示与验收

```bash
python scripts/import_frigate_events.py -n 8 --force   # 或 seed_events.py
python -m services.summary_worker.main --once

curl -s localhost:8000/summary/today | python -m json.tool
curl -s localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"今天 front_yard 有什么？","camera":"front_yard"}' \
  | python -m json.tool
```

API 文档：http://localhost:8000/docs

## 真实 Frigate

```bash
FRIGATE_BASE_URL=http://192.168.1.80:5000
MQTT_HOST=192.168.1.80
MQTT_PORT=1883
MQTT_TOPIC=frigate/events
```

```bash
python scripts/import_frigate_events.py -n 10 --force
```

## 可选 LLM

```bash
SUMMARY_MODE=llm
CHAT_MODE=llm
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

未配置 Key 时默认 `rule` / `extractive`，仍可完整演示。

## Event Intelligence OpenCLIP Worker（迁移阶段 4）

跨仓 enrichment Worker 默认使用安全 Stub。启用本地 OpenCLIP 时使用独立 model overlay；API 服务不会加载模型：

```bash
PROCESSOR_API_TOKEN=replace-me docker-compose \
  -f compose.slice.yaml -f compose.model.yaml up --build
```

关键配置为 `MODEL_PROVIDER=stub|openclip`、`AI_DEVICE=auto|cpu|cuda`、`OPENCLIP_MODEL` 和 `OPENCLIP_PRETRAINED`。Worker 只通过 Event Intelligence 的 job-scoped Evidence API 读取媒体，不接受 Frigate URL、Token 或本地文件路径。

## Android App

Jetpack Compose 客户端在 `android/`，对接同一套 API（Today / Timeline / Search / Settings）。

```bash
export JAVA_HOME=~/tools/jdk-17
export ANDROID_HOME=~/Android/Sdk
cd android
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

默认 Base URL：`http://10.0.2.2:8000`（模拟器访问本机 API）。真机请在 Settings 改为 API 所在局域网地址，例如 `http://192.168.1.84:8000`。API 需 `--host 0.0.0.0`。

用 Android Studio 打开 `android/` 目录即可 Run。环境说明见 [`docs/android-dev-machine.md`](docs/android-dev-machine.md)。

## 下一步（M3）

- Android Chat 页 + 推送通知
- iOS App：Summary / Timeline / Search / Chat
- Home Assistant Integration
