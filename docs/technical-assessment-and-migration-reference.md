# Nanexus Video Summary 技术评估与基座化改造参考

> 文档状态：初始技术评估
> 评估日期：2026-08-20
> 适用项目：`nanexus_ai_video_summary`
> 目标基座：`nanexus_frigate_extension` / Nanexus Event Intelligence

## 1. 文档目的

本文记录 Nanexus Video Summary 当前实现的技术状况、主要风险、值得保留的产品资产，以及未来基于 Nanexus Event Intelligence 进行渐进式改造的建议。

本文不是当前系统的生产就绪声明，也不是一次性重写计划。它用于后续架构设计、任务拆分、迁移验收和开源边界讨论，避免在改造过程中重复分析已经明确的问题。

## 2. 总体结论

Nanexus Video Summary 是一个思路完整、技术选型基本合理、已经跑通端到端链路的 M2 原型。它验证了以下产品路径：

```text
Frigate Event
  → 事件接入与持久化
  → Snapshot AI 分析
  → Caption / Tags / Embedding
  → Timeline / Semantic Search / Daily Summary / Chat
  → Android 客户端
```

项目的主要价值在于验证了上层产品能力，而不是当前的基础设施实现。当前后端适合概念演示和局域网开发，不适合直接作为长期生产架构继续堆叠功能。

未来应将 Nanexus Event Intelligence 作为唯一长期基座，让 Video Summary 逐步退役重复的事件接入、事件模型、媒体代理、队列和持久化能力，只保留并发展摘要、语义检索、问答和客户端体验等高级功能。

推荐的长期关系是：

```text
Nanexus Event Intelligence
通用事件智能基座 / 中间件 / Extension
        ↑
        │ 稳定 API、事件订阅、Processor Contract
        │ Evidence、Claim、Model Invocation 契约
        │
Nanexus Video Summary
独立开源的高级应用产品
        ├── AI Enrichment Worker
        ├── Embedding / Semantic Search
        ├── Daily / Weekly Summary
        ├── Event Chat
        ├── Web
        └── Android / iOS
```

两个项目应保持独立仓库、独立版本和独立发布，但依赖方向必须始终保持单向：

```text
Video Summary → Event Intelligence
Event Intelligence ✕→ Video Summary
```

## 3. 当前技术栈

### 3.1 后端

- Python 3.11+
- FastAPI
- Pydantic / Pydantic Settings
- SQLAlchemy 2，同步模式
- PostgreSQL 16
- pgvector
- Redis List / Set
- Paho MQTT
- HTTPX
- PyTorch / TorchVision
- OpenCLIP
- OpenAI-compatible Chat Completions

### 3.2 当前服务划分

- `mqtt_listener`：订阅 `frigate/events`，写入事件并投递 AI 任务；
- `ai_worker`：读取 Snapshot，生成模板 Caption、Tags 和 Embedding；
- `summary_worker`：按计划或队列生成日摘要；
- FastAPI API：提供 Timeline、Summary、Search、Chat、Conversation 和媒体接口。

### 3.3 基础设施

- PostgreSQL + pgvector；
- Redis；
- Mosquitto；
- 当前 Compose 只启动基础设施，四个应用服务仍需手动运行。

### 3.4 Android

- Kotlin；
- Jetpack Compose；
- Material 3；
- Navigation Compose；
- ViewModel + StateFlow；
- Retrofit + OkHttp；
- Kotlin Serialization；
- DataStore；
- Coil。

当前 Android App 已有 Summary、Timeline、Search、Event Detail 和 Settings 等基础页面，属于可运行的轻量 MVP。

## 4. 当前实现中值得保留的资产

后续改造不应简单推倒重来。以下内容具有明确的复用或参考价值：

1. Summary、Timeline、Search、Chat 的产品信息架构；
2. FastAPI/Pydantic API Schema 所表达的原始业务需求；
3. OpenCLIP 图像/文本 Embedding 与 pgvector 检索的可行性验证；
4. Rule 模式和 LLM 模式之间的降级思路；
5. Summary 预计算、客户端只读的成本控制思路；
6. Chat 返回相关事件 ID 的可解释设计；
7. Android Compose 客户端和现有页面流程；
8. 本地模型、云端模型可替换的配置方向；
9. Seed、Import、Reprocess 等开发演示工具；
10. M0、M1、M2 实现文档及其产品演进记录。

