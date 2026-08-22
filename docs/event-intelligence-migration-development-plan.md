# Nanexus Video Summary 基座化改造开发计划

> 文档状态：待实施
> 制定日期：2026-08-21
> 主要依据：[技术评估与基座化改造参考](./technical-assessment-and-migration-reference.md)
> 上层项目：`nanexus_ai_video_summary`
> 目标基座：`nanexus_frigate_extension` / Nanexus Event Intelligence

## 1. 计划目的

本计划把技术评估中的结论转换为可以逐项实施、验证和停止的开发步骤。

计划的最终目标不是把两个仓库机械合并，而是形成两个可独立开源、独立发布、通过稳定契约协作的产品：

```text
Nanexus Event Intelligence
  通用事件智能基座
        ↑
        │ Versioned API / Processor Contract / Event Delivery
        │ Evidence / Claim / Model Invocation
        │
Nanexus Video Summary
  高级摘要、搜索和问答产品
```

迁移完成后：

- Event Intelligence 是事件、生命周期、Evidence 和可靠 Pipeline 的唯一基座；
- Video Summary 不再直接订阅 Frigate MQTT；
- Video Summary 不再维护第二份 Canonical Event；
- Video Summary 不再直接读取 Frigate 媒体地址；
- AI 解释以 Claim 和 ModelInvocation 表达，不覆盖来源事实；
- Summary、Search、Chat 和移动端继续属于 Video Summary；
- 两个项目可以分别构建、测试、版本化和开源；
- 用户仍可通过一套 Compose 获得完整产品体验。

## 2. 实施原则

### 2.1 单向依赖

只允许：

```text
Video Summary → Event Intelligence
```

禁止：

```text
Event Intelligence → Video Summary
```

基座不得 Import Video Summary 包，不得因为上层应用引入 PyTorch、OpenCLIP 或特定云 LLM SDK。

### 2.2 契约优先

跨仓库功能必须先定义契约，再实现 Provider 或 UI。禁止通过以下方式临时打通：

- 直接访问另一个项目的数据库；
- Import 另一个项目的内部 ORM Model；
- 共享未版本化的 Redis Key；
- 读取另一个项目的内部文件目录；
- 依赖未声明的内部 HTTP Endpoint；
- 在客户端拼接 Frigate 媒体 URL。

### 2.3 渐进迁移

旧系统在新链路完成验收前保持可运行。每迁移一项能力，再停用一项旧能力。不要一次性重写后切换。

### 2.4 一个阶段一个退出门槛

每个阶段必须：

1. 有明确输入和输出；
2. 有自动化测试；
3. 有故障或降级测试；
4. 有文档更新；
5. 有可回退开关；
6. 满足退出条件后才进入下一阶段。

### 2.5 来源事实和 AI 解释分离

- Observation 是来源事实；
- Evidence 是媒体或原始证据引用；
- Claim 是模型或规则作出的解释；
- ModelInvocation 是调用记录；
- Decision 是策略结果；
- Summary 是 Video Summary 的应用级聚合结果。

任何 AI 结果不得原位覆盖 Observation。

### 2.6 默认无外部副作用

- Replay 默认不重新调用收费模型；
- 云模型默认关闭；
- Evidence 默认不发送到云端；
- 通知和外部写回默认关闭；
- 开发阶段先使用 Stub Provider；
- 所有外部调用必须有显式配置、审计和预算边界。

## 3. 范围与非目标

### 3.1 本计划范围

- 基座 AI Processor/Enrichment 契约；
- ReviewItem 触发 AI 任务；
- Evidence 安全读取；
- Claim 和 ModelInvocation 写入；
- Stub/OpenCLIP Provider；
- Embedding 和语义搜索迁移；
- Summary 迁移；
- Chat 迁移；
- Web 和 Android API 迁移；
- Compose 和版本兼容；
- 旧重复后端退役；
- 开源准备和发布 Gate。

### 3.2 暂不作为首轮目标

- 完整连续视频理解；
- 实时流推理；
- 跨站点云平台；
- iOS 正式客户端；
- App Store / Google Play 发布；
- 复杂订阅计费；
- 自动报警警方等高风险动作；
- 大规模 Kubernetes 部署；
- 通用多租户 SaaS；
- 过早拆分 Android 独立仓库。

## 4. 仓库职责

### 4.1 Event Intelligence 仓库

负责：

- Canonical Observation、ReviewItem、Camera；
- Evidence 和安全媒体代理；
- Outbox、Redis Stream、Retry、DLQ；
- Processor 注册和权限；
- Claim、ClaimEvidence、ModelInvocation；
- AI Job 的通用投递契约；
- Replay、Audit 和 Feedback；
- Capability API；
- 基座 API 和 Schema 版本；
- 基座数据 Migration。

### 4.2 Video Summary 仓库

负责：

- Event Intelligence Client；
- Stub/OpenCLIP/VLM/LLM Provider 实现；
- AI Enrichment Worker；
- Embedding 生成和产品级检索；
- Summary 和重点事件选择；
- Conversation 和 Chat；
- Video Summary API；
- Web 产品页面；
- Android/iOS 客户端；
- Video Summary 数据 Migration；
- 完整产品 Compose 发行包。

### 4.3 变更归属判断

开发中遇到新需求时按以下顺序判断：

1. 是否与 Frigate 或其他来源协议有关？是则进入基座 Adapter。
2. 是否是任何上层 Processor 都需要的事件/Evidence/Claim 能力？是则进入基座。
3. 是否是通用模型调用生命周期或权限？是则进入基座契约。
4. 是否只服务摘要、搜索、Chat 或客户端体验？是则留在 Video Summary。
5. 如果暂时不能证明通用性，优先留在上层，避免污染基座。

## 5. 总体阶段

