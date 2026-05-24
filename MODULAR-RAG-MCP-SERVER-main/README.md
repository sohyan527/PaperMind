# 科研文献管理 RAG 系统

面向科研论文、技术报告、课题资料和实验文档的本地化 RAG 知识管理系统。系统支持将 PDF、DOC/DOCX、PNG/JPG/JPEG 等文献资料摄取为可检索知识库，通过混合检索、重排序、多模态图片理解和可观测 dashboard，帮助研究者完成文献归档、论文问答、图表检索、研究线索追踪和知识库评估。

本项目保留 MCP Server 能力，可作为科研知识库工具暴露给支持 MCP 的 AI 客户端，也提供 Streamlit Dashboard 用于文献上传、数据浏览、摄取链路追踪、查询链路追踪和评估。

## 核心场景

- **文献集中管理**：将论文 PDF、课题报告、Word 笔记、扫描图、实验截图统一入库。
- **论文语义检索**：用自然语言查询研究问题、方法、数据集、指标、结论和局限。
- **图表内容检索**：提取 PDF/DOCX 中的图表图片，使用 Vision LLM 生成描述，让图表也能被文本检索命中。
- **综述辅助**：围绕某个研究主题检索多篇文献片段，辅助整理研究脉络。
- **可观测调试**：查看摄取、切分、增强、向量化、检索、融合、重排等中间结果。
- **质量评估**：通过 golden test set 和 RAG 评估模块持续检查检索质量。

## 功能概览

| 模块 | 能力 | 说明 |
| --- | --- | --- |
| 文献摄取 | PDF、DOC、DOCX、PNG、JPG、JPEG | Dashboard 支持多格式上传；DOC 依赖 LibreOffice 转换 |
| 文本解析 | MarkItDown + 自定义 Loader | 文档统一转换为标准 `Document` 协议 |
| 图片处理 | PDF/DOCX 内嵌图提取，单图上传 | 图片以 `[IMAGE: id]` 占位符进入文本链路 |
| 图片过滤 | 小装饰图过滤，重复图去重 | 减少校徽、页眉、样式元素等无用图片入库 |
| 图片理解 | Vision LLM Caption | 将图表描述写回 chunk，支持“用文字搜图片” |
| 切分与增强 | Recursive Splitter、Chunk Refiner、Metadata Enricher | 生成适合检索的语义块和元数据 |
| 检索 | Dense + BM25 + RRF | 兼顾语义召回和关键词精确匹配 |
| 重排序 | Cross-Encoder / LLM / None | 按配置启用重排 |
| 存储 | ChromaDB + BM25 Index + SQLite Image Index | 向量、关键词索引、图片索引分层存储 |
| Dashboard | 数据管理、链路追踪、评估面板 | 面向调试和文献库维护 |
| MCP Tools | `query_knowledge_hub`、`list_collections`、`get_document_summary` | 可被 MCP Client 调用 |

## 系统流程

```text
科研文献 / 图片
  -> LoaderFactory 按文件类型选择 Loader
  -> 文本解析 + 图片提取 + 图片过滤去重
  -> DocumentChunker 语义切分
  -> ChunkRefiner / MetadataEnricher
  -> ImageCaptioner 生成图表描述
  -> Dense Embedding + BM25 Sparse Encoding
  -> ChromaDB / BM25 / ImageStorage 入库
  -> Hybrid Search + Rerank
  -> Dashboard / MCP Tool 查询
```

## 支持的文档类型

| 类型 | 支持情况 | 说明 |
| --- | --- | --- |
| `.pdf` | 支持 | 提取文本和内嵌图片 |
| `.docx` | 支持 | 提取文本和 `word/media/*` 内嵌图片 |
| `.doc` | 支持，需 LibreOffice | 先转换为 DOCX 再解析 |
| `.png` / `.jpg` / `.jpeg` | 支持 | 作为单图文献资料入库 |

PDF 和 DOCX 中的图片会先经过过滤：

- 小图标、页眉页脚、装饰元素会被跳过。
- 完全重复图片会被跳过。
- 轻微缩放或压缩后的近似重复图片会被跳过。
- 只有保留下来的图片才会写入 `data/images`、`image_index.db`，并进入图片 caption 阶段。

