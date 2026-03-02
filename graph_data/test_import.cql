// 测试 Neo4j CSV 导入

// 首先检查 import 目录
// 在 Neo4j Desktop 中，import 目录通常在：
// C:\Users\<用户名>\.neo4j\neo4jDatabases\<database-id>\installation-<version>\import\

// 测试 1: 检查 nodes.csv 是否存在
// 如果文件不存在，会报错

// 测试 2: 尝试导入少量数据
// 将 CSV 文件复制到 import 目录后运行

// 导入节点数据
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
RETURN row
LIMIT 5;