| 阶段 | 名称 | 核心结果 | 主要仓库 |
|---|---|---|---|
| 0 | 基线冻结与验收资产 | 保存旧系统行为基线 | Video Summary |
| 1 | 跨项目契约设计 | 冻结 Processor/Capability v1 | 两个仓库 |
| 2 | 基座 AI Enrichment 基础 | 可靠投递 Stub AI Job | Event Intelligence |
| 3 | 首个端到端垂直切片 | Review → Caption Claim → UI | 两个仓库 |
| 4 | OpenCLIP Provider 迁移 | 真实单图 Enrichment | Video Summary |
| 5 | Embedding 与语义搜索 | 新 Search 不在 API 加载模型 | 两个仓库 |
| 6 | Summary 迁移 | 基于 ReviewItem 的日摘要 | Video Summary |
| 7 | Chat 迁移 | 基于新检索与稳定引用的问答 | Video Summary |
| 8 | Web 与 Android 迁移 | 客户端完全使用新 API | Video Summary |
| 9 | 部署、安全和兼容 | 一键部署及版本协商 | 两个仓库 |
| 10 | 旧链路退役与数据处理 | 停止重复接入和重复存储 | Video Summary |
| 11 | 开源发布准备 | 两个项目独立发布可验证 | 两个仓库 |

阶段 0～3 是架构地基，不应跳过。阶段 4～8 应按顺序实施，但 UI 展示类工作可在契约稳定后适度并行。阶段 10 必须晚于所有对照验收。

## 6. 阶段 0：基线冻结与验收资产

### 6.1 目标

停止继续扩展旧基础设施，同时把旧系统已经实现的产品行为转成可重复验收的基线。

### 6.2 任务

#### BASELINE-001：冻结旧基础设施范围

在文档中声明以下模块进入维护模式：

- `services/mqtt_listener`；
- 旧 `Event` 表；
- `src/nanexus/queue.py` Redis List/Set；
- 旧媒体读取和重定向；
- API 进程内 OpenCLIP 加载。

只允许修复阻塞迁移或数据导出的严重问题，不再增加新功能。

#### BASELINE-002：建立后端最小测试框架

创建 pytest 基线，至少覆盖：

- Frigate Payload 解析；
- Rule Summary 输出；
- Search keyword fallback；
- Chat extractive fallback；
- API Schema 序列化；
- 当前配置加载。

这些测试的目的不是把旧实现生产化，而是固定需要保留的上层行为。

#### BASELINE-003：建立 Android 基线

至少增加：

- API DTO 反序列化测试；
- Repository URL 组合测试；
- Summary/Timeline/Search ViewModel 状态测试；
- Debug APK 构建检查。

#### BASELINE-004：创建脱敏迁移 Fixture

从现有 Seed 或基座 Fixture 中建立一套不含私人媒体和凭据的固定数据，覆盖：

- Person Review；
- Vehicle Review；
- Review 与多个 Object；
- 有 Snapshot；
- Evidence 不可用；
- 重复/更新事件；
- 跨 UTC 日期边界；
- Toronto 本地日期边界。

#### BASELINE-005：记录行为基线

保存以下输出作为对照：

- Timeline 返回结构；
- 一组 Search 查询及 Top-K；
- 一天的 Rule Summary；
- 一组 Extractive Chat 答案；
- Android 主要页面截图或 UI 验收记录。

### 6.3 产物

- 旧系统冻结说明；
- pytest 和 Android test 基线；
- 脱敏 Fixture；
- 行为对照记录；
- 已知差异清单。

### 6.4 退出条件

- 旧系统可在固定 Fixture 上重复运行；
- 核心上层行为有自动测试或明确快照；
- 测试不依赖真实摄像头、私人媒体或云 Key；
- 迁移过程中可以判断新旧结果的差异；
- 没有对旧队列和旧 Event 模型新增功能。

### 6.5 回退方式

本阶段不改变运行链路，不需要运行时回退。

### 6.6 实施状态（2026-08-21）

BASELINE-001～005 已完成。验收证据见 [`baseline-acceptance.md`](./baseline-acceptance.md)，逐任务开发记录见 [`development-progress.md`](./development-progress.md)。本记录不表示 CONTRACT-001 已开始。

## 7. 阶段 1：跨项目契约设计

### 7.1 目标

在写 AI Worker 前，明确两个项目之间唯一允许的集成方式。

### 7.2 关键设计决策

必须形成 ADR 或版本化规范，至少回答：

1. AI 任务在 Review `ended` 时触发，还是允许 `updated`？
2. Job 的 Subject 是 ReviewItem、Observation 还是通用 Canonical Entity？
3. 一个 Job 如何引用 Evidence？
4. Processor 如何取得短期授权的媒体内容？
5. Claim 如何写回？
6. ModelInvocation 由基座创建还是 Processor 提交？
7. Job 和结果的幂等键如何计算？
8. Provider 超时、失败、abstain 如何表达？
9. Replay 默认是否重新推理？
10. 基座和 Video Summary 如何协商版本与 Capability？

### 7.3 推荐的 v1 决策

- 首轮只处理 lifecycle=`ended` 的 ReviewItem；
- 一个 Review 默认选择一张代表性 Snapshot；
- Evidence 只能通过基座受控 API 读取；
- Processor 不接收 Frigate 原始 URL 和凭据；
- Job 使用稳定 `job_id` 和 `idempotency_key`；
- Caption 和 Tags 分别作为结构化 Claim；
- 每次处理必须关联一个 ModelInvocation；
- Evidence 不可用时允许明确 abstain；
- Replay 默认复用已有结果，不触发真实模型；
- 显式 `reprocess` 才产生新的 Invocation；
- v1 先支持内部可信网络服务身份，接口保留正式认证扩展点。

### 7.4 任务

#### CONTRACT-001：Processor Contract v1

> 实施状态（2026-08-21）：已完成；架构 Gate 已批准。未开始 CONTRACT-002。

定义 Job Envelope：

```text
job_id
contract_version
processor_type
subject_type
subject_id
subject_revision
evidence_refs
requested_outputs
privacy_policy
idempotency_key
requested_at
trace_id
```