单独上传的图片不会被装饰图过滤，因为用户主动上传的图片默认视为有效研究资料。

## 目录结构

```text
.
├── config/                         # 系统配置和 prompt
├── data/                           # 本地数据、向量库、BM25、图片索引
├── scripts/                        # 启动、摄取、查询、评估脚本
├── src/
│   ├── core/                       # 通用类型、配置、查询引擎、trace
│   ├── ingestion/                  # 文献摄取、切分、增强、向量化、存储
│   ├── libs/                       # Loader、LLM、Embedding、VectorStore、Splitter
│   ├── mcp_server/                 # MCP 工具和协议处理
│   └── observability/dashboard/    # Streamlit Dashboard
└── tests/                          # 单元、集成、端到端测试
```

## 快速开始

### 1. 创建虚拟环境

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
source .venv/bin/activate
```

### 2. 安装依赖

```bash
python -m pip install -e ".[dev]"
```

如需处理 PDF 内嵌图片，请确保安装 PyMuPDF：

```bash
python -m pip install pymupdf
```

如需处理 `.doc` 老格式 Word 文件，请安装 LibreOffice，并确保命令行可以访问 `soffice`。

### 3. 配置模型

编辑 `config/settings.yaml`。当前示例使用 Qwen / DashScope OpenAI-compatible 接口：

```yaml
llm:
  provider: "qwen"
  model: "qwen-turbo"
  api_key: ""
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"

embedding:
  provider: "qwen"
  model: "text-embedding-v3"
  dimensions: 1024
  api_key: ""
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"

vision_llm:
  enabled: true
  provider: "qwen"
  model: "qwen-vl-max"
  api_key: ""
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  max_image_size: 2048
```

也可以通过环境变量提供 key：

```bash
export DASHSCOPE_API_KEY="your-key"
```

Windows PowerShell：

```powershell
$env:DASHSCOPE_API_KEY="your-key"
```

## 启动 Dashboard

```bash
python scripts/start_dashboard.py
```

默认地址：

```text
http://localhost:8501
```

Dashboard 页面包括：

- **Overview**：系统配置和数据统计。
- **Ingestion Manager**：上传科研文献、触发入库、删除文档。
- **Data Browser**：查看已入库文档、chunk 和图片。
- **Ingestion Traces**：查看文献摄取每个阶段的中间结果。
- **Query Traces**：查看查询、召回、融合、重排过程。
- **Evaluation Panel**：运行 RAG 评估。

## 上传科研文献

推荐使用 Dashboard 的 `Ingestion Manager` 页面上传：

```text
PDF / DOC / DOCX / PNG / JPG / JPEG
```

上传后选择 collection，例如：

- `paper_reading`
- `llm_survey`
- `experiment_notes`
- `thesis_refs`

系统会自动执行：

1. 文件 hash 检查，避免重复处理。
2. 文本解析。
3. 图片提取、过滤和去重。
4. 文本切分。
5. chunk 改写和元数据增强。
6. 图片 caption。
7. 向量化和 BM25 编码。
8. 写入 ChromaDB、BM25、ImageStorage。

如果文档已经处理过，需要重新入库，可以先在 Dashboard 删除该文档，再重新上传。

## 查看已入库文档

可以在 Dashboard 中查看：

- `Ingestion Manager` 页面下方的文档列表。
- `Data Browser` 页面中的 collection、文档、chunk 和图片详情。

系统内部会聚合以下数据源：

- `data/db/ingestion_history.db`
- ChromaDB 向量库
- `data/db/bm25`
- `data/db/image_index.db`
- `data/images`

## 命令行摄取

脚本入口：

```bash
python scripts/ingest.py --path path/to/paper.pdf --collection paper_reading
```

强制重新处理：

```bash
python scripts/ingest.py --path path/to/paper.pdf --collection paper_reading --force
```

说明：当前 Dashboard 是多格式文献上传的推荐入口；命令行脚本主要用于批量或自动化处理场景。

## 命令行查询

```bash
python scripts/query.py --query "这篇论文使用了什么数据集和评价指标？" --collection paper_reading
```

查看更详细的召回过程：

```bash
python scripts/query.py --query "RAG 检索阶段用了哪些方法？" --collection paper_reading --verbose
```

禁用重排：

```bash
python scripts/query.py --query "论文的主要贡献是什么？" --collection paper_reading --no-rerank
```

## MCP 工具

项目提供 MCP 工具接口，便于 AI 客户端访问科研知识库。

主要工具：

- `query_knowledge_hub`：面向文献库执行查询。
- `list_collections`：列出已有 collection。
- `get_document_summary`：获取指定文档摘要和元数据。

典型使用场景：

- 在 AI 客户端中询问某个研究主题的相关论文。
- 查询某篇论文的贡献、方法、实验设置和局限。
- 让 Agent 基于本地文献库辅助写综述、开题报告或实验计划。

## 多模态图片处理策略

科研文献中的图片主要包括两类：

- 有价值图片：模型结构图、实验流程图、结果图表、消融实验表格截图。
- 无价值图片：校徽、页眉页脚、版权标识、背景纹理、装饰线条。

系统在 loader 阶段会过滤明显无价值图片：

- 尺寸过小的图片不保存。
- 面积过小的图片不保存。
- 完全重复的图片不保存。
- 近似重复的图片不保存。

这可以显著降低 PPT PDF 或模板化论文中的无效图片数量，减少 Vision LLM 调用成本。

图片保留后会进入 caption 阶段，caption 文本会被写入 chunk：

```text
[IMAGE: image_id]
(Description: ...)
```

因此用户可以通过文字检索图表内容。

## 配置建议

### 降低 Vision API 压力

如果图片很多或 Vision 接口不稳定，可以在 `config/settings.yaml` 中降低图片尺寸：

```yaml
vision_llm:
  max_image_size: 1024
