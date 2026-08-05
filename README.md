# Nanexus AI Video Summary

Frigate 之上的 AI 视频摘要 / 时间线 / 语义检索（当前 **M1**）。

- 架构设计：[`docs/architecture.md`](docs/architecture.md)
- M0 总结：[`docs/m0-implementation.md`](docs/m0-implementation.md)
- M1 总结：[`docs/m1-implementation.md`](docs/m1-implementation.md)

## 当前能力

- Docker：PostgreSQL（pgvector）+ Redis + Mosquitto
- `mqtt_listener`：`frigate/events` → 落库 → Redis 队列
- `ai_worker`：拉取 snapshot → OpenCLIP caption/embedding（可 `AI_MODE=stub`）
- API：
  - `GET /timeline`
  - `GET /summary/today`
  - `POST /search`（语义检索）
  - `GET /events/{id}/snapshot`（本地图或跳转 Frigate）
- 无真实 Frigate：`scripts/seed_events.py` 生成演示图 + MQTT 事件

## 快速开始

### 1. 基础设施

```bash
cp .env.example .env
docker compose up -d
# 或: docker-compose up -d
```

Mosquitto 默认映射主机 **1884**（避免与已有 1883 冲突）。

### 2. Python 环境

```bash
python3 -m venv .venv
source .venv/bin/activate
# CPU 建议先装 PyTorch CPU wheel，再装项目：
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e .
```

首次运行会下载 OpenCLIP 权重，需联网。

### 3. 启动三个服务

```bash
source .venv/bin/activate
uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000
python -m services.mqtt_listener.main
python -m services.ai_worker.main
```

### 4. 演示与验收

```bash
python scripts/seed_events.py
# 等待 ai_worker 打出 processed ... OpenCLIP
python scripts/build_summary.py

curl -s localhost:8000/health | python -m json.tool
curl -s localhost:8000/timeline | python -m json.tool
curl -s localhost:8000/search \
  -H 'content-type: application/json' \
  -d '{"query":"black SUV","limit":5}' | python -m json.tool
curl -sI localhost:8000/events/6/snapshot

# 切换模型后重跑理解
python scripts/reprocess_events.py
```

API 文档：http://localhost:8000/docs

### 切换 stub（无 Torch 时）

```bash
# .env
AI_MODE=stub
```

## 目录结构

```text
docker-compose.yml
src/nanexus/          # config / models / vision / search / media
services/api/
services/mqtt_listener/
services/ai_worker/
scripts/              # seed / summary / reprocess / dev_up
docs/
data/snapshots/       # 本地演示快照（gitignore）
```

## 配置

见 `.env.example`。连真实 Frigate 时设置：

```bash
FRIGATE_BASE_URL=http://192.168.1.80:5000
MQTT_HOST=192.168.1.80
MQTT_PORT=1883
MQTT_TOPIC=frigate/events
```

然后重启三个服务，并导入历史事件（不必等新检测）：

```bash
python scripts/import_frigate_events.py -n 10 --force
```

`mqtt_listener` 会继续订阅实时 `frigate/events`。

## 下一步（M2）

- Summary Worker 定时 + LLM
- Chat（RAG over events/summaries）
- 更强 caption 模型（可选 BLIP）