#### CONTRACT-002：Enrichment Result v1

> 实施状态（2026-08-21）：已完成并冻结；状态不变量、ModelInvocation 事实边界与禁止思维链规则见双仓验收和基座 ADR-012。

定义结果：

```text
job_id
idempotency_key
status: succeeded | abstained | failed
model_invocation
claims[]
errors[]
completed_at
```

禁止提交 Chain-of-Thought。只允许结构化输出、简短原因和可审计元数据。

#### CONTRACT-003：Capability v1

> 实施状态（2026-08-21）：已完成并冻结；版本协商、支持面和媒体限制已形成规范 Schema。

基座 Capability 至少声明：

- Platform/API Version；
- Canonical Schema Version；
- Processor Contract Version；
- 支持的 Subject；
- 支持的 Evidence 类型；
- 是否支持 Claim 写回；
- 是否支持 ModelInvocation；
- 是否支持 Replay/Dry Run；
- 最大媒体大小和允许 Content-Type。

#### CONTRACT-004：权限与隐私规则

> 实施状态（2026-08-21）：已完成并冻结；采用按 Job/Subject/Evidence 对象授权、默认拒绝及 `local_only` 外网禁用。

定义 Processor 所需最小权限：

- 读取指定 Job Subject；
- 读取 Job 中列出的 Evidence；
- 提交指定 Job 的 Enrichment Result；
- 不允许任意遍历其他事件；
- 不允许直接写 Observation；
- 不允许取得 Frigate Credential。

#### CONTRACT-005：兼容性测试样例

> 实施状态（2026-08-21）：已完成；两个仓库使用独立模型验证同一脱敏 Fixture，并覆盖失败和降级规则。

为 Job、Result、Capability 建立 JSON Schema/Pydantic Model 和固定 Fixture。两个仓库分别运行 Contract Test。

### 7.5 产物

- Processor Contract ADR；
- Job/Result/Capability Schema；
- 权限模型说明；
- Replay 语义；
- 版本兼容规则；
- 两个仓库共享的脱敏 Contract Fixture。

### 7.6 退出条件

- 契约经过人工评审；
- 两个仓库均能独立验证 Fixture；
- Contract 包不依赖任一仓库的内部 ORM；
- 重大字段语义无未决项；
- v1 明确兼容和破坏性变更规则。

### 7.7 实施状态（2026-08-21）

阶段 1 已达到退出条件并冻结。验收证据见 [`architecture-reviews/2026-08-21-contract-002-005-gate.md`](./architecture-reviews/2026-08-21-contract-002-005-gate.md)；本状态不表示阶段 2 已开始。

## 8. 阶段 2：基座 AI Enrichment 基础

### 8.1 目标

让 Event Intelligence 能可靠地产生、投递和记录通用 AI Enrichment 任务，但暂不运行真实模型。

### 8.2 任务

#### FOUNDATION-001：基座数据库 Migration

核对并补齐：

- ModelInvocation 状态和错误字段；
- Claim 与 Evidence 关联；
- Processor Job/Attempt；
- 幂等唯一约束；
- Job 状态索引；
- 必要的 AuditRecord。

所有结构通过 Alembic，不使用 `create_all()` 代替 Migration。

#### FOUNDATION-002：ReviewEnded 触发器

在基座可靠 Pipeline 中，当 Review 首次进入 ended 状态时产生 `AIEnrichmentRequested`。

要求：

- 相同 Review Revision 重复到达只产生一个逻辑 Job；
- 更新 Revision 的行为有明确规则；
- 没有可用 Evidence 时仍产生可审计结果或明确跳过；
- 事务提交和 Outbox 写入保持原子性。

#### FOUNDATION-003：独立 Consumer Group

AI Enrichment 使用独立 Redis Stream Consumer Group，不能阻塞现有 Rule、Decision 和 Notification 快路径。

#### FOUNDATION-004：Retry 和 DLQ

定义：

- 可重试错误；
- 不可重试错误；
- 最大尝试次数；
- 退避策略；
- DLQ 记录；
- 人工 requeue；
- 停机恢复。

#### FOUNDATION-005：Stub Processor

实现确定性 Stub：

```text
person observed at front_yard
```

Stub 不读取真实模型，不访问云端，输出固定版本和确定性结果。

#### FOUNDATION-006：Claim/API/UI 展示

事件详情 API 返回关联 Claim 和 ModelInvocation 摘要。UI 清楚区分：

- 来源事实；
- AI 解释；
- 模型和版本；
- 处理状态；
- Evidence；
- 失败或 abstain。

### 8.3 故障测试

必须覆盖：

- Outbox 发布前进程退出；
- Redis 暂时不可用；
- Worker 在取到任务后退出；
- 结果提交超时；
- 同一消息重复投递；
- Poison Message；
- Evidence 不存在；
- DLQ requeue。

### 8.4 退出条件

- Review ended 到 Stub Claim 完成端到端闭环；
- Kill/restart 不丢 Job；
- 重复消息不重复创建最终 Claim；
- 失败最终进入 DLQ；
- 现有 Rule/Notification 快路径不被 AI 阻塞；
- API/UI 可审计查看；
- Replay 默认不触发真实外部副作用。

### 8.5 实施状态（2026-08-21）

FOUNDATION-001～006 已在 Event Intelligence 仓库完成，并通过 Video Summary 侧的只读跨仓复核。基座验收记录为 `docs/architecture/foundation-001-006-acceptance.md`；本仓复核记录见 [`architecture-reviews/2026-08-21-foundation-001-006-gate.md`](./architecture-reviews/2026-08-21-foundation-001-006-gate.md)。

阶段 2 已达到退出条件。本状态不授权、也不表示阶段 3 已开始；Video Summary 运行时代码、旧链路和数据模型在本阶段均未切换。

## 9. 阶段 3：首个跨仓库垂直切片