这些资产应在迁移中被提炼成测试用例、API 契约或产品验收标准，而不应只作为旧代码保留。

## 5. 主要结构性问题

### 5.1 Redis 队列不具备可靠投递语义

当前任务队列使用 `LPUSH + BRPOP`。Worker 从 Redis 取出任务时，任务立即从队列消失。如果 Worker 在处理过程中崩溃、断电或被终止，任务无法恢复。

当前实现缺少：

- ACK；
- Pending 状态；
- Visibility Timeout；
- 自动重试；
- Dead Letter Queue；
- 任务租约；
- 消费者恢复。

去重流程还存在永久漏处理窗口：系统先将 Frigate ID 写入 Redis `processed_set`，再将任务入队。如果写入 Set 成功但入队失败，后续相同事件会因为已经标记为 processed 而无法重新入队。

AI Worker 处理失败时只把数据库状态设为 `failed`，不会清除去重标记或自动重新投递。因此失败任务可能永久停留。

#### 改造方向

不继续扩展旧队列，直接复用 Event Intelligence 已有的：

- Transactional Outbox；
- Redis Stream；
- Consumer Group；
- ACK / Pending；
- Retry；
- DLQ；
- 稳定幂等键。

这是迁移中的最高优先级基础能力之一。

### 5.2 AI 模型在 API 请求进程内加载和运行

语义搜索会在 FastAPI 请求路径内调用 Vision Pipeline 生成文本 Embedding。第一次 Search 请求可能直接加载 PyTorch 和完整 OpenCLIP 模型。

这会导致：

- API 首次请求延迟很高；
- API 进程占用大量内存或 GPU 显存；
- 多个 API Worker 分别加载模型；
- 模型崩溃可能影响整个 API；
- 无法独立扩缩 AI 推理资源；
- 与项目文档中“API 不运行重模型”的原则冲突。

LLM Chat 也直接在 API 请求路径内同步调用外部服务。可选的同步 Summary regenerate 同样会在请求内运行生成逻辑。

#### 改造方向

所有模型调用统一经过 Model Provider / Model Gateway。重模型运行在独立 Worker 或独立推理服务中，API 只负责授权、参数校验、任务下发和结果读取。

### 5.3 Event 数据模型混合来源事实和 AI 解释

当前 `Event` 同时保存：

- Frigate 来源 ID 和原始 Payload；
- Camera、Label 和时间；
- Snapshot / Clip URI；
- AI Caption；
- AI Tags；
- Embedding；
- AI 处理状态。

这种结构适合 MVP，但不适合长期演进：

- 新模型运行会覆盖旧结果；
- 无法同时保存多个模型的不同解释；
- Caption 看起来像来源事实；
- 无法完整记录模型、版本、Prompt、耗时和错误；
- 无法表示 abstention 和 confidence 语义；
- Embedding 与固定全局维度耦合；
- Observation 修订与 AI 重处理缺少清晰关系。

#### 改造方向

迁移到基座的 Canonical Domain Model：

```text
Observation       来源事实
ReviewItem        可复核事件及生命周期聚合
Evidence          Snapshot / Clip / Preview 引用
Claim             Caption / Tags / 结构化解释
ModelInvocation   模型、版本、输入、耗时、错误和隐私路由
EmbeddingRecord   向量、维度、模型和被向量化对象
```

AI 结果不得覆盖 Observation。每个结果必须可追溯到 Evidence、模型版本和调用记录。

### 5.4 没有正式数据库迁移体系

当前使用 `Base.metadata.create_all()` 在启动时建表，只能创建缺失对象，无法安全处理：

- 列类型变更；
- 非空列新增；
- 索引变更；
- 向量维度变化；
- 数据回填；
- 约束升级；
- 版本升级和回滚。

开源项目一旦开始发布多个版本，这会立即成为升级障碍。

#### 改造方向

所有数据库结构通过 Alembic 管理。基座实体进入 Event Intelligence migration；Video Summary 独有的 Summary、Conversation 或应用索引进入 Video Summary 自己的 migration。

