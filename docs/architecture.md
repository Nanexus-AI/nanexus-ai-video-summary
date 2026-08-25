# Nanexus AI Video Summary — 项目构想与架构设计

> 与 [Frigate](https://frigate.video/) 结合的 AI 视频摘要 / 智能安防助手。  
> 本文档由初步构想细化而来，作为后续设计与实现的基线。

阶段 9 部署边界：生产模式 fail closed，并从可信身份绑定 owner/site/role；服务身份与用户身份分离。启动验证 Event Intelligence capability，迁移只由 Alembic job 执行。readiness 区分 worker/model/基座降级，指标仅使用有界标签。一体/外接基座 Compose 均保持 Video Summary → Event Intelligence 单向 HTTP v1 依赖，旧链路继续保留回退。

阶段 8 客户端边界：Web/Android 默认只调用 Video Summary `/api/v1` 产品契约。Summary、Search 与异步 Chat 的关联对象均为 Event Intelligence Subject UUID，并经 Video Summary 的稳定 Subject Link 打开基座公开 Review/Evidence 入口。客户端不持有基座内部 URL/Token、不直连 Frigate、不复制 Review/Evidence 规则。Android Debug 可配置 LAN HTTP；Release 默认只允许 HTTPS。开发 `owner_id` 仅用于数据隔离；生产 ownership 来自阶段 9 的可信身份绑定。

---

## 1. 产品定位

面向已部署 Frigate 的家庭 / 小微场景用户，提供：

| 能力 | 说明 |
|------|------|
| **Daily Summary** | 每日事件自动摘要（“今天院子里发生了什么”） |
| **Timeline** | 可浏览的结构化事件时间线 |
| **Semantic Search** | 自然语言检索（“昨天拿纸箱的人”“红衣服”“黑 SUV”） |
| **Chat** | 基于历史事件的问答助手 |
| **Notification** | 智能通知（可对接 HA / 手机推送） |

**非目标（初期）：** 替代 Frigate 做检测与录像；本产品消费 Frigate 的事件、快照与片段，并在其上叠加理解与检索层。

---

## 2. 产品目标与约束

### 2.1 安装体验

目标形态：

```text
docker compose up
→ 填写 Frigate 地址 / MQTT / Token
→ 可用
```

### 2.2 部署覆盖

| 环境 | 优先级 |
|------|--------|
| Docker（Linux / NAS） | P0 |
| Windows / Linux 原生 | P1 |
| Home Assistant Add-on | P1 |
| iOS App（订阅产品） | P1（客户端） |

### 2.3 架构原则

1. **不做「LangChain + 单脚本 Demo」**：Demo 快，但维护、性能、部署、计费都难扩展。
2. **分层微服务**：各层独立扩缩、换 GPU、换模型，互不影响。
3. **异步优先**：事件入队再处理，避免 API 同步卡住。
4. **媒体仍归 Frigate**：只存 URI，不自建图片库。
5. **摘要预计算**：定时生成 Summary，客户端只读，控制 LLM 成本。

---

## 3. 总体架构

```text
                    iOS App / HA / Web
                           │
                    HTTPS / WebSocket
                           │
                    AI Assistant API
                           │
           ┌───────────────┼────────────────┐
           │               │                │
     Event Service    AI Service      Search Service
           │               │                │
           └───────────────┼────────────────┘
                           │
                    PostgreSQL (+ pgvector)
                           │
                   MQTT / Frigate API
                           │
                        Frigate
```

配套基础设施：

| 组件 | 职责 |
|------|------|
| **Redis** | 任务队列、缓存、限流 |
| **PostgreSQL + pgvector** | 业务数据 + 向量检索 |
| **Frigate** | 检测、录像、snapshot/clip（外部依赖） |

---

## 4. 服务分层

### 4.1 API Server（核心网关）

| 项 | 建议 |
|----|------|
| 技术 | **FastAPI（Python）** |
| 原因 | AI 生态（PyTorch / ONNX / Transformers / Whisper / YOLO / OpenCLIP 等）以 Python 为主；做 API 比 C++ 更合适 |

**示例 API：**

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/summary/today` | 今日摘要 |
| `GET` | `/timeline` | 事件时间线 |
| `POST` | `/chat` | 对话问答 |
| `POST` | `/search` | 语义搜索 |

**职责边界：** 鉴权、配置、查询、下发任务；**不**在请求路径里直接跑重模型或同步调 LLM。

> 为何不用 C++ 做 API：后续必接 LLM / Embedding / Reranker / Vision / Speech，Python 生态优势明显；C++ 会增加集成复杂度。

---

### 4.2 MQTT Event Service

独立服务（如 `mqtt_listener`）。

**职责：**

1. 订阅 `frigate/events`（及必要的相关 topic）
2. 解析事件（如 person / car 等）
3. 写入 PostgreSQL
4. 将「待分析」任务推入 Redis Queue，通知 AI Worker

**原则：** 不要把 MQTT 消费逻辑写进 API Server。多摄像头（如 100 路）时同步处理会导致 API 阻塞与积压。

**建议处理流：**

```text
Frigate MQTT event
  → mqtt_listener 校验 / 去重
  → 落库（raw event）
  → Redis enqueue（vision / caption / embed）
  → （可选）轻量通知
```

---

### 4.3 AI Worker（核心价值层）

独立服务（如 `ai_worker`），完全与 API 解耦。

**单事件管线（建议顺序）：**

```text
New Event
  → 读取 Snapshot（Frigate URI）
  → Vision 理解
  → Caption 生成
  → Embedding
  → 写回 PostgreSQL
```

**设计收益：**

- GPU 从 RTX 5060 升到 5090：只换 Worker / 模型配置，其它模块不动
- 可水平扩展多个 Worker 消费同一队列
- 失败重试、死信队列可单独演进

---

### 4.4 LLM / Summary Worker

**原则：** API Server **不**在用户请求时直接调用 LLM。

独立 `summary_worker`（可与 AI Worker 同仓库、不同进程）：

| 触发 | 行为 |
|------|------|
| 定时（如每日 23:50） | 读取当日全部事件 → 生成 Summary → 落库 |
| （可选）手动触发 | `POST /summary/regenerate` 入队 |

客户端：

```text
GET /summary/today  → 读已生成结果（低成本、低延迟）
```

**成本控制：** 摘要预计算 + 按日/按摄像头聚合，避免每次打开 App 都打 GPT。

---

### 4.5 Database：PostgreSQL + pgvector

**不用 SQLite 作为主库。** 中长期会有：Conversation、Summary、Tag、Embedding、Notification、User、Subscription 等，SQLite 维护成本会快速上升。

| 能力 | 方案 |
|------|------|
| 关系数据 | PostgreSQL |
| 向量检索 | **pgvector**（同库） |
| 外部向量库 | 初期 **不引入** Milvus / Pinecone / Qdrant |

语义搜索目标体验：

> 「昨天那个拿纸箱的人」→ 一条（或少量）SQL / 向量查询完成。

**建议核心实体（草案）：**

| 实体 | 主要字段（示意） |
|------|------------------|
| `events` | frigate_id, camera, label, start/end, snapshot_uri, clip_uri, caption, embedding, tags |
| `daily_summaries` | date, camera?, content, model, created_at |
| `conversations` | user_id, messages, related_event_ids |
| `users` / `subscriptions` | 账号与订阅（商业化） |
| `notifications` | channel, payload, status |

---

### 4.6 Redis

**必选。** 至少承担：

| 用途 | 说明 |
|------|------|
| 任务队列 | 新事件 → Queue → AI Worker |
| 去重 / 锁 | 同一 Frigate event 防重复处理 |
| 缓存 | 今日 summary、热点 timeline |
| （可选）限流 | API / LLM 调用配额 |

```text
新事件 → Redis Queue → AI Worker 异步处理
（禁止在 MQTT 回调里同步跑 Vision）
```

---

### 4.7 Object Storage 策略

**不自建图片/视频仓库。** 继续使用 Frigate 的：

- `clips/`
- `export/`
- `snapshot/`

数据库只存 URI，例如：

```text
event_id → snapshot_url / clip_url
```

访问时通过 Frigate API 或已配置的媒体路径代理，避免重复存储与同步问题。

---

### 4.8 搜索：视觉语义，而非全文

| 方案 | 结论 |
|------|------|
| 全文搜索（关键词） | 初期不做主力 |
| **OpenCLIP → Embedding → pgvector** | 推荐主路径 |

查询示例：

| 用户说法 | 期望 |
|----------|------|
| 红衣服 | 命中相关人物事件 |
| UPS | 命中快递车辆/人员 |
| 黑 SUV | 命中对应车辆片段 |

后续可加：**Reranker**、时间/摄像头过滤、多模态（图文联合）。

---

### 4.9 移动端：iOS（SwiftUI）

| 项 | 建议 |
|----|------|
| 框架 | **SwiftUI**（主攻 iOS） |
| 不用 | Flutter（与「长期 iOS + 订阅」目标不一致） |

**App 信息架构（MVP）：**

1. Summary  
2. Timeline  
3. Search  
4. Chat  
5. Notification  

通过 HTTPS / WebSocket 连接 AI Assistant API。

---

### 4.10 Home Assistant Integration

| 阶段 | 做法 |
|------|------|
| **先做** | 正式 Integration（非 HACS 卡片优先） |
| **实体示例** | AI Summary Sensor、AI Timeline、AI Notification |
| **后做** | Dashboard / Lovelace 卡片自动展示 |

目标：装好 Integration 后，Dashboard 能直接看到摘要与通知，而不是先做一个孤立的前端卡片。

---

## 5. 端到端数据流

### 5.1 实时事件理解

```text
Frigate 检测
  → MQTT frigate/events
  → mqtt_listener 落库 + 入队
  → ai_worker：snapshot → vision → caption → embedding
  → 可选：规则/LLM 判断是否推送通知
```

### 5.2 日终摘要

```text
定时触发（如 23:50）
  → summary_worker 聚合当日 events
  → LLM 生成结构化摘要
  → 写入 daily_summaries
  → App / HA Sensor 只读
```

### 5.3 语义搜索

```text
用户自然语言
  → API 生成 query embedding（OpenCLIP / text encoder）
  → pgvector 近邻检索 + 时间/摄像头过滤
  → （可选）Rerank
  → 返回事件列表 + Frigate 媒体 URI
```

### 5.4 对话

```text
用户提问
  → 检索相关 events / summaries
  → LLM 基于检索上下文回答（RAG）
  → 写入 conversations
```

---

## 6. 配置与首次引导

用户首次需提供（最少集）：

| 配置项 | 说明 |
|--------|------|
| Frigate 地址 | HTTP API Base URL |
| MQTT | Host / Port / Topic 前缀 / 账号 |
| Token / API Key | Frigate 或本服务鉴权 |
| （可选）GPU / 模型路径 | 本地推理资源 |
| （可选）LLM Provider | 本地或云端 API Key |

引导流程应在 Web UI 或 Onboarding 中完成，避免手改大量 YAML（HA Add-on 可再提供配置页）。

---

## 7. 技术选型汇总

| 层级 | 选型 | 备注 |
|------|------|------|
| API | FastAPI | 统一对外接口 |
| Event Ingest | 独立 MQTT Service | 与 API 解耦 |
| AI Pipeline | 独立 Worker | Vision / Caption / Embed |
| Summary | 独立 Worker + 定时任务 | 预计算，控成本 |
| DB | PostgreSQL + pgvector | 一体存储与检索 |
| Queue | Redis | 异步与稳定 |
| 媒体 | Frigate 既有存储 | 只存 URI |
| 搜索 | OpenCLIP + pgvector | 语义检索 |
| 客户端 | SwiftUI iOS | 订阅产品主端 |
| 智能家居 | HA Integration | Sensor / Timeline / Notify |
| 部署 | Docker Compose | 一键启动；后续 Add-on |

**明确不优先的路径：**

- LangChain 单体脚本作为产品骨架  
- API 内同步调 LLM  
- SQLite 作主库  
- 自建对象存储替代 Frigate 媒体  
- 初期上独立向量库集群  
- 以 HACS Card 作为 HA 集成起点  
- Flutter 作为主客户端  

---

## 8. 建议里程碑（细化）

### M0 — 骨架可运行

- [x] Docker Compose：API + MQTT Listener + Postgres + Redis  
- [x] 配置 Frigate / MQTT 后能稳定收事件并落库  
- [x] 基础 `GET /timeline`

### M1 — 理解层

- [x] AI Worker：snapshot → caption → embedding  
- [x] `POST /search`（pgvector）  
- [x] 媒体 URI 可从 API 回跳到 Frigate

### M2 — 摘要与成本可控

- [x] Summary Worker 日终任务  
- [x] `GET /summary/today`  
- [x] 基础 Chat（RAG over events/summaries）

### M3 — 客户端与 HA

- [ ] iOS App：Summary / Timeline / Search  
- [ ] HA Integration：Summary Sensor + Notification  
- [ ] 推送策略（重要事件 vs 日报）

### M4 — 产品化

- [ ] 用户与订阅模型  
- [ ] 多设备 / 多摄像头配额与限流  
- [ ] HA Add-on 打包  
- [ ] 可观测性（队列积压、Worker 失败率、LLM 费用）

---

## 9. 风险与开放问题

| 议题 | 说明 |
|------|------|
| 模型部署形态 | 全本地 / 混合云？影响隐私宣传与订阅定价 |
| LLM 选型 | 本地小模型做 caption/summary，还是云端大模型做日终摘要？ |
| 多租户 | 单机家庭版 vs 未来 SaaS 网关是否同构 |
| Frigate 版本兼容 | events MQTT payload、媒体 API 变更 |
| 隐私与合规 | 录像不出户 vs 云端增强功能的开关设计 |
| GPU 可选 | 无 GPU 时的 CPU/轻量模型降级路径 |

## 基座化阶段 6：Summary v1（2026-08-24）

本节取代上文旧 `daily_summaries` 设计作为新的基座化 Summary 路径；旧设计和接口暂时保留用于回退。

```text
Event Intelligence public /api/v1/events
  → ended-preferred Review DTO + canonical review_item_id
  → Video Summary summary_worker（本地日 UTC bounds、去重、评分）
  → Video Summary summaries（版本化、可追溯、可 supersede）
  → GET /api/v1/summaries/{local_date}（只读预计算结果）
```

边界不变量：Video Summary 不导入 Event Intelligence 源码/ORM，不读取其数据库，不直连 Frigate，不读取 Evidence 媒体；Event Intelligence 不依赖 Video Summary。基座公开 Review 详情提供 canonical Subject ID、Site/Camera timezone，并继续公开 Claim/Decision/Feedback。Summary Worker 只使用这些结构化 DTO。

`Summary` 由 Video Summary 独立拥有，包含本地日期、时区、Site/Camera、文本及结构化内容、所有来源 Subject、generator/model/prompt 版本、状态和 supersede 时间。`NULL camera_id` 使用 PostgreSQL `NULLS NOT DISTINCT` 唯一约束，保证站点级生成幂等。旧版本只在新结果 ready 后标记 superseded，不被覆盖或删除。

Rule v1 以 Decision、Feedback、Label、Zone、Duration、本地时间和高质量 Claim 做透明评分，并按等价摄像头/Label/Zone/Caption 压缩重复重点事件。LLM 只接收 Rule 结构化 Context；字符、Token 和估算 Cost 任一超限或调用失败都返回 Rule 结果。API 不同步生成；重建只入队，状态可通过 `/api/v1/summaries/jobs/{id}` 查询。

---

## 10. 一句话结论

**用 Docker Compose 交付一套「Frigate 事件 → 异步 AI 理解 → Postgres/pgvector 检索 → 预计算摘要」的分层系统；API 只做编排与查询，媒体继续交给 Frigate，客户端以 iOS + HA Integration 触达用户。**

## Migration maintenance boundary (BASELINE-001)

As of 2026-08-21, the following legacy infrastructure is frozen in maintenance mode:

- `services/mqtt_listener` and direct Frigate MQTT ingestion;
- the legacy `nanexus.models.Event` table and its mixed source/AI fields;
- Redis List/Set delivery in `src/nanexus/queue.py`;
- legacy media file reads and redirects in `services/api/main.py` and `src/nanexus/media.py`;
- OpenCLIP loading from the API search path.

These components remain runnable solely as migration and behavior references. Changes are limited to severe fixes required to unblock migration, preserve baseline execution, or export data. No new features may be added. This freeze does not change the runtime path and has no runtime rollback action.

The migration dependency remains one-way: Video Summary may consume only public, versioned Event Intelligence contracts. Event Intelligence must not depend on this repository. The projects must not share databases, ORM models, private Redis keys, internal media paths, or undeclared endpoints. Video Summary must not bypass Event Intelligence to access Frigate or Evidence.

## Frozen cross-project contract boundary (stage 1)

The only allowed dependency is `Video Summary → Event Intelligence` through published, versioned JSON. Event Intelligence owns the normative schemas; this repository keeps an independent consumer mirror and must not import Event Intelligence source, ORM, database models, broker envelopes, filesystem paths or Frigate adapters.

Processor v1 integration consists of ended `review_item` Jobs with opaque Snapshot Evidence IDs, structured Results with invocation facts and Caption/Tags claims, Capability negotiation, object-scoped Evidence read/Result submit authority, and default result reuse during Replay. Explicit reprocess is required for a new invocation.

Job possession alone grants no media access. Video Summary must use the future authorized Event Intelligence Evidence API and may not construct Frigate URLs. Normative decisions are ADR-011/012 in Event Intelligence; consumer acceptance is under `docs/architecture-reviews/`.

## Stage 3 public runtime boundary

Video Summary now integrates through EventIntelligenceClient only. It consumes the public Processor Capability, Job, Subject, job-scoped Evidence and Result endpoints using independent v1 DTO mirrors. It never imports base source or persistence types.

The external Stub Worker performs deterministic local processing and submits auditable invocation facts and a Caption Claim. The stage-3 Compose overlay selects ENRICHMENT_PROCESSOR_MODE=external; the base default remains internal_stub, preserving rollback and the old Video Summary chain.

## Stage 4 worker-only model boundary

OpenCLIP is now a Video Summary Provider loaded only by `services.event_intelligence_worker`. The normal API process defaults to keyword fallback and does not import Torch/OpenCLIP. A frozen legacy API inference switch exists only for rollback until the Search migration stage.

The Worker consumes opaque Evidence bytes solely through the Event Intelligence Processor API, validates type/size/decode, and writes only versioned Results. Event Intelligence remains the sole owner of Job, Evidence, Claim and ModelInvocation persistence. `MODEL_PROVIDER=stub|openclip` selects the implementation; Stub is the default and no cloud provider is registered.

## Stage 5 semantic Search boundary (2026-08-24)

Semantic vectors are application data owned by Video Summary. Event Intelligence owns canonical Subject, Claim and Evidence and exposes stable IDs only through Processor API v1. The enrichment worker submits Caption/Tags first, then queues a local embedding record using the public receipt. A separate embedding worker persists to Video Summary PostgreSQL/pgvector. Search API requests text vectors from a separate model service and never imports the heavy model runtime. Search results use Subject/Claim IDs and job-scoped Event Intelligence Evidence URLs; the frozen legacy Event table remains only for rollback paths and is not queried by `/api/v1/search`.
## Chat v1 boundary

Chat v1 is an application-owned asynchronous pipeline. The API persists `Conversation`/`ChatMessage` and queues `ChatJob`; the dedicated Chat Worker alone performs versioned Search/Summary retrieval and optional LLM generation. Search and Summary already consume Event Intelligence through public contracts, so Chat never reads the legacy Event table, imports Event Intelligence ORM, shares its database, or accesses Frigate/Evidence. Citations are stable Event Intelligence Subject UUIDs. The old synchronous `/chat` remains rollback-only until a later client migration and retirement gate.