### 9.1 目标

验证 Video Summary 能作为独立上层产品，通过正式契约消费基座 Job 并提交结果。

### 9.2 任务

#### SLICE-001：Event Intelligence Client

在 Video Summary 中建立独立 Client 层，只依赖公开契约：

- Capability；
- Job 获取/消费；
- Subject Metadata；
- Evidence Content；
- Result Submit；
- Health。

Client 必须具有：

- Timeout；
- Retry 分类；
- Trace ID；
- 结构化错误；
- 版本检查；
- 日志脱敏。

#### SLICE-002：Video Summary Stub Worker

把 Stub Processor 移至或复现在 Video Summary Worker 中，验证真正的跨项目边界。

#### SLICE-003：服务身份

配置 Video Summary Processor 身份，只授予当前 Job 的 Evidence 读取和 Result Submit 权限。

#### SLICE-004：Compose 集成 Demo

建立集成 Compose 或 Overlay：

```text
Fixture
→ Event Intelligence
→ Reliable Pipeline
→ Video Summary Stub Worker
→ Caption Claim
→ Event Intelligence API/UI
```

#### SLICE-005：Contract Integration Test

两个仓库的 CI 至少各自完成：

- Schema Fixture Test；
- 不兼容版本拒绝；
- 缺少 Capability 降级；
- 重复 Result 幂等；
- Evidence 权限失败。

### 9.3 退出条件

- 两个仓库不共享数据库；
- Video Summary 不 Import 基座内部包；
- Video Summary 不直接访问 Frigate；
- 独立构建的两个服务可以完成闭环；
- 基座停机或版本不兼容时有明确错误；
- 关闭 Video Summary 不影响基座事件和规则链路。

### 9.3.1 实施状态（2026-08-21）

SLICE-001～005 已完成代码与隔离集成验收；证据见 [验收记录](./architecture-reviews/2026-08-21-slice-001-005-gate.md)。本状态不授权阶段 4；真实 Docker Compose smoke run 是进入阶段 4 的前置条件。

### 9.4 首个实施里程碑

阶段 0～3 完成后，形成第一个可发布的内部里程碑：

> `ReviewItem ended → reliable job → Video Summary Stub Processor → audited Caption Claim → API/UI`

在该里程碑通过之前，不进入 OpenCLIP、Search、Summary 或 Chat 的正式迁移。

## 10. 阶段 4：OpenCLIP Provider 迁移

### 10.1 目标

把旧项目中可复用的 OpenCLIP 能力迁移成独立 Provider，同时保留 Stub 和安全降级。

### 10.2 任务

#### MODEL-001：Provider Interface

定义 Video Summary 内部 Provider 接口：

- `analyze_image`；
- `embed_image`；
- `embed_text`；
- Health/Readiness；
- Model Identity；
- Resource Requirements；
- Timeout/Cancellation；
- Structured Result；
- Abstain。

#### MODEL-002：OpenCLIP Provider

迁移：

- 模型加载；
- Device 选择；
- 图像 Embedding；
- 文本 Embedding；
- Zero-shot 标签。

明确标注它是 Zero-shot Enrichment，不宣称为完整 Caption/VLM。

#### MODEL-003：模型进程隔离

保证 FastAPI 不加载 PyTorch/OpenCLIP。模型只存在于 Worker 或独立 Model Service。

#### MODEL-004：媒体输入校验

- 只从基座 Evidence API 获取；
- 限制大小和 Content-Type；
- Pillow 解码失败可审计；
- 不接受任意 URL 或 `file://`；
- 不接触 Frigate Token。

#### MODEL-005：模型元数据和评估

记录：

- Provider；
- Model；
- Pretrained Variant；
- Device；
- Input Evidence；
- Latency；
- Result Hash；
- Error；
- Prompt/Label Set Version。

#### MODEL-006：CPU 基线

在无 GPU 环境完成固定 Fixture 验收，并记录：

- 启动时间；
- 单图延迟；
- 内存；
- 输出稳定性。

### 10.3 退出条件

- Stub/OpenCLIP 可配置切换；
- API 进程不加载模型；
- 模型失败不丢 Job；
- 每个 Claim 可追溯到 Invocation 和 Evidence；
- 固定 Fixture 有质量基线；
- CPU 环境可运行；
- 云端 Provider 仍默认关闭。

## 11. 阶段 5：Embedding 与语义搜索迁移

### 11.1 目标

建立可版本化、可重建、不依赖旧 Event 表的语义检索。

### 11.2 前置决策

在本阶段开始前决定 Embedding 存储位置：

- 推荐首版由 Video Summary 拥有应用级 pgvector 表；
- 基座只提供 Subject、Evidence、Claim 和权限契约；
- 不直接修改基座 Observation 表增加 vector 列；
- 当第二个上层产品需要通用向量能力时，再评估下沉。

### 11.3 任务

#### SEARCH-001：Embedding 数据模型

至少包含：

```text
id
subject_type
subject_id
subject_revision
modality
vector
dimensions
provider
model
model_version
source_claim_id
content_hash
created_at
superseded_at
```

#### SEARCH-002：Alembic 和 pgvector

- 正式 Migration；
- 维度约束；
- 向量索引；
- 元数据过滤索引；
- Upgrade 检查；
- 模型维度变化策略。

#### SEARCH-003：异步索引任务

Caption Claim 完成后异步产生 Embedding Job。索引失败不得影响 Claim 持久化。

#### SEARCH-004：Query Embedding Service

Search API 不加载模型。查询文本 Embedding 通过已启动的 Model Service 或轻量 RPC 获得。

#### SEARCH-005：Search API v1

支持：

- Query；
- Camera/Site；
- Label；
- Since/Until；
- Subject Type；
- Pagination；
- 最小相似度；
- Method/Model 元数据。

结果返回稳定 Subject ID、相关 Claim 和可打开 Evidence，不返回旧自增 Event ID 作为长期引用。

