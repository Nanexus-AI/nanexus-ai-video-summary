# Nanexus AI Video Summary

Frigate 之上的 AI 视频摘要 / 时间线 / 语义检索 / 问答（当前 **M2**）。

- 架构设计：[`docs/architecture.md`](docs/architecture.md)
- M0 总结：[`docs/m0-implementation.md`](docs/m0-implementation.md)
- M1 总结：[`docs/m1-implementation.md`](docs/m1-implementation.md)
- M2 总结：[`docs/m2-implementation.md`](docs/m2-implementation.md)

## 当前能力

- Docker：PostgreSQL（pgvector）+ Redis + Mosquitto
- `mqtt_listener`：`frigate/events` → 落库 → Redis 队列
- `ai_worker`：snapshot → OpenCLIP caption/embedding
- `summary_worker`：日终/队列预计算摘要（rule 或 LLM）
- API：
  - `GET /timeline` / `GET /summary/today`
  - `POST /search` / `POST /chat`
  - `GET /events/{id}/snapshot`
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

## 下一步（M3）

- iOS App：Summary / Timeline / Search / Chat
- Home Assistant Integration
- 通知策略
