// Neo4j 数据导入脚本
// 生成时间: 2026-03-01 18:28:09

// ==========================================
// 📋 使用说明
// ==========================================
// 1. 找到 Neo4j 的 import 目录
//    在 Neo4j Browser 中运行:
//    CALL dbms.listConfig() YIELD name, value
//    WHERE name = 'dbms.directories.import'
//    RETURN value
//
// 2. 将 graph_data/nodes.csv 和 graph_data/relationships.csv
//    复制到上面找到的 import 目录
//
// 3. 在 Neo4j Browser 中运行此脚本
// ==========================================

// 创建约束和索引
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Character) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (ch:Chapter) REQUIRE ch.id IS UNIQUE;

// 导入节点数据
// 注意: 确保 nodes.csv 已复制到 Neo4j 的 import 目录
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CALL {
  WITH row
  FOREACH (_ IN CASE WHEN row.type = 'Character' THEN [1] ELSE [] END |
    MERGE (n:Character {id: row.id})
    ON CREATE SET
      n.name = row.name,
      n.description = row.description,
      n.aliases = row.aliases,
      n.first_seen_chapter = row.first_seen_chapter,
      n.first_seen_act = row.first_seen_act,
      n.occurrence_count = toInteger(row.occurrence_count)
    ON MATCH SET
      n.name = row.name,
      n.description = row.description,
      n.aliases = row.aliases,
      n.first_seen_chapter = row.first_seen_chapter,
      n.first_seen_act = row.first_seen_act,
      n.occurrence_count = toInteger(row.occurrence_count)
  )
  FOREACH (_ IN CASE WHEN row.type = 'Location' THEN [1] ELSE [] END |
    MERGE (n:Location {id: row.id})
    ON CREATE SET
      n.name = row.name,
      n.description = row.description,
      n.aliases = row.aliases
    ON MATCH SET
      n.name = row.name,
      n.description = row.description,
      n.aliases = row.aliases
  )
  FOREACH (_ IN CASE WHEN row.type = 'Event' THEN [1] ELSE [] END |
    MERGE (n:Event {id: row.id})
    ON CREATE SET
      n.name = row.name,
      n.description = row.description
    ON MATCH SET
      n.name = row.name,
      n.description = row.description
  )
  FOREACH (_ IN CASE WHEN row.type = 'Item' THEN [1] ELSE [] END |
    MERGE (n:Item {id: row.id})
    ON CREATE SET
      n.name = row.name,
      n.description = row.description
    ON MATCH SET
      n.name = row.name,
      n.description = row.description
  )
  FOREACH (_ IN CASE WHEN row.type = 'Organization' THEN [1] ELSE [] END |
    MERGE (n:Organization {id: row.id})
    ON CREATE SET
      n.name = row.name,
      n.description = row.description
    ON MATCH SET
      n.name = row.name,
      n.description = row.description
  )
  FOREACH (_ IN CASE WHEN row.type = 'Chapter' THEN [1] ELSE [] END |
    MERGE (n:Chapter {id: row.id})
    ON CREATE SET
      n.name = row.name,
      n.chapter_number = toInteger(row.chapter_number),
      n.act_number = toInteger(row.act_number)
    ON MATCH SET
      n.name = row.name,
      n.chapter_number = toInteger(row.chapter_number),
      n.act_number = toInteger(row.act_number)
  )
} IN TRANSACTIONS OF 1000 ROWS;

// 导入关系数据
// 注意: 确保 relationships.csv 已复制到 Neo4j 的 import 目录
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
CALL {
  WITH row
  MATCH (source {id: row.source_id})
  MATCH (target {id: row.target_id})
  FOREACH (_ IN CASE WHEN row.type = 'APPEARS_IN' THEN [1] ELSE [] END |
    MERGE (source)-[r:APPEARS_IN {context: row.context, chapter: row.chapter, weight: toFloat(row.weight)}]->(target)
  )
  FOREACH (_ IN CASE WHEN row.type = 'LOCATED_AT' THEN [1] ELSE [] END |
    MERGE (source)-[r:LOCATED_AT {context: row.context}]->(target)
  )
  FOREACH (_ IN CASE WHEN row.type = 'INTERACTS_WITH' THEN [1] ELSE [] END |
    MERGE (source)-[r:INTERACTS_WITH {context: row.context, chapter: row.chapter, weight: toFloat(row.weight)}]->(target)
  )
  FOREACH (_ IN CASE WHEN row.type = 'PARTICIPATES_IN' THEN [1] ELSE [] END |
    MERGE (source)-[r:PARTICIPATES_IN {context: row.context}]->(target)
  )
  FOREACH (_ IN CASE WHEN row.type = 'RELATES_TO' THEN [1] ELSE [] END |
    MERGE (source)-[r:RELATES_TO {context: row.context}]->(target)
  )
  FOREACH (_ IN CASE WHEN row.type = 'OWNS' THEN [1] ELSE [] END |
    MERGE (source)-[r:OWNS {context: row.context}]->(target)
  )
  FOREACH (_ IN CASE WHEN row.type = 'MEMBER_OF' THEN [1] ELSE [] END |
    MERGE (source)-[r:MEMBER_OF {context: row.context}]->(target)
  )
  FOREACH (_ IN CASE WHEN row.type = 'ALLY' THEN [1] ELSE [] END |
    MERGE (source)-[r:ALLY {context: row.context}]->(target)
  )
  FOREACH (_ IN CASE WHEN row.type = 'ENEMY' THEN [1] ELSE [] END |
    MERGE (source)-[r:ENEMY {context: row.context}]->(target)
  )
  FOREACH (_ IN CASE WHEN row.type = 'FAMILY' THEN [1] ELSE [] END |
    MERGE (source)-[r:FAMILY {context: row.context}]->(target)
  )
} IN TRANSACTIONS OF 1000 ROWS;