#### SEARCH-006：重建与模型升级

提供：

- Reindex 指令；
- Dry Run；
- 进度；
- 模型版本并存；
- 新索引完成后切换；
- 旧索引清理策略。

#### SEARCH-007：检索评估集

固定至少一组中英文查询：

- 红衣服的人；
- 黑色车辆；
- 前院包裹；
- 昨天车道上的人；
- 不存在的目标。

记录 Top-K、人工相关性和模型版本。

### 11.4 退出条件

- 新 Search 完全不读取旧 Event 表；
- API 进程不加载 OpenCLIP；
- 模型升级可重建而不覆盖旧结果；
- 时间和 Camera 过滤正确；
- 中英文固定评估可重复；
- 没有 Embedding 时有明确降级或空结果语义；
- 搜索结果能回到基座 Evidence。

## 12. 阶段 6：Summary 迁移

### 12.1 目标

把摘要从“底层 Event 罗列”升级为基于 ReviewItem、Claim、Decision 和本地日期的产品能力。

### 12.2 任务

#### SUMMARY-001：Summary 应用模型

Video Summary 自己管理：

```text
Summary
- id
- summary_type
- local_date
- timezone
- site_id
- camera_id?
- content
- structured_content
- source_subject_ids
- generator
- model_version
- prompt_version
- status
- created_at
- superseded_at
```

#### SUMMARY-002：本地日期范围

实现：

```text
Site/Camera Timezone
→ Local Day 00:00–24:00
→ UTC Query Bounds
```

增加 DST、Toronto 和 UTC 边界测试。

#### SUMMARY-003：Review 聚合

- 一个 Review 只计一次；
- 关联 Object 不重复计数；
- 优先使用 ended Review；
- Evidence/Claim 缺失时可降级；
- 记录所有来源 Subject ID。

#### SUMMARY-004：重点事件选择

第一版使用可解释规则：

- Decision Outcome；
- Feedback；
- Label；
- Zone；
- Duration；
- 时间；
- 是否有高质量 Claim；
- 重复事件压缩。

重点排序必须可测试，不先依赖不透明 LLM 判断。

#### SUMMARY-005：Rule Summary v1

生成确定性结构化摘要，作为任何 LLM 模式的基线和降级路径。

#### SUMMARY-006：LLM Summary v1

- 只消费结构化 Review/Claim Context；
- 不直接读取媒体；
- 记录 Prompt Version 和 Invocation；
- 有 Token/Cost 上限；
- 失败降级到 Rule Summary；
- 不在 API 请求路径同步生成。

#### SUMMARY-007：调度与手动重建

- 独立 Worker；
- 按 Site Timezone 调度；
- 幂等；
- 支持指定日期重建；
- 旧版本不被静默覆盖；
- 可观察任务状态。

#### SUMMARY-008：新旧对照

对固定 Fixture 比较：

- 重复事件数量；
- 事件覆盖；
- 时间边界；
- 重点事件；
- 输出稳定性。

### 12.3 退出条件

- Summary 不读取旧 Event 表；
- 基于 ReviewItem 去重；
- Site Timezone 正确；
- Rule 模式可完全离线运行；
- LLM 失败安全降级；
- API 只读预计算结果；
- 每份 Summary 可追溯到 Subject、Claim 和生成版本。

## 13. 阶段 7：Chat 迁移

### 13.1 目标

构建基于新 Search/Summary 的可审计问答，不依赖旧 Event 和同步重模型路径。

### 13.2 任务

#### CHAT-001：Conversation 正规化

将单个 JSON 消息数组改为 Conversation + Message，支持：

- User/Assistant/System Role；
- Created At；
- Method；
- Related Subject IDs；
- Prompt/Model Version；
- Token/Cost；
- 错误和降级；
- 所有权。

#### CHAT-002：时间语义解析

支持最小集合：

- 今天；
- 昨天；
- 最近 N 天；
- 明确日期；
- 上午/下午/时间范围；
- Site Timezone。

解析结果必须结构化并可测试。

#### CHAT-003：Retrieval Pipeline

```text
Question
→ Time/Camera Filter
→ Semantic Search
→ Summary Retrieval
→ Context Budget
→ Answer
```

#### CHAT-004：引用

回答引用稳定 Subject ID，客户端可以打开对应 Review 和 Evidence。不得继续以旧数据库自增 Event ID 作为长期外部引用。

#### CHAT-005：LLM Worker/Service

LLM 调用退出 API 请求进程的重任务路径。可采用异步 Job + Poll/SSE，或受控的独立 Model Gateway。具体选择形成 ADR。

#### CHAT-006：安全和 Prompt Injection

- Evidence/Claim 内容视为不可信数据；
- 不执行 Context 中的指令；
- 不泄露系统 Prompt、Token 或内部 URL；
- 限制输出和上下文；
- 记录可审计引用，不保存 Chain-of-Thought。

#### CHAT-007：降级模式

LLM 不可用时返回结构化 Extractive Answer，而不是无解释地失败。

### 13.3 退出条件

- Chat 不读取旧 Event 表；
- 时间查询在 Site Timezone 下正确；
- 回答具有稳定可打开引用；
- Conversation 有所有权边界；
- LLM 不可用时可降级；
- Prompt/Model/检索方法可审计；
- 固定问题集有回归测试。

## 14. 阶段 8：Web 与 Android 迁移

### 14.1 目标

让用户端完全使用新的 Video Summary API，同时保持基座和上层产品的界面边界。

### 14.2 Web 任务

#### CLIENT-WEB-001：导航和产品页面

增加或完善：

- Summary；
- Search；
- Chat；
- Related Event Detail；
- Processor/Model 状态；
- Settings。

#### CLIENT-WEB-002：统一事件链接

Summary/Search/Chat 都使用稳定 Subject Link 打开基座事件详情，不复制事件详情业务逻辑。

#### CLIENT-WEB-003：加载和错误状态

明确区分：

