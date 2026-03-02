# Neo4j 图数据库集成指南

## 🎯 集成优势

将 Neo4j 图数据库集成到 RAG 系统中，可以：

- ✅ **快速查询角色关系** - 无需遍历所有文档
- ✅ **精确的角色信息** - 直接查询节点属性
- ✅ **复杂的关系查询** - 支持多跳关系查询
- ✅ **可视化关系网络** - 在 Neo4j Browser 中查看图谱
- ✅ **高性能检索** - 图数据库专为关系查询优化

## 📋 配置步骤

### 1. 安装 Neo4j

#### 选项 A: Neo4j Desktop (推荐)
- 下载: https://neo4j.com/desktop/
- 适合个人开发和测试
- 包含图形化界面

#### 选项 B: Neo4j Community Edition
- 下载: https://neo4j.com/download/
- 适合生产环境
- 命令行管理

### 2. 配置环境变量

创建 `.env` 文件：
```env
MOONSHOT_API_KEY=your_moonshot_api_key_here

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

### 3. 导入图数据

运行导入脚本：
```bash
python graph_data_extractor.py
python setup_neo4j_import.py
```

或者使用 Neo4j Browser 导入：
1. 打开 Neo4j Browser
2. 运行 `import_to_neo4j.cql` 脚本

### 4. 验证连接

运行测试脚本：
```bash
python graph_neo4j_retrieval.py
```

## 🔍 使用方法

### 查询角色关系

```python
from main import RAGSystem

# 创建 RAG 系统
rag_system = RAGSystem()
rag_system.initialize_system()
rag_system.build_knowledge_base()

# 询问角色关系问题
answer = rag_system.ask_question("漂泊者和谁互动最多？")
print(answer)
```

### 支持的查询类型

#### 1. 角色关系查询
- "漂泊者和谁是一对？"
- "漂泊者最恨谁？"
- "秧秧的关系网络是什么？"
- "漂泊者和炽霞有什么关系？"

#### 2. 角色出现查询
- "漂泊者第一次出现在哪里？"
- "秧秧最后一次出现在第几章？"
- "炽霞首次出现是哪一章？"

#### 3. 关系类型查询
- "漂泊者有哪些敌人？"
- "秧秧有哪些盟友？"
- "漂泊者在哪些地点出现过？"
- "秧秧拥有哪些物品？"
- "漂泊者属于哪个组织？"

### Neo4j Browser 查询

在 Neo4j Browser 中可以直接运行 Cypher 查询：

```cypher
# 查看所有角色
MATCH (c:Character) RETURN c LIMIT 25;

# 查看角色关系图
MATCH (c:Character)-[r:INTERACTS_WITH]->(c2:Character)
RETURN c, r, c2 LIMIT 100;

# 查看特定角色的关系
MATCH (c:Character {name: '漂泊者'})-[]-(connected)
RETURN c, connected LIMIT 200;

# 查看角色出现的章节
MATCH (c:Character {name: '秧秧'})-[:APPEARS_IN]->(ch:Chapter)
RETURN ch ORDER BY ch.chapter_number, ch.act_number;
```

## 📊 数据结构

### 节点类型

#### Character (角色)
- `id`: 唯一标识符
- `name`: 角色名称
- `description`: 角色描述
- `aliases`: 别名
- `first_seen_chapter`: 首次出现章节
- `first_seen_act`: 首次出现幕
- `occurrence_count`: 出现次数

#### Location (地点)
- `id`: 唯一标识符
- `name`: 地点名称
- `description`: 地点描述
- `aliases`: 别名

#### Chapter (章节)
- `id`: 唯一标识符
- `name`: 章节名称
- `chapter_number`: 章节编号
- `act_number`: 幕编号

#### Event (事件)
- `id`: 唯一标识符
- `name`: 事件名称
- `description`: 事件描述

#### Item (物品)
- `id`: 唯一标识符
- `name`: 物品名称
- `description`: 物品描述

#### Organization (组织)
- `id`: 唯一标识符
- `name`: 组织名称
- `description`: 组织描述

### 关系类型

- `APPEARS_IN`: 角色出现在某章节
- `LOCATED_AT`: 角色位于某地点
- `INTERACTS_WITH`: 角色之间互动
- `ENEMY`: 敌人关系
- `ALLY`: 盟友关系
- `OWNS`: 拥有物品
- `MEMBER_OF`: 所属组织
- `FAMILY`: 家庭关系
- `RELATES_TO`: 相关关系

## 🚀 性能优化

### 1. 使用 Neo4j 索引

```cypher
# 已自动创建的约束
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Character) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (ch:Chapter) REQUIRE ch.id IS UNIQUE;
```

### 2. 查询优化

- 优先使用 Neo4j 进行关系查询
- 限制返回结果数量
- 使用合适的索引

## 🐛 故障排除

### 1. 连接失败

**错误**: `Failed to establish connection`

**解决**:
- 检查 Neo4j 是否启动
- 检查 URI 和端口是否正确
- 检查用户名和密码

### 2. 数据未导入

**错误**: `Node not found`

**解决**:
- 运行 `graph_data_extractor.py` 重新提取数据
- 运行 `setup_neo4j_import.py` 重新导入数据
- 检查 CSV 文件是否在 import 目录

### 3. 查询超时

**错误**: `Query timeout`

**解决**:
- 减少查询范围
- 添加 LIMIT 限制
- 检查索引是否创建

## 📈 扩展功能

### 1. 添加自定义查询

在 `graph_neo4j_retrieval.py` 中添加新方法：

```python
def query_custom_relationship(self, character_name: str) -> List[Dict]:
    query = """
    MATCH (c:Character {name: $name})-[r]->(target)
    RETURN type(r) AS relationship_type, target.name AS target_name
    """
    return self._execute_query(query, {"name": character_name})
```

### 2. 添加图算法

```cypher
# 最短路径
MATCH path = shortestPath(
  (c1:Character {name: '漂泊者'})-[*]-(c2:Character {name: '炽霞'})
)
RETURN path;

# PageRank
CALL gds.pageRank.stream('Character')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC;
```

## 🎓 学习资源

- [Neo4j 官方文档](https://neo4j.com/docs/)
- [Cypher 查询语言](https://neo4j.com/docs/cypher-manual/current/)
- [图数据库概念](https://neo4j.com/docs/operations-manual/current/introduction-to-graphs/)

## 📞 支持

如有问题，请检查：
1. Neo4j 是否正常运行
2. 环境变量是否正确配置
3. 数据是否已正确导入
4. 查看日志文件中的错误信息