### 5.5 媒体读取边界过宽

当前媒体函数可以读取：

- 任意 HTTP/HTTPS URL；
- 任意 `file://` 路径；
- 任意本地路径；
- HTTP Redirect 的最终目标。

同时没有严格限制：

- 允许访问的 Origin；
- 响应 Content-Type；
- 响应体大小；
- Redirect 目标；
- Token 可以发送到的 Host；
- 文件系统允许读取的目录。

这可能形成 SSRF、内网探测、本地文件读取、凭据误发和内存消耗问题。

API 还可能把客户端直接重定向到 Frigate 内部地址，暴露内部网络结构并绕过统一 Evidence 授权。

#### 改造方向

Video Summary 不再实现媒体代理，统一使用基座 Evidence API。基座负责 Origin 钉扎、凭据隔离、响应限长、类型白名单、访问审计和隐私策略。

### 5.6 缺少身份认证和资源所有权

当前 API 没有内置认证，所有事件、媒体、Conversation、Summary regenerate 和 Event reprocess 接口均可直接访问。Chat 请求中的 `user_id` 由客户端直接提交，Conversation 通过自增数字 ID 读取，没有所有权验证。

这只适合可信开发局域网，不适合：

- 公网部署；
- 手机远程访问；
- 多用户；
- 多站点；
- 云端模型授权；
- 商业订阅。

#### 改造方向

至少区分：

- 最终用户身份；
- Video Summary 服务身份；
- Processor 写回权限；
- Evidence 读取权限；
- 管理操作权限；
- 普通只读权限。

认证与授权应优先由基座或统一网关提供，Video Summary 不应另建不兼容的身份体系。

## 6. AI 能力和产品语义问题

### 6.1 当前 OpenCLIP 不是完整 Caption 模型

当前视觉处理本质是图像 Embedding 与一组固定 Zero-shot Labels 比较，然后把 Top-K 标签拼接成模板文本。

它能够验证图文 Embedding 和粗粒度分类，但不能稳定理解：

- 人物正在执行的动作；
- 包裹和手持物体；
- 目标间关系；
- 车辆方向和行为；
- 事件发展的时间过程；
- 某个事件为什么重要。

因此当前 Caption 更准确地说是模板化的 Zero-shot Enrichment。

#### 后续建议

模型能力可以分层：

```text
轻量本地模型
  → Embedding / 粗分类 / 低成本过滤

VLM
  → Caption / 结构化事件解释

事件聚合
  → 生命周期 / 多帧 / Review / Scenario

LLM
  → Daily Summary / Chat / 用户化表达
```

OpenCLIP 可以继续承担 Embedding 和粗标签，但不应被视为最终视频理解模型。

### 6.2 当前主要分析单张 Snapshot，而非 Video

项目名称是 Video Summary，但 Worker 当前主要读取单张 Snapshot，没有实现：

- Clip 抽帧；
- 多帧代表图选择；
- 行为时间分析；
- 轨迹理解；
- 音频；
- Review 全生命周期上下文。

当前能力更接近 Frigate Event Snapshot Summary。这个范围对 MVP 是合理的，但开源产品说明必须准确，后续应基于 ReviewItem 和多个 Evidence 扩展为真正的事件或视频摘要。

### 6.3 Daily Summary 缺少事件聚合和重要性判断

当前 Daily Summary 主要按日期读取所有 Event，统计 Label 和 Camera，并将前 30～40 条事件直接列出或交给 LLM 改写。

尚未处理：

- 同一对象的多次更新；
- Review 与 Object 去重；
- 重复事件压缩；
- 重要性排序；
- Decision 和 Feedback；
- 场景聚类；
- 异常性；
- 多摄像头关联。

后续第一版应基于 ReviewItem，而不是底层 Observation。更高层摘要应逐步基于 Scenario。

### 6.4 日期与时区语义不一致

Summary Worker 可以在配置时区中决定“今天”，但数据库查询区间固定按 UTC 零点切分。对 Toronto 等时区，用户理解的本地日期和实际加载的事件范围可能不同。

正确语义应为：

```text
用户/站点本地日期
  → 站点时区 00:00–24:00
  → 转换成 UTC 查询范围
```

