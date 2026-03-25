# 🚀 启动说明

## 环境准备

### 1. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
MOONSHOT_API_KEY=你的Moonshot API密钥
```

## 启动方式

### 方式1：启动 Streamlit 前端界面（推荐）

```bash
streamlit run streamlit_app.py
```

### 方式2：启动命令行交互模式

```bash
python main.py
```

然后输入：
```python
rag_system = RAGSystem()
rag_system.initialize_system()
rag_system.run_interactive()
```

## 项目结构

```
mc_rag/
├── main.py                    # RAG系统核心代码
├── streamlit_app.py          # Streamlit前端界面
├── config.py                 # 配置文件
├── data_preparation.py       # 数据准备模块
├── index_construction.py     # 索引构建模块
├── retrieval_optimization.py # 检索优化模块
├── generation_integration.py # 生成集成模块
├── graph_neo4j_retrieval.py  # Neo4j图检索（可选）
├── requirements.txt          # 依赖列表
└── .env                      # 环境变量（需要自己创建）
```

## 常见问题

### 1. 内存不足

如果遇到内存不足问题，可以：
- 使用更小的嵌入模型：`BAAI/bge-small-zh-v1.5`
- 减少 `top_k` 值
- 使用 GPU 加速

### 2. API 限流

如果遇到 API 限流问题：
- 增加重试间隔
- 减少并发请求
- 使用更高级别的 API 计划

### 3. Neo4j 连接失败

如果 Neo4j 连接失败：
- 检查 Neo4j 服务是否启动
- 检查连接参数是否正确
- 或者注释掉 Neo4j 相关代码

## 技术栈

- **LLM**: Moonshot (Kimi)
- **向量数据库**: FAISS
- **嵌入模型**: BGE-small-zh
- **检索器**: BM25 + 向量检索
- **前端**: Streamlit
- **图数据库**: Neo4j (可选)