- 基座离线；
- Video Summary Worker 离线；
- 模型未配置；
- Evidence 过期；
- Job 处理中；
- 功能不受当前 Capability 支持。

### 14.3 Android 任务

#### CLIENT-ANDROID-001：API v1 DTO

新增版本化 DTO，不直接复用旧 EventOut 语义。为 JSON Fixture 建立兼容测试。

#### CLIENT-ANDROID-002：Capability Negotiation

App 连接服务器时先读取 Capability，根据支持情况显示或隐藏功能。

#### CLIENT-ANDROID-003：认证和安全存储接口

即使首版仍运行在可信局域网，也先建立 Token Provider 和安全存储边界，避免认证逻辑散落到 Retrofit 调用。

#### CLIENT-ANDROID-004：网络安全 Build Variant

- Debug 可配置 LAN HTTP；
- Release 默认禁止 Cleartext；
- 不在日志输出 Token、完整查询或敏感 URL；
- Release 关闭不必要的网络日志。

#### CLIENT-ANDROID-005：页面迁移

按顺序迁移：

1. Settings/Health；
2. Timeline Link；
3. Summary；
4. Search；
5. Event Detail Link；
6. Chat。

#### CLIENT-ANDROID-006：状态与缓存

至少增加：

- 分页；
- Retry；
- Loading/Empty/Error；
- 配置变化刷新；
- 基础本地缓存策略；
- 进程恢复。

### 14.4 退出条件

- Web/Android 不直接调用 Frigate；
- 不读取旧 Video Summary Event API；
- Capability 不支持时安全降级；
- Release Android 默认不允许明文 HTTP；
- DTO Fixture Test 通过；
- Summary/Search/Chat 能打开对应基座事件；
- 主要页面具有自动测试或明确 UI 验收。

## 15. 阶段 9：部署、安全和兼容

### 15.1 目标

形成两个独立项目、一套完整部署体验，并让升级和故障行为可预测。

### 15.2 任务

#### RELEASE-001：依赖锁定

- Python 版本与基座协调，优先统一到 Python 3.12；
- 使用 `uv.lock` 或等价方案；
- OpenCLIP/CUDA 作为 Optional Profile；
- 固定 Node/Android 构建版本；
- 记录模型权重来源和许可证。

#### RELEASE-002：完整 Compose

提供：

- Event Intelligence；
- Video Summary API；
- Video Summary Worker；
- Summary/Chat Worker；
- Web；
- PostgreSQL/pgvector；
- Redis；
- Migration Job；
- Health Check。

支持两种模式：

1. 一体安装；
2. 连接已有 Event Intelligence。

#### RELEASE-003：配置和 Secret

- `.env.example` 完整；
- Secret 不进入日志；
- 云 Key 使用文件或 Secret 注入；
- 默认只绑定可信地址；
- 明确公网部署前置条件。

#### RELEASE-004：兼容矩阵

维护 Video Summary 与 Event Intelligence 的版本范围，并在启动时检查 Capability。

#### RELEASE-005：Observability

至少记录：

- Job backlog；
- Processing latency；
- Retry/DLQ；
- Model latency；
- Model error；
- Token/Cost；
- Search latency；
- Summary freshness；
- 基座连接状态。

#### RELEASE-006：资源 Profile

定义：

- Stub；
- CPU OpenCLIP；
- GPU OpenCLIP；
- Optional Cloud LLM。

每种 Profile 提供明确最低资源、启动方式和降级行为。

### 15.3 退出条件

- 干净环境一条命令启动；
- Migration 自动且可验证；
- 不兼容版本在启动阶段明确拒绝；
- Secret/Token 不进入日志或浏览器；
- CPU Profile 可用；
- Worker 故障不影响基座核心事件链路；
- 运维人员可观察 backlog、错误和 DLQ。

## 16. 阶段 10：旧链路退役与数据处理

### 16.1 目标

只有在新链路完成对照验收后，才停止重复基础设施和旧数据写入。

### 16.2 退役顺序

#### RETIRE-001：停止旧 MQTT Listener

前提：所有新事件已由 Event Intelligence 接收，并连续观察无缺口。

#### RETIRE-002：停止旧 AI Queue/Worker

前提：新 Processor 已处理真实 Review，Retry/DLQ 和 Reprocess 均验证。

#### RETIRE-003：停止旧 Summary Worker

前提：新 Summary 连续生成并通过本地日期、去重和内容对照。

#### RETIRE-004：停止旧 Search/Chat Path

前提：Web/Android 已切到新 API，固定查询集通过。

#### RETIRE-005：旧数据库处理

对旧数据选择并记录：

- 导入；
- 只读归档；
- 保留有限时间；
- 删除。

不得在没有备份、记录和用户确认的情况下删除旧数据。

#### RETIRE-006：代码归档

旧模块可以：

- 移至 `legacy/`；
- 打 Tag 后删除；
- 保留迁移脚本和 Fixture；
- 在 README 标明不再运行。

具体删除应单独授权，不在普通迁移任务中隐式执行。

### 16.3 双读/影子验证

在切换前运行一段影子期：

- 旧系统继续产出但不对用户作为主结果；
- 新系统作为候选结果；
- 比较事件覆盖、Caption、Search、Summary；
- 记录差异；
- 不重复发送通知或产生收费副作用。

### 16.4 退出条件

- 新系统连续运行达到约定观察期；
- 没有不可解释的事件缺口；
- 固定验收集通过；
- Android/Web 已不依赖旧 API；
- 旧数据已明确归档或迁移；
- 回退说明已演练；
- 退役操作有独立记录。

## 17. 阶段 11：独立开源发布准备

### 17.1 目标

让 Event Intelligence 和 Video Summary 都能作为独立开源项目构建和发布，同时保持组合部署体验。

### 17.2 任务

#### OSS-001：许可证和第三方依赖审计

