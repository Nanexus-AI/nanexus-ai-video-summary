# M0 实现总结：环境搭建、步骤与代码说明

本文记录从架构构想到可运行产品雏形（M0）的落地过程，包括环境分工、实现内容、数据流、验证结果与已知问题。

相关文档：

- 架构设计：[architecture.md](./architecture.md)
- 快速上手：[../README.md](../README.md)

---

## 1. 目标与范围

### 1.1 M0 要证明什么

在不引入真实 Vision / LLM 的前提下，打通：

```text
Frigate 风格 MQTT 事件
  → mqtt_listener 落库 + 入队
  → ai_worker（stub）写 caption / embedding
  → API 提供 timeline / summary
```

### 1.2 M0 明确不做

| 不做 | 原因 |
|------|------|
| OpenCLIP / 真视觉模型 | 放到 M1 |
| 云端/本地 LLM 日终摘要 | M0 用规则摘要代替 |
| iOS / Home Assistant Integration | 后续客户端阶段 |
| 订阅 / 多租户 | 产品化阶段 |
| 自建媒体存储 | 仍只存 Frigate URI |

---

## 2. 环境策略

采用「Docker 管基础设施 + Python venv 跑业务服务」：

| 层级 | 方式 | 组件 |
|------|------|------|
| 基础设施 | Docker Compose | PostgreSQL(+pgvector)、Redis、Mosquitto |
| 业务服务 | 本机 `.venv` | API、mqtt_listener、ai_worker |
| 演示数据 | 本机脚本 | `seed_events.py`（无需真实 Frigate） |

这样做的原因：

1. **开发快**：改 Python 代码无需重建镜像。
2. **依赖稳**：数据库 / 队列 / MQTT 版本固定、可复现。
3. **与部署路径一致**：未来把三个服务也放进 Compose 即可，架构不用改。

---

## 3. 搭建步骤（实际执行过程）

### 步骤 A：准备配置

```bash
cd /path/to/nanexus_ai_video_summary
cp .env.example .env
```

关键配置（默认值）：

| 变量 | 默认 | 说明 |
|------|------|------|
| `DATABASE_URL` | `postgresql+psycopg://nanexus:nanexus@localhost:5432/nanexus` | Postgres |
| `REDIS_URL` | `redis://localhost:6379/0` | 队列 |
| `MQTT_HOST` / `MQTT_PORT` | `localhost` / `1884` | Mosquitto |
| `MQTT_TOPIC` | `frigate/events` | Frigate 事件主题 |
| `FRIGATE_BASE_URL` | `http://localhost:5000` | 拼 snapshot/clip URI |
| `EMBEDDING_DIM` | `512` | 向量维度（为 OpenCLIP 预留） |

### 步骤 B：启动基础设施

```bash
docker compose up -d
# 若无 compose 插件：
# docker-compose up -d
```

或使用一键脚本（会创建 `.env`、起容器、建 venv、安装包）：

```bash
chmod +x scripts/dev_up.sh
./scripts/dev_up.sh
```

### 步骤 C：创建 Python 虚拟环境并安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

`pyproject.toml` 把 `src/nanexus` 装成可编辑包，三个服务都能 `import nanexus`。

### 步骤 D：启动三个业务进程（三个终端）

```bash
source .venv/bin/activate

# 终端 1：API
uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2：MQTT 消费
python -m services.mqtt_listener.main

# 终端 3：AI Worker
python -m services.ai_worker.main
```

### 步骤 E：灌演示数据并验收

```bash
source .venv/bin/activate
python scripts/seed_events.py
python scripts/build_summary.py

curl -s localhost:8000/health | python -m json.tool
curl -s 'localhost:8000/timeline?limit=5' | python -m json.tool
curl -s localhost:8000/summary/today | python -m json.tool
```

交互式文档：http://localhost:8000/docs

---

## 4. 搭建过程中遇到的问题

### 4.1 系统没有 `docker compose` 插件

本机 Docker 有 daemon，但无 Compose 插件 / `docker-compose` 命令。

**处理：** 下载独立二进制到用户目录：

```bash
curl -fsSL \
  https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64 \
  -o ~/.local/bin/docker-compose
chmod +x ~/.local/bin/docker-compose
```

