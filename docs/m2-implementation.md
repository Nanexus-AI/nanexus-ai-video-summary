# M2 实现总结：日终摘要 Worker + Chat RAG

在 M1 理解层之上，完成「预计算摘要」与「基于检索的问答」，控制 LLM 成本。

相关文档：

- 架构：[architecture.md](./architecture.md)
- M1：[m1-implementation.md](./m1-implementation.md)

---

## 1. M2 目标

| 目标 | 状态 |
|------|------|
| Summary Worker 日终任务 | ✅ 定时 + Redis 队列 |
| `GET /summary/today` 只读预计算结果 | ✅（M0 已有，M2 强化写入路径） |
| 基础 Chat（RAG over events/summaries） | ✅ `POST /chat` |

---

## 2. Summary Worker

进程：`python -m services.summary_worker.main`

| 触发 | 行为 |
|------|------|
| 定时 | 每天 `SUMMARY_HOUR:SUMMARY_MINUTE`（默认 23:50，`SUMMARY_TIMEZONE`）入队一次 |
| 队列 | 消费 `nanexus:summary:jobs`，调用 `build_daily_summary` 落库 |
| 手动 | `POST /summary/regenerate` 入队；或 `--once` / `scripts/build_summary.py` |

模式：

| `SUMMARY_MODE` | 说明 |
|----------------|------|
| `rule`（默认） | 结构化统计 + highlights，无外部费用 |
| `llm` | OpenAI 兼容 Chat Completions；失败回退 rule |

原则：**客户端只 `GET /summary/today`**，不在请求路径同步烧 LLM（除非显式 `sync=true` 调试）。

---

## 3. Chat RAG

`POST /chat`

```json
{ "message": "今天前院有几辆车？", "camera": "front_yard" }
```

流程：

1. 语义/关键词检索近期事件（`CHAT_LOOKBACK_DAYS`）
2. 附带近几日 `daily_summaries`
3. `CHAT_MODE=extractive`：基于检索上下文的规则回答（默认，零成本）
4. `CHAT_MODE=llm`：把上下文送给 LLM；失败回退 extractive
5. 写入 `conversations`（messages JSON + related_event_ids）

---

## 4. 新增配置

```bash
SUMMARY_MODE=rule
SUMMARY_HOUR=23
SUMMARY_MINUTE=50
SUMMARY_TIMEZONE=UTC
CHAT_MODE=extractive
CHAT_LOOKBACK_DAYS=3
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

---

## 5. 验证

```bash
# 第四个进程
python -m services.summary_worker.main

# 立刻生成今日摘要（入队）
curl -s localhost:8000/summary/regenerate \
  -H 'content-type: application/json' \
  -d '{"sync":false}' 

# 或同步
curl -s localhost:8000/summary/regenerate \
  -H 'content-type: application/json' \
  -d '{"sync":true}' | python -m json.tool

curl -s localhost:8000/summary/today | python -m json.tool

curl -s localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"今天 front_yard 有什么车？","camera":"front_yard"}' \
  | python -m json.tool
```

---

## 6. 一句话

M2 把摘要预计算交给独立 worker，把问答做成「先检索再回答」；默认 rule/extractive 可在无 LLM Key 时用真实 Frigate 数据跑通，接上 `LLM_API_KEY` 即可升级文案质量。