- Python/npm/Gradle 依赖；
- 模型代码和权重许可证；
- OpenCLIP Pretrained 权重来源；
- 图标、截图和文档资产；
- Frigate 名称与商标表述。

#### OSS-002：隐私与 Secret 审计

- 私网 IP；
- Token/API Key；
- 真实 Camera 名称；
- 人物和车辆图像；
- 本地文件路径；
- 日志和 Replay Bundle。

#### OSS-003：独立构建验证

在干净环境中分别验证：

- Event Intelligence 独立运行；
- Video Summary 在没有内部源码路径时构建；
- Video Summary 连接公开契约版本的基座；
- 一体 Compose Demo；
- Stub Profile 不需要真实模型或云 Key。

#### OSS-004：文档

Video Summary 至少提供：

- 产品定位；
- 与 Event Intelligence 的关系；
- 架构图；
- 快速开始；
- Capability/兼容矩阵；
- 模型和硬件说明；
- 隐私说明；
- Android 开发说明；
- 升级和故障排查；
- 安全边界。

#### OSS-005：Release Gate

- 测试通过；
- Lint/Type Check；
- Migration Check；
- Compose Config；
- Secret Scan；
- License/SBOM；
- 干净安装；
- 版本映射；
- 人工发布授权。

### 17.3 退出条件

- 两个仓库可以独立构建；
- Video Summary 不依赖基座内部源码；
- 公开 Fixture 不含私人数据；
- 许可证和模型权重边界明确；
- Community Demo 可重复；
- 未经明确授权不创建外部仓库、Tag、Release 或公开镜像。

## 18. 测试策略

### 18.1 测试层级

| 层级 | 重点 |
|---|---|
| Unit | Schema、时间范围、排序、Prompt 构建、状态机 |
| Contract | Job、Result、Capability、版本兼容 |
| Repository | Migration、唯一约束、幂等、查询 |
| Pipeline | Outbox、Stream、ACK、Retry、DLQ、重启 |
| Integration | Review → Evidence → Claim → Search/Summary |
| API | 权限、分页、错误、Schema |
| Model | 固定 Fixture、输出结构、性能基线 |
| Web | 页面状态、链接、降级 |
| Android | DTO、Repository、ViewModel、Build Variant |
| End-to-end | Compose 一键闭环、故障恢复 |

### 18.2 必测故障

- PostgreSQL 暂时不可用；
- Redis 暂时不可用；
- Event Intelligence 重启；
- Video Summary Worker 重启；
- Worker 处理一半被 Kill；
- Evidence 404/过期；
- Evidence 类型错误或超大；
- 模型加载失败；
- 模型超时/OOM；
- LLM 429/5xx；
- 重复 Job；
- 重复 Result；
- 不兼容 Contract Version；
- Site Timezone/DST 边界；
- Android 连接旧服务器。

### 18.3 测试数据规则

- 默认使用合成或明确脱敏 Fixture；
- 真实媒体不得进入 Git；
- 云模型测试默认关闭；
- 需要云测试时使用显式 Marker/Profile；
- 性能结果记录硬件和模型版本；
- AI 质量不能只用模型 Confidence 自证。

## 19. 数据迁移策略

### 19.1 首选原则

首轮迁移不要求把旧 `Event` 表完整转换成 Canonical 历史。优先保证新事件全部走新链路。

### 19.2 可选方案

#### 方案 A：只迁移新数据

- 最简单；
- 旧数据库只读保留；
- 新系统从切换日期开始工作。

#### 方案 B：导入旧事件引用

- 将旧 Frigate ID 映射到基座 SourceEntity；
- 不伪造不存在的 Review 生命周期；
- 旧 Caption 作为 Legacy Claim；
- 标明来源模型未知或旧版本；
- Embedding 建议重新生成。

#### 方案 C：完整历史重处理

- 仅在 Evidence 仍可访问时执行；
- 使用 Replay/Reprocess；
- 控制模型成本；
- 不产生通知等外部副作用。

### 19.3 推荐选择

第一轮采用方案 A，并保留未来方案 B 的导入脚本设计。不要让历史数据迁移阻塞新架构上线。

## 20. 可观测性和质量指标

### 20.1 可靠性

- Review ended 到 Job 创建成功率；
- Job 完成率；
- Retry 次数；
- DLQ 数量；
- 重复 Result 被幂等拒绝数量；
- 不可解释事件缺口。

### 20.2 性能

- Review ended 到 Caption P50/P95；
- Evidence 下载延迟；
- 模型推理延迟；
- Search P50/P95；
- Summary 生成时长；
- Worker backlog。

### 20.3 AI 质量

- Caption 人工可接受率；
- Search Precision@K；
- Summary 重点事件覆盖率；
- 重复事件压缩率；
- Chat 引用正确率；
- Abstain 合理率。

### 20.4 成本和资源

- CPU/GPU 利用率；
- 模型内存/显存；
- 单事件云调用次数；
- Token/费用；
- 每日摘要成本；
- Embedding 存储增长。

指标基线先记录，不在没有真实评估数据时宣称质量提升百分比。

## 21. 实施顺序和依赖

```text
BASELINE
   ↓
CONTRACT
   ↓
FOUNDATION
   ↓
FIRST VERTICAL SLICE
   ↓
OPENCLIP
   ↓
EMBEDDING / SEARCH
   ↓
SUMMARY
   ↓
CHAT
   ↓
WEB / ANDROID
   ↓
DEPLOYMENT / SECURITY
   ↓
SHADOW VALIDATION
   ↓
LEGACY RETIREMENT
   ↓
OPEN-SOURCE RELEASE GATE
```

关键依赖：

- Contract 未冻结，不实现真实 Provider；
- Claim/Invocation 未完成，不迁移 OpenCLIP；
- Embedding/Search 未完成，不迁移 Chat；
- Review 聚合和时区未完成，不切换 Summary；
- 客户端未切换，不退役旧 API；
- 影子期未通过，不删除旧数据或代码。

