# Nanexus AI Video Summary

Frigate 之上的 AI 视频摘要 / 时间线 / 语义检索雏形（M0）。

- 架构设计：[`docs/architecture.md`](docs/architecture.md)
- M0 步骤 / 实现总结：[`docs/m0-implementation.md`](docs/m0-implementation.md)

## M0 能力

- Docker：PostgreSQL（pgvector）+ Redis + Mosquitto
- `mqtt_listener`：订阅 `frigate/events` → 落库 → Redis 队列
- `ai_worker`：stub caption / embedding（后续换成 OpenCLIP）
- API：`GET /timeline`、`GET /summary/today`、`POST /summary/regenerate`
- 无真实 Frigate 时可用 `scripts/seed_events.py` 灌演示事件

## 快速开始

### 1. 基础设施

```bash
cp .env.example .env
# 若系统没有 `docker compose` 插件，可用独立二进制：
# curl -fsSL https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64 \
#   -o ~/.local/bin/docker-compose && chmod +x ~/.local/bin/docker-compose
docker compose up -d
# 或: docker-compose up -d
```

默认把 Mosquitto 映射到主机 **1884**（很多机器上 1883 已被占用）。`.env` 里 `MQTT_PORT` 需与之一致。

或一键：

```bash
chmod +x scripts/dev_up.sh
./scripts/dev_up.sh
```

### 2. Python 虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. 启动三个服务（三个终端）

```bash
source .venv/bin/activate

# API
uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000

# MQTT listener
python -m services.mqtt_listener.main

# AI worker (stub)
python -m services.ai_worker.main
```

### 4. 灌入演示事件并生成摘要

```bash
source .venv/bin/activate
python scripts/seed_events.py
python scripts/build_summary.py

curl -s localhost:8000/health | python -m json.tool
curl -s localhost:8000/timeline | python -m json.tool
curl -s localhost:8000/summary/today | python -m json.tool
```

API 文档：http://localhost:8000/docs

## 目录结构

```text
docker-compose.yml          # postgres / redis / mosquitto
src/nanexus/                # 共享库：config、models、queue、summary
services/api/               # FastAPI
services/mqtt_listener/     # Frigate MQTT 消费
services/ai_worker/         # 异步 AI 管线（当前 stub）
scripts/                    # seed / summary / dev_up
docs/architecture.md        # 架构设计
```

## 配置

见 `.env.example`。连真实 Frigate 时设置：

- `FRIGATE_BASE_URL`
- `MQTT_HOST` / `MQTT_PORT` / `MQTT_TOPIC`（默认 `frigate/events`）

## 下一步（M1）

- AI Worker 接入真实 snapshot 拉取 + OpenCLIP embedding
- `POST /search`（pgvector）
- 真正的 Summary Worker / LLM
