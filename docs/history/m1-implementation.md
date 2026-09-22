# M1 实现总结：理解层（Snapshot → Caption → Embedding → Search）

> **Historical document.** Retained for engineering context; model names, defaults, and media
> behavior below are not current guidance. See [`docs/architecture.md`](../architecture.md) and
> [`docs/resource-profiles.md`](../resource-profiles.md).

在 M0 骨架之上，完成「真实视觉理解管线 + 语义搜索 + 媒体回跳」。

相关文档：

- 架构：[architecture.md](../architecture.md)
- M0：[m0-implementation.md](./m0-implementation.md)

---

## 1. M1 目标

| 目标 | 状态 |
|------|------|
| AI Worker：拉取 snapshot → caption → embedding | ✅ |
| `POST /search`（OpenCLIP + pgvector） | ✅ |
| 媒体 URI 可从 API 回跳 / 本地演示图可访问 | ✅ |
| 无 Frigate / 无 GPU 仍可演示 | ✅（本地 demo 图 + CPU） |

---

## 2. 实现要点

### 2.1 Vision 管线（`src/nanexus/vision.py`）

- 默认 `AI_MODE=openclip`
- 模型：OpenCLIP `ViT-B-32` / `openai`（512 维，与 `EMBEDDING_DIM` 对齐）
- **Embedding**：图像 L2 归一化向量写入 `events.embedding`
- **Caption**：零样本分类（安防场景候选标签）Top-3 + Frigate label/sub_label 拼成描述
- **Stub 回退**：`AI_MODE=stub`，或 snapshot 拉取失败时降级

### 2.2 媒体（`src/nanexus/media.py`）

支持：

- `http(s)://`（真实 Frigate，可选 `FRIGATE_TOKEN`）
- `file://` 本地路径
- `data/snapshots/` 下文件名

API：

| 接口 | 作用 |
|------|------|
| `GET /events/{id}/snapshot` | 本地文件优先，否则 307 跳到 Frigate URI |
| `GET /media/snapshots/{filename}` | 演示用静态快照 |

### 2.3 AI Worker

```text
dequeue → fetch snapshot → VisionPipeline.analyze_image → 写 caption/embedding/tags → done
```

启动时预加载 OpenCLIP（CPU 首次较慢）。

### 2.4 搜索（`POST /search`）

```json
{ "query": "black SUV", "limit": 10, "camera": null }
```

- `openclip`：query 文本编码 → `cosine_distance` 排序（pgvector）
- `stub` 或无向量：caption/label/tag 关键词回退

### 2.5 演示种子

`scripts/seed_events.py` 会：

1. 用 Pillow 生成带文字的彩色 JPEG（红衣人 / 黑 SUV / UPS 等）
2. 存到 `data/snapshots/{frigate_id}.jpg`
3. MQTT payload 的 `snapshot_uri` 使用 `file://...`，Worker 不依赖 API 在线

重跑理解：

```bash
python scripts/reprocess_events.py
# 或 POST /events/{id}/reprocess
```

---

## 3. 新增配置

| 变量 | 默认 | 说明 |
|------|------|------|
| `AI_MODE` | `openclip` | `stub` / `openclip` |
| `AI_DEVICE` | `auto` | `cpu` / `cuda` / `auto` |
| `OPENCLIP_MODEL` | `ViT-B-32` | |
| `OPENCLIP_PRETRAINED` | `openai` | |
| `FRIGATE_TOKEN` | 空 | Bearer token（可选） |
| `SNAPSHOTS_DIR` | `data/snapshots` | 本地快照目录 |
| `PUBLIC_BASE_URL` | `http://127.0.0.1:8000` | 对外 API 基址 |

---

## 4. 验证步骤

```bash
source .venv/bin/activate
pip install -e .

# 重启 api / mqtt_listener / ai_worker 后：
python scripts/seed_events.py
# 等待 worker 处理完成
curl -s localhost:8000/timeline | python -m json.tool
curl -s localhost:8000/search \
  -H 'content-type: application/json' \
  -d '{"query":"black SUV","limit":5}' | python -m json.tool
curl -sI localhost:8000/events/1/snapshot
```

期望：

- timeline 中 caption 含 `OpenCLIP sees:`
- search `method` 为 `openclip-pgvector`
- snapshot 接口返回 `200` 或 `307`

---

## 5. 与架构文档的对应

| 架构 M1 | 落地 |
|---------|------|
| snapshot → caption → embedding | OpenCLIP 零样本 caption + 图像 embedding |
| `POST /search` | pgvector cosine |
| 媒体回跳 Frigate | `/events/{id}/snapshot` redirect / 本地 file |

**说明：** 完整自然语言 caption（BLIP 等）未引入，以免 M1 依赖过重；零样本标签已足够支撑检索与时间线可读性，M2 可再升级 caption 模型。
