# Neo4j 导入 CSV 文件指南

## 📋 问题原因

Neo4j 的 `file:///` URL 指向的是 Neo4j 安装目录下的 `import` 文件夹，而不是你的项目目录。

## 🔧 解决方案

### 方法一：使用 Neo4j Browser 查找 import 目录

1. **打开 Neo4j Browser**
   - 访问 http://localhost:7474
   - 登录 (用户名: neo4j, 密码: 你设置的密码)

2. **查找 import 目录**
   ```cypher
   CALL dbms.listConfig() YIELD name, value
   WHERE name = 'dbms.directories.import'
   RETURN value
   ```

3. **复制 CSV 文件到该目录**
   - Windows: 通常在 `C:\Users\<用户名>\.neo4j\neo4jDatabases\<database-id>\installation-<version>\import\`
   - Linux/Mac: 通常在 `~/.neo4j/neo4jDatabases/<database-id>/installation-<version>/import/`

4. **运行导入脚本**
   - 复制 `graph_data/import_to_neo4j.cql` 的内容
   - 粘贴到 Neo4j Browser
   - 点击运行

### 方法二：使用绝对路径

如果你知道 import 目录的位置，可以修改 `import_to_neo4j.cql` 中的路径：

```cypher
LOAD CSV WITH HEADERS FROM 'file:///C:/Users/YourUsername/.neo4j/neo4jDatabases/database-xxx/installation-4.4.xx/import/nodes.csv' AS row
```

### 方法三：使用 Neo4j Desktop 的图形界面

1. **打开 Neo4j Desktop**
2. **选择你的项目**
3. **点击 "Import" 按钮**
4. **选择 CSV 文件**
5. **Neo4j 会自动处理导入**

## 📝 完整导入步骤

### 1. 准备 CSV 文件
确保 `graph_data` 目录下有：
- `nodes.csv`
- `relationships.csv`

### 2. 找到 Neo4j import 目录
在 Neo4j Browser 中运行：
```cypher
CALL dbms.listConfig() YIELD name, value
WHERE name = 'dbms.directories.import'
RETURN value
```

### 3. 复制文件
将 CSV 文件复制到上面找到的目录。

### 4. 运行导入脚本
在 Neo4j Browser 中运行 `graph_data/import_to_neo4j.cql` 的内容。

### 5. 验证导入
```cypher
// 查看节点数量
MATCH (n) RETURN count(n) AS node_count;

// 查看关系数量
MATCH ()-[r]->() RETURN count(r) AS relationship_count;

// 查看所有角色
MATCH (c:Character) RETURN c.name LIMIT 10;
```

## 💡 提示

- 如果使用 Neo4j Desktop，文件路径可能需要使用正斜杠 `/` 而不是反斜杠 `\`
- 确保 CSV 文件编码为 UTF-8
- 如果导入失败，检查 Neo4j 日志文件获取详细错误信息

## 🐛 常见问题

### 1. 找不到文件
- 确认文件路径正确
- 检查文件是否在 import 目录中
- 确认文件名大小写正确

### 2. 权限错误
- 确保 Neo4j 有读取 CSV 文件的权限
- 尝试以管理员身份运行 Neo4j

### 3. 格式错误
- 检查 CSV 文件格式
- 确保第一行是列名
- 检查编码是否为 UTF-8