时区应主要来自 Site 或 Camera 配置，而不是单一进程环境变量。

### 6.5 Chat 是初级 RAG 验证

当前 Chat 的优点包括：

- 限定基于检索上下文回答；
- 可以引用相关 Event ID；
- LLM 未配置或失败时有 Extractive 降级。

但仍存在：

- 固定最近三天检索；
- 不解析“昨天”“上周”“下午三点”等时间表达；
- 最近 Summary 的选择比较粗糙；
- Conversation 消息保存在单个 JSON 数组；
- 对话增长后更新成本持续上升；
- 没有 Token Budget；
- 没有 Prompt/Model Invocation 审计；
- LLM 调用阻塞 API；
- 多用户资源隔离缺失。

因此 Chat 应继续被视为产品方向验证，而不是稳定的安防问答实现。

## 7. 工程质量与发布问题

### 7.1 自动化测试基本缺失

当前没有形成 Python 后端测试套件，Android 也没有实际单元测试或 Instrumentation Test。

以下行为缺少回归保护：

- Frigate Payload 兼容；
- MQTT 重复和乱序事件；
- Redis 故障窗口；
- Worker 崩溃恢复；
- Summary 幂等；
- 时区边界；
- 向量维度和模型升级；
- API Schema；
- Conversation；
- 媒体安全；
- Android DTO 与服务端兼容。

本次评估运行了 Python `compileall` 和核心依赖导入检查，两项通过。该结果只说明语法及基础导入正常，不代表功能和集成行为已经验证。

### 7.2 Python 依赖没有锁定

项目同时维护 `requirements.txt` 和 `pyproject.toml`，但没有 lock 文件和明确的兼容上限。

PyTorch、TorchVision、OpenCLIP 对 CPU/CUDA、操作系统和 Wheel 来源比较敏感，容易造成不可复现构建。

后续建议：

- 使用 `uv.lock` 或等价锁定方案；
- 区分核心依赖、OpenCLIP、CUDA 和开发依赖；
- 模型能力作为 Optional Extra；
- 在容器和 CI 中验证 CPU 基线；
- 明确模型权重下载和缓存策略。

### 7.3 Compose 尚未提供完整产品启动

当前 Compose 只启动 PostgreSQL、Redis 和 Mosquitto。API、MQTT Listener、AI Worker 和 Summary Worker 仍需手动启动。

长期 Video Summary 发行包应能够：

- 启动或连接兼容版本的 Event Intelligence；
- 启动 Video Summary API；
- 启动 AI/Summary Worker；
- 启动 Web；
- 通过 Profile 选择本地模型或云模型；
- 执行数据库 Migration；
- 检查基座 Capability 和版本兼容性；
- 提供完整 Health Check。

### 7.4 API 缺少正式版本前缀和能力协商

当前 API 直接使用 `/timeline`、`/search`、`/chat` 等路径。未来独立发布后，应建立：

- 正式 API 版本；
- Capability Discovery；
- Contract Version；
- 向后兼容策略；
- Error Schema；
- 分页契约；
- 基座兼容矩阵。

建议提供类似：

```text
GET /api/v1/capabilities
```

返回 Event Intelligence API 版本、Canonical Schema 版本、Evidence 能力、Claim 写回能力和事件订阅能力。

## 8. Android App 评估

### 8.1 当前优点

Android App 是结构清楚的小型 Compose MVP：

- API 调用集中在 Retrofit Interface；
- Repository 隔离网络访问；
- DTO 使用 Kotlin Serialization；
- 设置使用 DataStore；
- 页面状态通过 ViewModel 和 StateFlow 管理；
- Summary、Timeline、Search、Detail 和 Settings 边界明确。

目前不需要为了架构形式将 Android 单独拆成第三个仓库。它在产品上仍属于 Video Summary，建议继续留在 Video Summary 仓库，并保持公开 API 边界。

### 8.2 当前限制

- 没有自动化测试；
- 没有认证和 Token 管理；
- 没有本地缓存和离线体验；
- 没有完整分页状态；
- 没有重试/退避策略；
- 没有 Chat 页面；
- 没有推送；
- 没有多站点；
- 没有 Capability Negotiation；
- 错误消息和部分 UI 文本硬编码；
- DTO 与当前旧后端 Event 模型直接耦合。

