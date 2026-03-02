# Neo4j 数据查询指南

## 📊 查看数据统计

### 查看节点数量
```cypher
MATCH (n) 
RETURN count(n) AS node_count;
```

### 查看关系数量
```cypher
MATCH ()-[r]->() 
RETURN count(r) AS relationship_count;
```

### 查看各类型节点数量
```cypher
MATCH (n)
RETURN labels(n)[0] AS type, count(n) AS count
ORDER BY count DESC;
```

## 🔍 常用查询

### 1. 查看所有角色
```cypher
MATCH (c:Character)
RETURN c.name, c.description, c.occurrence_count
ORDER BY c.occurrence_count DESC
LIMIT 25;
```

### 2. 查看角色关系网络（以漂泊者为例）
```cypher
MATCH (c:Character {name: '漂泊者'})-[r:INTERACTS_WITH]->(c2:Character)
RETURN c.name, r, c2.name, r.weight
ORDER BY r.weight DESC;
```

### 3. 查看角色出现的章节
```cypher
MATCH (c:Character)-[r:APPEARS_IN]->(ch:Chapter)
WHERE c.name = '秧秧'
RETURN ch.name, r.chapter, r.act
ORDER BY ch.chapter_number, ch.act_number;
```

### 4. 查看角色出现的地点
```cypher
MATCH (c:Character)-[r:LOCATED_AT]->(l:Location)
WHERE c.name = '炽霞'
RETURN l.name, count(*) as times
ORDER BY times DESC;
```

### 5. 查看角色的首次出现
```cypher
MATCH (c:Character)
RETURN c.name, c.first_seen_chapter, c.first_seen_act
ORDER BY c.first_seen_chapter, c.first_seen_act;
```

### 6. 查看章节中的所有角色
```cypher
MATCH (c:Character)-[:APPEARS_IN]->(ch:Chapter)
WHERE ch.chapter_number = 1
RETURN ch.act_number, collect(c.name) as characters
ORDER BY ch.act_number;
```

### 7. 查看角色关系路径
```cypher
MATCH path = shortestPath(
  (c1:Character {name: '漂泊者'})-[*]-(c2:Character {name: '炽霞'})
)
RETURN path;
```

### 8. 查看互动最强的角色对
```cypher
MATCH (c1:Character)-[r:INTERACTS_WITH]->(c2:Character)
RETURN c1.name, c2.name, r.weight, r.context
ORDER BY r.weight DESC
LIMIT 20;
```

### 9. 查看所有地点
```cypher
MATCH (l:Location)
RETURN l.name, l.description
ORDER BY l.name;
```

### 10. 查看所有事件
```cypher
MATCH (e:Event)
RETURN e.name, e.description
ORDER BY e.name;
```

## 🎨 可视化查询

### 查看角色关系图
```cypher
MATCH (c1:Character)-[r:INTERACTS_WITH]->(c2:Character)
WHERE r.weight > 0.5
RETURN c1, r, c2
LIMIT 100;
```

### 查看特定角色的关系网络
```cypher
MATCH (c:Character {name: '漂泊者'})-[]-(connected)
RETURN c, connected
LIMIT 200;
```

### 查看章节-角色关系图
```cypher
MATCH (c:Character)-[:APPEARS_IN]->(ch:Chapter)
WHERE ch.chapter_number < 5
RETURN c, ch
LIMIT 100;
```

## 💡 使用提示

1. **运行查询**: 在 Neo4j Browser 中输入查询，点击运行按钮（或按 Ctrl+Enter）

2. **查看结果**: 
   - 表格视图：显示查询结果
   - 图形视图：显示节点和关系的可视化

3. **导出结果**: 点击结果右上角的导出按钮

4. **保存查询**: 点击查询框右上角的保存按钮，可以保存常用查询

5. **清空结果**: 点击右上角的清空按钮

## 🎯 推荐查询组合

### 查询角色关系网络
```cypher
// 1. 首先查看角色列表
MATCH (c:Character)
RETURN c.name, c.occurrence_count
ORDER BY c.occurrence_count DESC;

// 2. 选择一个角色，查看其关系
MATCH (c:Character {name: '秧秧'})-[]-(connected)
RETURN c, connected
LIMIT 50;
```

### 查询剧情发展
```cypher
// 按章节顺序查看角色出现
MATCH (c:Character)-[:APPEARS_IN]->(ch:Chapter)
RETURN ch.chapter_number, ch.act_number, collect(c.name) as characters
ORDER BY ch.chapter_number, ch.act_number;
```

### 查询地点分布
```cypher
// 查看角色在哪些地点出现
MATCH (c:Character)-[:LOCATED_AT]->(l:Location)
RETURN l.name, collect(DISTINCT c.name) as characters
ORDER BY size(collect(DISTINCT c.name)) DESC;
```

现在你可以使用这些查询来探索你的知识图谱了！如果需要更具体的查询，请告诉我你想查询什么内容。