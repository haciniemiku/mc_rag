# 知识图谱提取使用指南

## 📖 概述

本模块使用大语言模型(LLM)从剧情文本中提取实体和关系，生成知识图谱数据，并支持导入到Neo4j图数据库。

## 🏗️ 架构设计

```
数据源(md文件)
    ↓
数据准备模块 (data_preparation.py)
    ↓
LLM实体关系提取 (graph_data_extractor.py)
    ↓
结构化输出 (nodes.csv, relationships.csv)
    ↓
Neo4j导入脚本 (import_to_neo4j.cql)
    ↓
Neo4j图数据库
```

## 🚀 快速开始

### 1. 环境准备

确保已安装依赖：
```bash
pip install langchain langchain-openai python-dotenv
```

### 2. 配置API密钥

在 `.env` 文件中设置：
```
MOONSHOT_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.moonshot.cn/v1
```

### 3. 运行提取

**方式一：独立运行**
```bash
python run_graph_extraction.py
```

**方式二：集成到数据准备流程**
```bash
python data_preparation.py
# 在测试完成后选择是否执行图数据提取
```

**方式三：在代码中调用**
```python
from data_preparation import DataPreparationModule

data_prep = DataPreparationModule("md_output")
documents = data_prep.load_documents()
nodes_file, rels_file, cypher_file = data_prep.extract_graph_data(batch_size=3)
```

## 📊 输出文件

### nodes.csv
节点数据文件，包含以下字段：
- `id`: 节点唯一标识
- `name`: 实体名称
- `type`: 实体类型 (Character/Location/Event/Item/Organization/Chapter)
- `description`: 实体描述
- `aliases`: 别名列表
- `first_seen_chapter`: 首次出现的章节
- `first_seen_act`: 首次出现的幕
- `occurrence_count`: 出现次数

### relationships.csv
关系数据文件，包含以下字段：
- `source_id`: 源节点ID
- `source_name`: 源节点名称
- `target_id`: 目标节点ID
- `target_name`: 目标节点名称
- `type`: 关系类型
- `context`: 关系上下文
- `chapter`: 章节信息
- `act`: 幕信息
- `weight`: 关系权重

### import_to_neo4j.cql
Neo4j Cypher导入脚本，包含：
- 约束和索引创建
- 节点数据导入
- 关系数据导入
- 数据验证查询

## 🗂️ 实体类型

| 类型 | 说明 | 示例 |
|------|------|------|
| Character | 角色 | 漂泊者、秧秧、炽霞 |
| Location | 地点 | 今州、云陵谷、黑海岸 |
| Event | 事件 | 嘤鸣初相召、撞金止行阵 |
| Item | 物品 | 声核、共鸣者 |
| Organization | 组织 | 瑝珑、夜归 |
| Chapter | 章节 | 第一章第一幕 |

## 🔗 关系类型

| 关系 | 说明 | 示例 |
|------|------|------|
| APPEARS_IN | 出现在 | 角色-章节 |
| LOCATED_AT | 位于 | 角色-地点 |
| INTERACTS_WITH | 互动 | 角色-角色 |
| PARTICIPATES_IN | 参与 | 角色-事件 |
| RELATES_TO | 关联 | 实体-实体 |
| OWNS | 拥有 | 角色-物品 |
| MEMBER_OF | 属于 | 角色-组织 |
| ALLY | 同盟 | 角色-角色 |
| ENEMY | 敌对 | 角色-角色 |
| FAMILY | 家庭 | 角色-角色 |

## 📥 导入Neo4j

### 方法一：使用Cypher脚本

1. 复制CSV文件到Neo4j import目录：
```bash
# Windows
copy graph_data\nodes.csv %NEO4J_HOME%\import\
copy graph_data\relationships.csv %NEO4J_HOME%\import\

# Linux/Mac
cp graph_data/nodes.csv $NEO4J_HOME/import/
cp graph_data/relationships.csv $NEO4J_HOME/import/
```

2. 在Neo4j Browser中运行：
```
:play import_to_neo4j.cql
```

### 方法二：使用neo4j-admin

```bash
neo4j-admin database load full --from=graph_data/
```

## 🔍 查询示例

### 查询所有角色
```cypher
MATCH (c:Character)
RETURN c.name, c.description
ORDER BY c.occurrence_count DESC
LIMIT 10
```

### 查询角色的互动关系
```cypher
MATCH (c:Character)-[r:INTERACTS_WITH]->(c2:Character)
WHERE c.name = '漂泊者'
RETURN c.name, c2.name, r.context, r.weight
ORDER BY r.weight DESC
```

### 查询角色出现的位置
```cypher
MATCH (c:Character)-[:LOCATED_AT]->(l:Location)
WHERE c.name = '秧秧'
RETURN l.name, count(*) as times
ORDER BY times DESC
```

### 查询章节中的所有角色
```cypher
MATCH (c:Character)-[:APPEARS_IN]->(ch:Chapter)
WHERE ch.chapter_number = 1
RETURN ch.act_number, collect(c.name) as characters
ORDER BY ch.act_number
```

### 查询角色关系路径
```cypher
MATCH path = shortestPath(
  (c1:Character {name: '漂泊者'})-[*]-(c2:Character {name: '炽霞'})
)
RETURN path
```

## ⚙️ 参数配置

### 批处理大小
调整 `batch_size` 参数以平衡速度和API限制：
```python
extractor.extract_from_documents(documents, batch_size=3)  # 推荐3-5
```

### 模型选择
```python
extractor = GraphDataExtractor(
    model_name="moonshot-v1-8k",  # 或 "moonshot-v1-32k"
    output_dir="graph_data"
)
```

### 文本长度限制
```python
content = doc.page_content[:3000]  # 调整文本长度
```

## 🐛 故障排除

### API限流错误
```
Error code: 429 - The engine is currently overloaded
```
**解决方案**：
- 增加重试延迟
- 减小batch_size
- 等待一段时间后重试

### JSON解析失败
```
JSONDecodeError: Expecting value
```
**解决方案**：
- 检查LLM输出格式
- 调整prompt模板
- 增加输出格式说明

### Neo4j导入失败
```
Unable to load CSV file
```
**解决方案**：
- 确认CSV文件在import目录
- 检查文件编码(UTF-8)
- 验证文件路径配置

## 📈 性能优化

1. **并行处理**：使用多线程处理多个文档
2. **缓存机制**：缓存已提取的实体和关系
3. **增量更新**：只处理新增或修改的文档
4. **批量导入**：使用Neo4j的批量导入功能

## 📝 最佳实践

1. **数据质量**：确保源数据格式统一、内容完整
2. **实体消歧**：处理同名实体和别名
3. **关系验证**：验证关系的合理性和完整性
4. **定期更新**：定期重新提取以更新知识图谱

## 📚 参考资料

- [Neo4j官方文档](https://neo4j.com/docs/)
- [Cypher查询语言](https://neo4j.com/docs/cypher-manual/current/)
- [LangChain文档](https://python.langchain.com/docs/)