```

### 关闭图片理解

如果只需要纯文本文献管理：

```yaml
vision_llm:
  enabled: false
```

### 调整切分粒度

```yaml
ingestion:
  chunk_size: 1000
  chunk_overlap: 200
```

科研论文通常建议保留一定 overlap，以减少方法描述、公式解释和实验结论被切断的问题。

## 可观测性

系统会记录 ingestion 和 query trace，便于调试：

- Load 阶段：文档文本长度、图片数量。
- Split 阶段：chunk 数量、chunk 文本。
- Transform 阶段：refine、metadata enrich、image caption 情况。
- Embed 阶段：dense/sparse 编码统计。
- Upsert 阶段：向量、BM25、图片索引写入情况。
- Query 阶段：dense 召回、BM25 召回、RRF 融合、rerank 结果。

这些信息可以在 Dashboard 的 trace 页面查看。

## 测试

运行单元测试：

```bash
python -m pytest tests/unit -q
```

运行指定测试：

```bash
python -m pytest tests/unit/test_loader_factory.py tests/unit/test_image_loader.py -q
```

本项目已覆盖：

- loader 合约。
- PDF/DOCX/图片摄取。
- 图片过滤和去重。
- chunk 元数据继承。
- LLM、Embedding、Retriever、Reranker 基础行为。
- Dashboard smoke。
- MCP 工具基础行为。

## 已知限制

- `.doc` 依赖 LibreOffice，本机没有 `soffice` 时无法自动转换。
- PDF/DOCX 图片占位符目前采用简化插入策略，未精确还原到原始段落位置。
- 图片过滤使用规则和轻量感知哈希，不等同于专业视觉去重模型。
- 对已入库旧文档，修改过滤规则后需要删除并重新 ingest 才会生效。
- Vision LLM 依赖外部模型服务，网络波动时可能仍出现少量失败；系统会重试并尽量 fallback。

## 适合谁使用

- 需要管理大量论文 PDF 的研究生、科研人员。
- 需要快速检索课题资料和实验记录的研发团队。
- 想构建个人文献知识库的工程师。
- 想学习 RAG 系统工程化、可观测性和多模态摄取流程的开发者。

## 项目定位

这个项目不是单纯的问答 demo，而是一个面向科研文献管理的 RAG 工程底座。它强调：

- 多格式文献接入。
- 文本和图表统一检索。
- 可解释、可追踪的摄取和查询链路。
- 可配置的模型、向量库、重排器和评估模块。
- 可通过 Dashboard 使用，也可通过 MCP 接入 AI 客户端。

目标是把分散的论文、报告、笔记和图表整理成一个可持续维护、可查询、可评估的个人或团队科研知识库。