### 8.3 明文 HTTP

当前 Android Manifest 和 Network Security Config 全局允许 Cleartext HTTP。这适合模拟器和可信局域网开发，不适合正式发布。

后续应区分：

```text
debug   → 可选择允许局域网 HTTP
release → 默认强制 HTTPS
```

正式客户端还需要服务配对、Token 安全存储、证书策略、远程访问和多服务器切换。

### 8.4 仓库拆分判断

在以下条件出现之前，Android/iOS 建议继续留在 Video Summary 仓库：

- 独立移动团队；
- 独立品牌和发布节奏；
- 同时连接多个 Nanexus 产品；
- 正式进入 App Store / Google Play；
- 移动端开源范围或许可证与后端不同；
- 演化为统一的 Nanexus Mobile 产品。

即使将来需要拆分，也可以保留目录历史后再提取仓库，不必现在提前承担跨仓库协调成本。

## 9. 与 Event Intelligence 的职责边界

### 9.1 应由基座提供的能力

- Source Adapter 和 Frigate 接入；
- Canonical Observation / ReviewItem / Camera；
- Evidence 引用和安全媒体代理；
- 生命周期和来源 ID 映射；
- Transactional Outbox；
- Redis Stream / Retry / DLQ；
- Claim 和 Model Invocation 契约；
- 通用 Processor / Plugin 生命周期；
- 隐私路由和模型调用审计；
- 身份、服务授权和 Evidence 访问控制；
- Replay、Feedback、Decision 和 Audit；
- 稳定 API、Capability 和版本契约。

### 9.2 应由 Video Summary 提供的能力

- 具体的 OpenCLIP/VLM/LLM Provider 组合；
- Caption 和 Enrichment 工作流；
- Embedding 生成和面向产品的检索策略；
- Daily / Weekly / Camera / Site Summary；
- 重点事件选择；
- Chat Prompt、Conversation 和问答体验；
- Summary/Search/Chat Web UI；
- Android/iOS 客户端；
- 上层产品配置；
- 可选的账号、订阅和商业服务。

### 9.3 需要谨慎判断的能力

Embedding 位于平台和应用之间：

- 基座宜定义通用对象引用、模型元数据、隐私和审计契约；
- Video Summary 可先拥有具体向量生成、索引和检索策略；
- 当第二个上层产品也需要通用向量检索时，再进一步下沉基础设施。

同理，基座可以支持通用 Model Provider，但不应因为 Video Summary 而直接引入 PyTorch、OpenCLIP 或特定云 LLM SDK。

## 10. 推荐迁移策略

采用渐进式“绞杀者迁移”：新旧系统短期并存，每完成一个垂直切片，就停用旧系统中的对应重复能力。

### 阶段 0：冻结重复基础设施扩展

- 不再扩展旧 MQTT Listener；
- 不再扩展旧 Event 表；
- 不再增强旧 Redis List 队列；
- 不再增加新的 Frigate 媒体代理逻辑；
- 旧系统继续作为可运行参考和行为基线。

### 阶段 1：定义 AI Enrichment 契约

在 Event Intelligence 中明确：

- `AIEnrichmentRequested` 或等价任务语义；
- Processor 身份与权限；
- Evidence 选择和读取方式；
- Caption/Tag Claim Schema；
- ModelInvocation 生命周期；
- 幂等键；
- Retry / DLQ；
- Replay 行为；
- 结果写回契约。

第一阶段使用确定性 Stub，不急于迁移真实模型。

### 阶段 2：完成第一个垂直切片

推荐的首个验收目标：

> 基座收到一个已结束的 ReviewItem 后，异步产生一条可审计的 Caption Claim，并能通过现有事件详情 API/UI 查看该 Claim。

该切片必须验证：

- 触发时机；
- ReviewItem 与 Observation 的处理边界；
- 代表性 Evidence 选择；
- Claim Schema；
- 模型版本记录；
- 重复消息幂等；
- 失败重试和 DLQ；
- Replay 是否重新调用模型；
- UI 对“来源事实”和“AI 解释”的区分。