`scripts/dev_up.sh` 已兼容 `docker compose` 与 `docker-compose` 两种调用。

### 4.2 主机 1883 端口已被占用

机器上已有独立 `mosquitto` 容器占用 `1883`。

**处理：** 本项目 Compose 将 Mosquitto 映射为 `1884:1883`，`.env` 中 `MQTT_PORT=1884`。

连真实 Frigate 时，把 `MQTT_*` 改成 Frigate 实际使用的 Broker 即可，不必一定用本项目自带的 Mosquitto。

---

## 5. 仓库结构

```text
nanexus_ai_video_summary/
├── docker-compose.yml          # postgres / redis / mosquitto
├── docker/
│   ├── postgres/init.sql       # CREATE EXTENSION vector
│   └── mosquitto/mosquitto.conf
├── .env.example
├── pyproject.toml              # 可编辑安装 nanexus 包
├── requirements.txt
├── README.md
├── docs/
│   ├── architecture.md         # 总体架构
│   └── m0-implementation.md    # 本文
├── src/nanexus/                # 共享库
│   ├── config.py               # pydantic-settings
│   ├── db.py                   # SQLAlchemy engine / init_db
│   ├── models.py               # Event / DailySummary
│   ├── schemas.py              # API Pydantic 模型
│   ├── queue.py                # Redis 队列 AIJob
│   ├── frigate.py              # MQTT payload 归一化
│   └── summary.py              # 规则摘要（LLM 占位）
├── services/
│   ├── api/main.py             # FastAPI
│   ├── mqtt_listener/main.py   # 事件接入
│   └── ai_worker/main.py       # stub AI 管线
└── scripts/
    ├── dev_up.sh
    ├── seed_events.py
    └── build_summary.py
```

---

## 6. 实现说明

### 6.1 数据模型

**`events`**

| 字段 | 说明 |
|------|------|
| `frigate_id` | Frigate 事件 ID（唯一） |
| `camera` / `label` / `sub_label` | 摄像头与检测类别 |
| `start_time` / `end_time` | 时间范围 |
| `snapshot_uri` / `clip_uri` | 指向 Frigate 的媒体 URI（不存文件） |
| `caption` | AI 描述（M0 为 stub） |
| `embedding` | `pgvector` 向量（M0 为确定性伪向量） |
| `tags` | 标签数组 |
| `status` | `pending` → `queued` → `processing` → `done` / `failed` |
| `raw_payload` | 原始 MQTT JSON |

**`daily_summaries`**

| 字段 | 说明 |
|------|------|
| `summary_date` | 日期 |
| `camera` | 可选；`NULL` 表示全摄像头汇总 |
| `content` | 摘要正文 |
| `model` | M0 固定为 `rule-v0` |
| `event_count` | 聚合事件数 |

### 6.2 MQTT Listener

文件：`services/mqtt_listener/main.py`

职责：

1. 连接 Mosquitto，订阅 `frigate/events`
2. 用 `parse_frigate_event()` 归一化 payload（兼容 `type/after` 与裸事件）
3. 按 `frigate_id` upsert 到 Postgres
4. Redis `SADD` 去重后，将 `AIJob` `LPUSH` 入队
5. 事件状态改为 `queued`

原则：**不在 MQTT 回调里跑模型**，只做接入与投递。

### 6.3 AI Worker（Stub）

文件：`services/ai_worker/main.py`

职责：

1. `BRPOP` 消费 Redis 队列
2. 读取事件 → `status=processing`
3. 生成 stub caption（基于 camera/label/sub_label）
4. 生成确定性伪 embedding（hash → 归一化向量，维度 `EMBEDDING_DIM`）
5. 写回 `caption` / `embedding` / `tags`，`status=done`

后续替换点非常集中：把 stub 两函数换成「拉 snapshot + OpenCLIP / caption 模型」即可，队列与表结构可复用。

### 6.4 API Server

文件：`services/api/main.py`

| 接口 | 作用 |
|------|------|
| `GET /health` | 检查 DB / Redis |
| `GET /timeline` | 事件列表（支持 camera/label/分页） |
| `GET /summary/today` | 读预计算摘要；没有则返回 fallback 文案 |
| `POST /summary/regenerate` | 触发规则摘要重建并落库 |
| `GET /docs` | Swagger UI |

