import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

try:
    from neo4j import GraphDatabase
    
    class Neo4jImporter:
        def __init__(self, uri, username, password):
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
        
        def close(self):
            self.driver.close()
        
        def create_constraints(self):
            """创建约束"""
            with self.driver.session() as session:
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Character) REQUIRE c.id IS UNIQUE;")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE;")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (ch:Chapter) REQUIRE ch.id IS UNIQUE;")
        
        def import_nodes(self, csv_file):
            """导入节点"""
            with self.driver.session() as session:
                result = session.run(f"""
                    LOAD CSV WITH HEADERS FROM 'file:///{csv_file}' AS row
                    CALL {{
                        WITH row
                        FOREACH (_ IN CASE WHEN row.type = 'Character' THEN [1] ELSE [] END |
                            MERGE (n:Character {{id: row.id}})
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
                            MERGE (n:Location {{id: row.id}})
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
                            MERGE (n:Event {{id: row.id}})
                            ON CREATE SET
                                n.name = row.name,
                                n.description = row.description
                            ON MATCH SET
                                n.name = row.name,
                                n.description = row.description
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'Item' THEN [1] ELSE [] END |
                            MERGE (n:Item {{id: row.id}})
                            ON CREATE SET
                                n.name = row.name,
                                n.description = row.description
                            ON MATCH SET
                                n.name = row.name,
                                n.description = row.description
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'Organization' THEN [1] ELSE [] END |
                            MERGE (n:Organization {{id: row.id}})
                            ON CREATE SET
                                n.name = row.name,
                                n.description = row.description
                            ON MATCH SET
                                n.name = row.name,
                                n.description = row.description
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'Chapter' THEN [1] ELSE [] END |
                            MERGE (n:Chapter {{id: row.id}})
                            ON CREATE SET
                                n.name = row.name,
                                n.chapter_number = toInteger(row.chapter_number),
                                n.act_number = toInteger(row.act_number)
                            ON MATCH SET
                                n.name = row.name,
                                n.chapter_number = toInteger(row.chapter_number),
                                n.act_number = toInteger(row.act_number)
                        )
                    }}
                    IN TRANSACTIONS OF 1000 ROWS;
                """)
                return result.summary()
        
        def import_relationships(self, csv_file):
            """导入关系"""
            with self.driver.session() as session:
                result = session.run(f"""
                    LOAD CSV WITH HEADERS FROM 'file:///{csv_file}' AS row
                    CALL {{
                        WITH row
                        MATCH (source {{id: row.source_id}})
                        MATCH (target {{id: row.target_id}})
                        FOREACH (_ IN CASE WHEN row.type = 'APPEARS_IN' THEN [1] ELSE [] END |
                            MERGE (source)-[r:APPEARS_IN {{context: row.context, chapter: row.chapter, weight: toFloat(row.weight)}}]->(target)
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'LOCATED_AT' THEN [1] ELSE [] END |
                            MERGE (source)-[r:LOCATED_AT {{context: row.context}}]->(target)
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'INTERACTS_WITH' THEN [1] ELSE [] END |
                            MERGE (source)-[r:INTERACTS_WITH {{context: row.context, chapter: row.chapter, weight: toFloat(row.weight)}}]->(target)
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'PARTICIPATES_IN' THEN [1] ELSE [] END |
                            MERGE (source)-[r:PARTICIPATES_IN {{context: row.context}}]->(target)
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'RELATES_TO' THEN [1] ELSE [] END |
                            MERGE (source)-[r:RELATES_TO {{context: row.context}}]->(target)
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'OWNS' THEN [1] ELSE [] END |
                            MERGE (source)-[r:OWNS {{context: row.context}}]->(target)
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'MEMBER_OF' THEN [1] ELSE [] END |
                            MERGE (source)-[r:MEMBER_OF {{context: row.context}}]->(target)
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'ALLY' THEN [1] ELSE [] END |
                            MERGE (source)-[r:ALLY {{context: row.context}}]->(target)
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'ENEMY' THEN [1] ELSE [] END |
                            MERGE (source)-[r:ENEMY {{context: row.context}}]->(target)
                        )
                        FOREACH (_ IN CASE WHEN row.type = 'FAMILY' THEN [1] ELSE [] END |
                            MERGE (source)-[r:FAMILY {{context: row.context}}]->(target)
                        )
                    }}
                    IN TRANSACTIONS OF 1000 ROWS;
                """)
                return result.summary()
        
        def get_statistics(self):
            """获取统计信息"""
            with self.driver.session() as session:
                node_count = session.run("MATCH (n) RETURN count(n) AS count;").single()["count"]
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count;").single()["count"]
                return {"nodes": node_count, "relationships": rel_count}


def main():
    print("=" * 60)
    print("🔄 Neo4j 数据导入工具")
    print("=" * 60)
    print()
    
    # CSV 文件路径
    csv_dir = Path("graph_data")
    nodes_file = csv_dir / "nodes.csv"
    relationships_file = csv_dir / "relationships.csv"
    
    # 检查文件是否存在
    if not nodes_file.exists():
        print(f"❌ nodes.csv 不存在: {nodes_file}")
        return
    
    if not relationships_file.exists():
        print(f"❌ relationships.csv 不存在: {relationships_file}")
        return
    
    print(f"📂 CSV 文件:")
    print(f"   - {nodes_file}")
    print(f"   - {relationships_file}")
    print()
    
    # 检查环境变量
    if not NEO4J_PASSWORD or NEO4J_PASSWORD == "your_password":
        print("⚠️  请在 .env 文件中设置 NEO4J_PASSWORD")
        print()
        print("💡 解决方案:")
        print("   1. 创建 .env 文件")
        print("   2. 添加以下内容:")
        print("      NEO4J_URI=bolt://localhost:7687")
        print("      NEO4J_USERNAME=neo4j")
        print("      NEO4J_PASSWORD=你的Neo4j密码")
        return
    
    try:
        # 连接 Neo4j
        print(f"🔗 连接 Neo4j: {NEO4J_URI}")
        importer = Neo4jImporter(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        print("✅ 连接成功！")
        print()
        
        # 创建约束
        print("📝 创建约束...")
        importer.create_constraints()
        print("✅ 约束创建完成！")
        print()
        
        # 导入节点
        print("📥 导入节点...")
        importer.import_nodes(str(nodes_file))
        print("✅ 节点导入完成！")
        print()
        
        # 导入关系
        print("🔗 导入关系...")
        importer.import_relationships(str(relationships_file))
        print("✅ 关系导入完成！")
        print()
        
        # 获取统计信息
        stats = importer.get_statistics()
        print("=" * 60)
        print("📊 导入统计:")
        print("=" * 60)
        print(f"   • 节点数量: {stats['nodes']}")
        print(f"   • 关系数量: {stats['relationships']}")
        print()
        print("🎉 导入完成！")
        print()
        
        importer.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        print("💡 可能的原因:")
        print("   1. Neo4j 未启动")
        print("   2. 连接信息不正确")
        print("   3. CSV 文件路径不正确")
        print("   4. 缺少 neo4j 包")
        print()
        print("   安装 neo4j 包:")
        print("   pip install neo4j")


if __name__ == "__main__":
    main()