### 阶段 3：迁移单事件 AI 理解

将旧 `vision.py` 和 `ai_worker` 中有价值的能力改造成 Video Summary Processor/Provider：

```text
ReviewItem
  → 选择 Evidence
  → Model Provider
  → Caption Claim
  → Tag Claims
  → EmbeddingRecord
```

完成后，旧 Video Summary 不再直接处理新 Frigate Event。

### 阶段 4：迁移语义搜索

- 建立正式 Embedding 数据模型；
- 记录 subject、modality、model、version、dimensions；
- 添加 pgvector Migration 和索引；
- Search API 不直接加载重模型；
- 建立过滤、分页和最小相关性阈值；
- 为模型升级和重新索引提供任务机制。

建议的数据方向：

```text
EmbeddingRecord
- subject_type
- subject_id
- modality
- vector
- model_id
- model_version
- dimensions
- source_claim_id
- created_at
```

### 阶段 5：迁移 Summary

Summary 改为读取：

```text
ReviewItem
+ Caption Claims
+ Decisions
+ Feedback
+ Camera / Site / Timezone
```

第一版基于 ReviewItem 去重和归并。后续再加入 Scenario、多摄像头、异常性、用户偏好和周/月摘要。

DailySummary 属于 Video Summary 应用模型，不应直接进入 Canonical 核心。

### 阶段 6：迁移 Chat

- Chat 只调用正式检索服务；
- 引用基座内部稳定 ID；
- 增加时间语义解析；
- Conversation 消息正规化存储；
- 建立 Prompt 和 ModelInvocation 版本；
- LLM 调用与 API 隔离；
- 加入 Token Budget、权限和审计。

### 阶段 7：迁移 Web 和 Android

- Web 增加 Summary、Search、Chat 产品页面；
- Android DTO 改为稳定 Video Summary API；
- 手机端不直接调用 Frigate；
- 手机端原则上也不直接组合调用多个基座内部接口；
- 增加 Capability Negotiation；
- 建立 Debug/Release 网络安全差异。

### 阶段 8：退役旧后端

当所有核心行为完成迁移和对照验收后：

- 停止旧 MQTT Listener；
- 停止旧 AI/Summary Queue；
- 停止旧 Event 数据写入；
- 导入或归档旧数据；
- 保留必要的迁移脚本、测试 Fixture 和历史文档；
- Android 和上层产品代码继续在 Video Summary 仓库演进。

## 11. 开源与发布建议

### 11.1 两个独立开源产品

推荐保持两个独立项目：

```text
nanexus-event-intelligence
nanexus-video-summary
```

它们分别拥有：

- 独立 README；
- 独立版本；
- 独立 Changelog；
- 独立 Issue；
- 独立 Release；
- 独立许可证决策；
- 明确兼容矩阵。

### 11.2 运行时禁止数据库级耦合

Video Summary 不应直接 Import 基座内部 SQLAlchemy Model，也不应直接写基座数据库。两个项目通过正式 API、事件流或 Processor Contract 协作。

否则即使物理上分成两个仓库，仍然会形成无法独立升级的分布式单体。

### 11.3 部署体验可以保持一体

代码分仓不代表安装复杂。Video Summary 可以提供一套 Compose：

```text
Event Intelligence
+ Video Summary API
+ AI Worker
+ Summary Worker
+ Web
```

未安装基座的用户可以一键启动兼容版本；已有基座的用户只部署 Video Summary 服务并配置连接地址。

### 11.4 建立兼容矩阵

示例：

| Video Summary | Event Intelligence |
|---|---|
| 0.1.x | >=0.2,<0.3 |
| 0.2.x | >=0.3,<0.5 |
| 1.x | >=1,<2 |

实际兼容还应通过 Capability Discovery 判断，而不是仅依赖版本号。

## 12. 改造优先级

### P0：迁移前必须解决

1. 定义基座 AI Enrichment / Processor Contract；
2. 使用可靠队列和幂等机制；
3. 分离 Observation、Claim、ModelInvocation 和 Embedding；
4. 使用基座 Evidence 安全访问；
5. 建立 Alembic Migration；
6. 建立最小自动化测试；
7. 重模型退出 API 进程。

