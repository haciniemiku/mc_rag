# 🎮 鸣潮剧情 RAG 助手 - Neo4j 集成版

## 📖 目录

- [快速开始](#-快速开始)
- [功能特性](#-功能特性)
- [系统架构](#-系统架构)
- [Neo4j 集成](#-neo4j-集成)
- [使用方法](#-使用方法)
- [测试](#-测试)
- [故障排除](#-故障排除)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
MOONSHOT_API_KEY=your_moonshot_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

### 3. 构建知识库

```bash
python main.py
```

### 4. 开始对话

按照提示输入问题，例如：
- "漂泊者和谁是一对？"
- "秧秧第一次出现在哪里？"
- "漂泊者最恨谁？"

## ✨ 功能特性

### 核心功能

- ✅ **剧情问答** - 基于鸣潮游戏剧情的问答系统
- ✅ **角色信息查询** - 查询角色的详细信息
- ✅ **关系网络分析** - 分析角色之间的关系
- ✅ **章节检索** - 精确查找特定章节的内容
- ✅ **地点检索** - 查找特定地点的信息

### Neo4j 图数据库功能

- ✅ **快速关系查询** - 基于图数据库的高性能关系查询
- ✅ **角色关系网络** - 可视化角色关系
- ✅ **多跳关系查询** - 查询多层关系
- ✅ **图算法支持** - 支持 PageRank 等图算法

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户接口                                │
│                    (Streamlit/CLI)                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG 系统核心                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  检索模块    │  │  生成模块    │  │  图检索模块  │       │
│  │  (Hybrid)    │  │  (LLM)      │  │  (Neo4j)     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  向量数据库     │  │  知识库文档     │  │  Neo4j 图数据库 │
│  (FAISS + BM25) │  │  (Markdown)     │  │  (Nodes/Edges)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 🔗 Neo4j 集成

### 数据模型

#### 节点类型

1. **Character (角色)**
   - 属性: id, name, description, aliases, first_seen_chapter, first_seen_act, occurrence_count
   - 关系: APPEARS_IN, INTERACTS_WITH, ENEMY, ALLY, LOCATED_AT, OWNS, MEMBER_OF

2. **Location (地点)**
   - 属性: id, name, description, aliases
   - 关系: 被角色 LOCATED_AT

3. **Chapter (章节)**
   - 属性: id, name, chapter_number, act_number
   - 关系: APPEARS_IN (被角色)

4. **Item (物品)**
   - 属性: id, name, description
   - 关系: OWNS (被角色)

5. **Organization (组织)**
   - 属性: id, name, description
   - 关系: MEMBER_OF (角色), APPEARS_IN

6. **Event (事件)**
   - 属性: id, name, description
   - 关系: PARTICIPATES_IN (角色)

#### 关系类型

- `APPEARS_IN`: 角色出现在某章节
- `LOCATED_AT`: 角色位于某地点
- `INTERACTS_WITH`: 角色之间互动
- `ENEMY`: 敌人关系
- `ALLY`: 盟友关系
- `OWNS`: 拥有物品
- `MEMBER_OF`: 所属组织
- `FAMILY`: 家庭关系
- `RELATES_TO`: 相关关系

### 数据流程

```
剧情文档 → LLM 提取 → 结构化数据 → Neo4j 导入
```

1. **数据提取**
   ```bash
   python graph_data_extractor.py
   ```

2. **数据导入**
   ```bash
   python setup_neo4j_import.py
   ```

3. **验证导入**
   ```bash
   python graph_neo4j_retrieval.py
   ```

## 💡 使用方法

### 1. 交互式对话

```bash
python main.py
```

### 2. Python API

```python
from main import RAGSystem

# 创建系统
rag_system = RAGSystem()
rag_system.initialize_system()
rag_system.build_knowledge_base()

# 问答
answer = rag_system.ask_question("漂泊者和谁是一对？")
print(answer)
```

### 3. Neo4j Browser 查询

在 Neo4j Browser 中运行：

```cypher
# 查看所有角色
MATCH (c:Character) RETURN c LIMIT 25;

# 查看角色关系图
MATCH (c:Character)-[r:INTERACTS_WITH]->(c2:Character)
RETURN c, r, c2 LIMIT 100;

# 查看特定角色的关系
MATCH (c:Character {name: '漂泊者'})-[]-(connected)
RETURN c, connected LIMIT 200;
```

### 4. 支持的查询类型

#### 角色关系查询
- "漂泊者和谁是一对？"
- "漂泊者最恨谁？"
- "秧秧的关系网络是什么？"
- "漂泊者和炽霞有什么关系？"

#### 角色出现查询
- "漂泊者第一次出现在哪里？"
- "秧秧最后一次出现在第几章？"
- "炽霞首次出现是哪一章？"

#### 关系类型查询
- "漂泊者有哪些敌人？"
- "秧秧有哪些盟友？"
- "漂泊者在哪些地点出现过？"
- "秧秧拥有哪些物品？"
- "漂泊者属于哪个组织？"

## 🧪 测试

### 1. Neo4j 连接测试

```bash
python test_neo4j_integration.py
```

### 2. 图检索测试

```bash
python graph_neo4j_retrieval.py
```

### 3. 完整系统测试

```bash
python main.py
```

## 🐛 故障排除

### 1. Neo4j 连接失败

**错误**: `Failed to establish connection`

**解决**:
```bash
# 检查 Neo4j 是否启动
# Neo4j Desktop: 点击 "Start" 按钮
# Neo4j CLI: neo4j start

# 检查配置
cat .env
```

### 2. 数据未导入

**错误**: `Node not found`

**解决**:
```bash
# 重新导入数据
python graph_data_extractor.py
python setup_neo4j_import.py

# 或在 Neo4j Browser 中运行
# import_to_neo4j.cql
```

### 3. 环境变量未加载

**解决**:
```bash
# 确保 .env 文件存在
# 确保格式正确
MOONSHOT_API_KEY=your_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### 4. 查询超时

**解决**:
```cypher
# 添加 LIMIT 限制
MATCH (c:Character) RETURN c LIMIT 25;

# 检查索引
SHOW INDEXES;
```

## 📚 相关文档

- [Neo4j 集成指南](NEO4J_INTEGRATION_GUIDE.md)
- [Neo4j 查询指南](NEO4J_QUERIES.md)
- [Neo4j 导入指南](NEO4J_IMPORT_TROUBLESHOOTING.md)

## 🎓 技术栈

- **Python 3.8+**
- **LangChain** - LLM 集成
- **FAISS** - 向量检索
- **Neo4j** - 图数据库
- **Streamlit** - Web 界面

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题，请查看：
1. [故障排除](#-故障排除)
2. [相关文档](#-相关文档)
3. 创建 Issue

---

**享受探索鸣潮剧情的乐趣！** 🎮