## 22. 推荐实施批次

为了便于逐步执行，建议按以下批次创建任务。

### 批次 A：准备与契约

1. BASELINE-001～005；
2. CONTRACT-001～005；
3. 人工架构评审。

### 批次 B：可靠 AI 地基

1. FOUNDATION-001～006；
2. 故障注入测试；
3. 基座 UI Claim 展示。

### 批次 C：跨仓库闭环

1. SLICE-001～005；
2. Compose Stub Demo；
3. 第一里程碑验收。

### 批次 D：真实 AI 与检索

1. MODEL-001～006；
2. SEARCH-001～007；
3. 固定质量评估集。

### 批次 E：上层产品能力

1. SUMMARY-001～008；
2. CHAT-001～007；
3. 新旧行为对照。

### 批次 F：客户端与发行

1. CLIENT-WEB；
2. CLIENT-ANDROID；
3. RELEASE-001～006。

### 批次 G：切换与开源

1. 影子验证；
2. RETIRE-001～006；
3. OSS-001～005；
4. 独立发布授权。

## 23. 每个任务的完成定义

任何任务只有同时满足以下条件才可标记完成：

1. 代码和 Schema 已实现；
2. 正常路径自动测试通过；
3. 相关故障路径测试通过；
4. Migration/配置/文档同步更新；
5. 没有引入反向仓库依赖；
6. 没有绕过 Evidence 和权限边界；
7. `git diff --check`、Lint、Type Check 通过；
8. 与任务相关的 Compose/Integration Test 通过；
9. 进度日志记录产物、验证结果、遗留和下一步；
10. 未经授权不执行数据删除、外部发布或生产切换。

## 24. 开发进度记录模板

建议每完成一个任务，在对应仓库维护进度日志：

```markdown
## YYYY-MM-DD：TASK-ID 任务名称

### 目标

### 已完成

### 数据和契约变更

### 验证结果

### 故障测试

### 兼容性影响

### 已知限制

### 回退方式

### 下一步
```

跨仓库任务需要分别记录两个仓库的 Commit/版本映射，但不要让一个仓库依赖另一个仓库未提交的工作树状态。

## 25. 风险登记

| 风险 | 影响 | 控制措施 |
|---|---|---|
| Contract 过早绑定 Video Summary | 基座失去通用性 | 只下沉被证明通用的能力 |
| 两仓库直接共享数据库 | 无法独立升级 | 强制 API/事件契约 |
| AI 慢任务阻塞告警 | 基座核心退化 | 独立 Consumer Group 和快慢路径 |
| Worker 崩溃丢任务 | 数据缺口 | Outbox/Stream/ACK/Retry/DLQ |
| 模型升级破坏向量索引 | 搜索失效 | 版本并存和可重建索引 |
| 媒体越权或 SSRF | 隐私和安全事故 | 只经基座 Evidence API |
| 云模型误传敏感媒体 | 隐私事故 | 默认本地、显式授权和审计 |
| Summary 日期错误 | 用户失去信任 | Site Timezone 和 DST 测试 |
| Chat 产生无依据回答 | 产品可信度下降 | 检索引用、上下文限定和 abstain |
| Android 继续使用 HTTP | 网络泄露 | Debug/Release 安全差异 |
| 旧系统退役过早 | 功能中断 | 影子期、可回退开关和分项切换 |
| 历史数据拖慢迁移 | 新架构迟迟不上线 | 首轮只迁移新数据 |
| 模型/权重许可证不清 | 阻塞开源 | 发布前单独审计 |

## 26. 第一轮实际执行建议

下一步不要直接迁移 OpenCLIP。建议从以下任务开始：

### 第 1 步：BASELINE-001～005

用固定 Fixture 和最小测试把旧系统行为保存下来。

### 第 2 步：CONTRACT-001～005

在两个项目之间定义 Processor Contract、Result、Capability、权限和 Replay 语义。

### 第 3 步：FOUNDATION-001～006

在基座中完成可靠 Job、Stub Processor、Claim/Invocation 存储和 UI 展示。

### 第 4 步：SLICE-001～005

把 Stub Worker 放到 Video Summary 一侧，通过正式契约完成跨仓库闭环。

第一轮结束时应能演示：

```text
Frigate Fixture
→ Event Intelligence Review ended
→ Outbox / Redis Stream
→ Video Summary Stub Worker
→ Caption Claim + ModelInvocation
→ Event Intelligence API/UI
```

第一轮明确不包含：

- OpenCLIP；
- pgvector Search；
- LLM Summary；
- Chat；
- Android 改版；
- 旧系统删除。

这样可以先证明最关键的产品边界和可靠运行轨道，再逐步加入高级功能。

## 27. 最终完成标准

整个改造计划完成时，应满足：

1. Event Intelligence 是 Frigate 事件和 Evidence 的唯一入口；
2. Video Summary 不直接订阅 Frigate；
3. 两个项目不共享数据库或内部 ORM；
4. AI 任务可靠、幂等、可重试、可进入 DLQ；
5. 所有 AI 解释可追溯到 Evidence 和 ModelInvocation；
6. API 进程不加载重模型；
7. Search、Summary、Chat 不读取旧 Event 表；
8. Summary 基于 ReviewItem 并使用正确 Site Timezone；
9. Web/Android 只使用稳定 Video Summary API 和基座公开链接；
10. Android Release 默认禁止明文 HTTP；
11. 两个项目可独立构建、测试和版本化；
12. 一体 Compose 可以一键运行完整产品；
13. 旧数据已迁移或明确归档；
14. 旧重复链路已安全退役；
15. 两个项目均通过各自的开源发布 Gate。

---

本计划应与技术评估文档共同维护：技术评估解释“为什么改”，本计划规定“按什么顺序改、每一步如何验收”。如果实施过程中改变核心边界、数据所有权、Processor Contract、Replay 语义或开源关系，应先更新 ADR 和本计划，再继续开发。