### P1：形成可公开测试版本前解决

1. API Version 和 Capability；
2. 基座与 Video Summary 兼容矩阵；
3. Summary 基于 ReviewItem 去重；
4. 站点时区语义；
5. Processor 服务授权；
6. Python 依赖锁定；
7. 完整 Compose；
8. Android Release 禁止默认明文 HTTP。

### P2：产品成熟阶段解决

1. VLM 和多帧视频理解；
2. Scenario 聚合；
3. 时间语义 Chat；
4. 多用户、多站点；
5. 推送和远程访问；
6. Android/iOS 离线体验；
7. 周报、月报和用户偏好；
8. 模型评估集、质量指标和成本指标。

## 13. 后续设计问题清单

开始正式开发前，建议逐项形成 ADR 或任务验收标准：

1. AI Enrichment 在 Review started、updated 还是 ended 时触发？
2. 一个 Review 应选择一张还是多张 Evidence？
3. 模型没有足够证据时如何 abstain？
4. Replay 默认复用旧 Claim，还是允许显式重新推理？
5. Processor 写回 Claim 的权限和幂等键如何定义？
6. Embedding 存在基座还是 Video Summary 自己的数据库？
7. 模型升级后如何批量重建 Embedding？
8. Daily Summary 按 User、Site、Camera 还是统一生成？
9. 用户本地日期和 Site Timezone 如何确定？
10. 云端 VLM 能否读取某个 Camera 的 Evidence？
11. Community 和 Pro 分别包含哪些 Model Provider？
12. Conversation 数据属于自托管实例还是用户云账号？
13. Android 如何安全发现和配对自托管服务器？
14. Event Intelligence 不可用时 Video Summary 的降级行为是什么？
15. 如何衡量 Caption、Search、Summary 和 Chat 的质量？

## 14. 改造验收原则

后续每个迁移切片至少满足：

1. 不新增对旧 Event 表的依赖；
2. 不绕过基座直接访问 Frigate；
3. 不绕过基座 Evidence 安全边界；
4. 不在 API 进程加载重模型；
5. 任务具有幂等、重试和可观察状态；
6. AI 结果记录模型和版本；
7. AI 解释不覆盖来源事实；
8. 失败不会静默丢任务；
9. 新增数据库结构有 Migration；
10. 新行为有自动化测试；
11. API 变更有版本或兼容说明；
12. 旧能力只有在新链路完成对照验收后才退役。

## 15. 当前状态摘要

| 方面 | 判断 |
|---|---|
| 产品方向 | 清晰，具备价值 |
| 技术选型 | 基本合理 |
| 架构构想 | 比当前实现更成熟 |
| 后端实现 | 可演示，不宜直接生产化 |
| AI 理解 | 单图 Zero-shot / Embedding 为主 |
| Summary | 原型级事件汇总 |
| Chat | 初级 RAG 验证 |
| Android | 合格的轻量 MVP |
| 安全 | 仅适合可信开发局域网 |
| 可靠性 | 队列、去重和恢复存在较大缺陷 |
| 测试 | 明显不足 |
| 长期演进 | 应依赖 Event Intelligence 渐进重构 |

### 2026-08-21 migration update

The stage-4 OpenCLIP assessment items are now implemented through the public Event Intelligence boundary. OpenCLIP is worker-only, the API defaults to a non-model fallback, media input is job-scoped and validated, and authoritative Claims/Invocations retain Evidence and latency traceability. The legacy implementation remains frozen for rollback. Embedding storage and semantic Search are intentionally unchanged and remain stage 5 work.

## 16. 建议的第一个正式改造任务

在 Event Intelligence 基座中实现一个最小 AI Enrichment 垂直切片：

> 一个已结束的 ReviewItem 通过可靠 Pipeline 触发 Stub Model Provider，生成一条带 Evidence、模型版本和幂等键的 Caption Claim；失败可重试并进入 DLQ；结果可通过现有 API 和 UI 查看；Replay 默认不产生新的模型副作用。

在该任务完成之前，不建议优先迁移 OpenCLIP、Search、Summary 或 Chat。这个切片将决定后续所有高级功能是否拥有正确、稳定和可扩展的运行轨道。