启动时调用 `init_db()`：确保 `vector` 扩展存在并建表。

### 6.5 规则摘要（Summary 占位）

文件：`src/nanexus/summary.py` + `scripts/build_summary.py`

按日统计 label/camera，并列出带 caption 的 highlights。这是 LLM Summary Worker 的可替换占位：接口形态（写入 `daily_summaries`，客户端只 `GET`）已与架构文档一致。

### 6.6 演示种子数据

文件：`scripts/seed_events.py`

向 MQTT 发布若干 Frigate 风格 `type=new` 消息（person / car / package / dog 等），用于无 Frigate 环境的端到端演示。

---

## 7. 端到端数据流（M0）

```text
seed_events / 真实 Frigate
        │  MQTT  frigate/events
        ▼
 mqtt_listener
        │  upsert events
        │  Redis LPUSH AIJob
        ▼
   ai_worker (stub)
        │  caption + embedding
        │  status=done
        ▼
    PostgreSQL
        ▲
        │  SELECT
   FastAPI (/timeline, /summary/today)
        ▲
   curl / 未来 iOS / HA
```

摘要路径（当前手动/脚本触发）：

```text
build_summary.py 或 POST /summary/regenerate
  → 聚合当日 events
  → 写入 daily_summaries
  → GET /summary/today 只读
```

---

## 8. 验收结果（首次联调）

本机首次跑通时观测到：

| 检查项 | 结果 |
|--------|------|
| Compose 三容器 | postgres / redis / mosquitto 正常 |
| `/health` | `{"status":"ok","database":true,"redis":true}` |
| 种子事件 | 发布 5 条 |
| AI Worker | 5 条均 `status=done`，带 stub caption |
| `/timeline` | `total=5`，含 snapshot URI 与 tags |
| `/summary/today` | 返回 `rule-v0` 预计算摘要 |

示例摘要片段：

```text
Summary for 2026-08-05
Total events: 5
By label: person=2, car=1, package=1, dog=1
...
- [16:13] driveway: Stub vision: black SUV near driveway
- [16:13] driveway: Stub vision: UPS near driveway
```

---

## 9. 技术选型对照（M0 落地版）

| 架构文档建议 | M0 实际 |
|--------------|---------|
| FastAPI | ✅ `services/api` |
| 独立 MQTT Service | ✅ `services/mqtt_listener` |
| 独立 AI Worker | ✅ stub 实现 |
| PostgreSQL + pgvector | ✅ `pgvector/pgvector:pg16` |
| Redis 队列 | ✅ list + processed set |
| 媒体只存 URI | ✅ |
| Summary 预计算 | ✅ 规则版占位 |
| OpenCLIP / LLM | ❌ 下一阶段 |
| iOS / HA | ❌ 下一阶段 |

---

## 10. 常用命令速查

```bash
# 基础设施
docker compose up -d
docker compose ps
docker compose logs -f postgres

# 服务
source .venv/bin/activate
uvicorn services.api.main:app --reload --port 8000
python -m services.mqtt_listener.main
python -m services.ai_worker.main

# 演示
python scripts/seed_events.py -n 10
python scripts/build_summary.py
curl -s localhost:8000/timeline | python -m json.tool

# 停止基础设施
docker compose down
```

---

## 11. 下一步（M1 建议）

按 [architecture.md](./architecture.md) 里程碑：

1. **AI Worker 真实化**：下载 Frigate snapshot → caption → OpenCLIP embedding 写回
2. **`POST /search`**：query 文本编码 + pgvector 近邻 + 时间/摄像头过滤
3. **Summary Worker**：定时任务 +（可选）LLM，替换 `rule-v0`
4. **配置引导页**：填写 Frigate / MQTT / Token 后持久化
5. **Compose 打包业务服务**：向「`docker compose up` 即用」再靠拢一步

---

## 12. 一句话总结

M0 用 Docker 固定 Postgres/Redis/MQTT，用 venv 跑三个 Python 进程，以 stub AI 打通「事件接入 → 异步理解字段 → 时间线/摘要可读」闭环；架构边界已按微服务切开，后续只需替换 Worker 与摘要实现，无需推倒重来。
