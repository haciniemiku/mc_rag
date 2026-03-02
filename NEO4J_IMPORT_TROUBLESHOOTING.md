# Neo4j CSV 导入问题排查指南

## 🚨 问题诊断

你运行查询后显示 "No changes, no records"，说明数据库中没有任何数据。

## 🔍 原因分析

### 1. CSV 文件未复制到正确位置

Neo4j 的 `file:///` URL 指向的是 **Neo4j 安装目录下的 import 文件夹**，而不是你的项目目录。

### 2. 如何找到正确的 import 目录

#### 方法一：在 Neo4j Browser 中运行
```cypher
SHOW DATABASES;
```

#### 方法二：查看 Neo4j Desktop 的数据库目录
Neo4j Desktop 的数据库通常在：
```
C:\Users\<用户名>\.neo4j\neo4jDatabases\
```

在该目录下找到你的数据库文件夹，然后进入：
```
<database-id>\installation-<version>\import\
```

#### 方法三：使用命令行
```bash
# Windows PowerShell
Get-ChildItem -Path "$env:USERPROFILE\.neo4j\neo4jDatabases" -Recurse -Directory -Filter "import" | Select-Object FullName
```

### 3. 复制 CSV 文件

找到 import 目录后，将以下文件复制到该目录：
- `graph_data\nodes.csv`
- `graph_data\relationships.csv`

## ✅ 正确的导入步骤

### 步骤 1：找到 import 目录
```
C:\Users\26386\.neo4j\neo4jDatabases\database-xxx\installation-4.4.xx\import\
```

### 步骤 2：复制 CSV 文件
```bash
# Windows PowerShell
copy "d:\26386\Desktop\projects\mc_rag\graph_data\nodes.csv" "C:\Users\26386\.neo4j\neo4jDatabases\database-xxx\installation-4.4.xx\import\"
copy "d:\26386\Desktop\projects\mc_rag\graph_data\relationships.csv" "C:\Users\26386\.neo4j\neo4jDatabases\database-xxx\installation-4.4.xx\import\"
```

### 步骤 3：重启 Neo4j（可选）
有时需要重启 Neo4j 才能识别新文件。

### 步骤 4：运行导入脚本
在 Neo4j Browser 中运行 `graph_data\import_to_neo4j.cql` 的内容。

## 🧪 测试导入

创建一个简单的测试：

1. 在 import 目录创建一个测试文件 `test.csv`：
```csv
id,name
1,测试节点
```

2. 运行测试查询：
```cypher
LOAD CSV WITH HEADERS FROM 'file:///test.csv' AS row
RETURN row;
```

如果能看到结果，说明导入功能正常。

## 💡 替代方案：使用 Neo4j Desktop 的图形界面

1. 打开 Neo4j Desktop
2. 选择你的项目
3. 点击 **Import** 按钮
4. 选择 CSV 文件
5. Neo4j 会自动处理导入

## 📋 检查清单

- [ ] 找到 Neo4j 的 import 目录
- [ ] 将 `nodes.csv` 复制到 import 目录
- [ ] 将 `relationships.csv` 复制到 import 目录
- [ ] 确认文件在 import 目录中
- [ ] 运行导入脚本

## 🐛 常见错误

### 错误 1：文件路径不正确
```
Cannot load from URL 'file:///nodes.csv': Couldn't load the external resource
```
**解决**：确保文件在 Neo4j 的 import 目录中

### 错误 2：文件不存在
```
No such file or directory
```
**解决**：检查文件路径和文件名

### 错误 3：权限问题
```
Access denied
```
**解决**：以管理员身份运行 Neo4j

## 📞 需要帮助？

如果以上方法都不行，请告诉我：
1. 你使用的是 Neo4j Desktop 还是 Community Edition？
2. 你的数据库目录在哪里？
3. 你尝试过哪些方法？

我会帮你进一步排查问题。