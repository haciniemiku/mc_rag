import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from neo4j import GraphDatabase
except ImportError:
    print("⚠️ 请安装 neo4j 包: pip install neo4j")
    GraphDatabase = None


class Neo4jGraphRetrieval:
    """基于 Neo4j 图数据库的检索模块"""
    
    def __init__(self, uri: str = None, username: str = None, password: str = None):
        """初始化 Neo4j 连接"""
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        
        if not self.password or self.password == "your_password":
            print("⚠️ 警告: 请在 .env 文件中设置 NEO4J_PASSWORD")
            self.driver = None
        elif GraphDatabase:
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
                print("✅ Neo4j 连接成功")
            except Exception as e:
                print(f"❌ Neo4j 连接失败: {e}")
                self.driver = None
        else:
            self.driver = None
    
    def close(self):
        """关闭 Neo4j 连接"""
        if self.driver:
            self.driver.close()
    
    def _execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """执行 Neo4j 查询"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"❌ Neo4j 查询执行失败: {e}")
            return []
    
    def query_character_info(self, character_name: str) -> Optional[Dict]:
        """查询角色详细信息"""
        query = """
        MATCH (c:Character {name: $name})
        RETURN c.id AS id,
               c.name AS name,
               c.description AS description,
               c.aliases AS aliases,
               c.first_seen_chapter AS first_seen_chapter,
               c.first_seen_act AS first_seen_act,
               c.occurrence_count AS occurrence_count
        """
        results = self._execute_query(query, {"name": character_name})
        return results[0] if results else None
    
    def query_character_relationships(self, character_name: str, relationship_type: str = None) -> List[Dict]:
        """查询角色的关系"""
        if relationship_type:
            query = """
            MATCH (c:Character {name: $name})-[r]->(target)
            WHERE type(r) = $rel_type
            RETURN type(r) AS relationship_type,
                   r.context AS context,
                   r.chapter AS chapter,
                   r.weight AS weight,
                   labels(target)[0] AS target_type,
                   target.name AS target_name
            ORDER BY r.weight DESC
            """
            results = self._execute_query(query, {
                "name": character_name,
                "rel_type": relationship_type
            })
        else:
            query = """
            MATCH (c:Character {name: $name})-[r]->(target)
            RETURN type(r) AS relationship_type,
                   r.context AS context,
                   r.chapter AS chapter,
                   r.weight AS weight,
                   labels(target)[0] AS target_type,
                   target.name AS target_name
            ORDER BY r.weight DESC
            """
            results = self._execute_query(query, {"name": character_name})
        
        return results
    
    def query_character_appears_in(self, character_name: str) -> List[Dict]:
        """查询角色出现的章节"""
        query = """
        MATCH (c:Character {name: $name})-[:APPEARS_IN]->(ch:Chapter)
        RETURN ch.name AS chapter_name,
               ch.chapter_number AS chapter_number,
               ch.act_number AS act_number,
               ch.act_number AS act_name
        ORDER BY ch.chapter_number, ch.act_number
        """
        results = self._execute_query(query, {"name": character_name})
        return results
    
    def query_character_locations(self, character_name: str) -> List[Dict]:
        """查询角色出现的地点"""
        query = """
        MATCH (c:Character {name: $name})-[:LOCATED_AT]->(l:Location)
        RETURN l.name AS location_name,
               l.description AS description,
               count(*) AS times
        ORDER BY times DESC
        """
        results = self._execute_query(query, {"name": character_name})
        return results
    
    def query_character_interactions(self, character_name: str) -> List[Dict]:
        """查询角色的互动关系"""
        query = """
        MATCH (c:Character {name: $name})-[r:INTERACTS_WITH]->(other:Character)
        RETURN other.name AS character_name,
               r.context AS context,
               r.chapter AS chapter,
               r.weight AS weight
        ORDER BY r.weight DESC
        """
        results = self._execute_query(query, {"name": character_name})
        return results
    
    def query_character_enemies(self, character_name: str) -> List[Dict]:
        """查询角色的敌人"""
        query = """
        MATCH (c:Character {name: $name})-[r:ENEMY]->(enemy:Character)
        RETURN enemy.name AS enemy_name,
               r.context AS context,
               r.chapter AS chapter
        """
        results = self._execute_query(query, {"name": character_name})
        return results
    
    def query_character_allies(self, character_name: str) -> List[Dict]:
        """查询角色的盟友"""
        query = """
        MATCH (c:Character {name: $name})-[r:ALLY]->(ally:Character)
        RETURN ally.name AS ally_name,
               r.context AS context,
               r.chapter AS chapter
        """
        results = self._execute_query(query, {"name": character_name})
        return results
    
    def query_character_owns(self, character_name: str) -> List[Dict]:
        """查询角色拥有的物品"""
        query = """
        MATCH (c:Character {name: $name})-[r:OWNS]->(item:Item)
        RETURN item.name AS item_name,
               r.context AS context
        """
        results = self._execute_query(query, {"name": character_name})
        return results
    
    def query_character_organizations(self, character_name: str) -> List[Dict]:
        """查询角色所属组织"""
        query = """
        MATCH (c:Character {name: $name})-[r:MEMBER_OF]->(org:Organization)
        RETURN org.name AS organization_name,
               r.context AS context
        """
        results = self._execute_query(query, {"name": character_name})
        return results
    
    def query_character_family(self, character_name: str) -> List[Dict]:
        """查询角色的家庭成员"""
        query = """
        MATCH (c:Character {name: $name})-[r:FAMILY]->(family:Character)
        RETURN family.name AS family_name,
               r.context AS context
        """
        results = self._execute_query(query, {"name": character_name})
        return results
    
    def query_character_network(self, character_name: str) -> Dict:
        """查询角色的完整关系网络"""
        network = {
            "character": character_name,
            "relationships": [],
            "interactions": [],
            "enemies": [],
            "allies": [],
            "locations": [],
            "items": [],
            "organizations": [],
            "family": []
        }
        
        # 获取基本信息
        info = self.query_character_info(character_name)
        if info:
            network["info"] = info
        
        # 获取各种关系
        relationships = self.query_character_relationships(character_name)
        if relationships:
            network["relationships"] = relationships
        
        # 获取互动关系
        interactions = self.query_character_interactions(character_name)
        if interactions:
            network["interactions"] = interactions
        
        # 获取敌人
        enemies = self.query_character_enemies(character_name)
        if enemies:
            network["enemies"] = enemies
        
        # 获取盟友
        allies = self.query_character_allies(character_name)
        if allies:
            network["allies"] = allies
        
        # 获取地点
        locations = self.query_character_locations(character_name)
        if locations:
            network["locations"] = locations
        
        # 获取物品
        items = self.query_character_owns(character_name)
        if items:
            network["items"] = items
        
        # 获取组织
        organizations = self.query_character_organizations(character_name)
        if organizations:
            network["organizations"] = organizations
        
        # 获取家庭
        family = self.query_character_family(character_name)
        if family:
            network["family"] = family
        
        return network
    
    def query_character_first_appearance(self, character_name: str) -> Optional[Dict]:
        """查询角色首次出现"""
        query = """
        MATCH (c:Character {name: $name})-[:APPEARS_IN]->(ch:Chapter)
        RETURN ch.name AS chapter_name,
               ch.chapter_number AS chapter_number,
               ch.act_number AS act_number,
               ch.act_number AS act_name
        ORDER BY ch.chapter_number, ch.act_number
        LIMIT 1
        """
        results = self._execute_query(query, {"name": character_name})
        return results[0] if results else None
    
    def query_character_last_appearance(self, character_name: str) -> Optional[Dict]:
        """查询角色最后一次出现"""
        query = """
        MATCH (c:Character {name: $name})-[:APPEARS_IN]->(ch:Chapter)
        RETURN ch.name AS chapter_name,
               ch.chapter_number AS chapter_number,
               ch.act_number AS act_number,
               ch.act_number AS act_name
        ORDER BY ch.chapter_number DESC, ch.act_number DESC
        LIMIT 1
        """
        results = self._execute_query(query, {"name": character_name})
        return results[0] if results else None
    
    def query_relationship_between_characters(self, char1: str, char2: str) -> List[Dict]:
        """查询两个角色之间的关系"""
        query = """
        MATCH (c1:Character {name: $name1})-[r]-(c2:Character {name: $name2})
        RETURN type(r) AS relationship_type,
               r.context AS context,
               r.chapter AS chapter,
               r.weight AS weight
        """
        results = self._execute_query(query, {"name1": char1, "name2": char2})
        return results
    
    def query_characters_in_chapter(self, chapter_number: int, act_number: int = None) -> List[Dict]:
        """查询某章节中的所有角色"""
        if act_number is not None:
            query = """
            MATCH (c:Character)-[:APPEARS_IN]->(ch:Chapter {chapter_number: $chapter, act_number: $act})
            RETURN c.name AS character_name, c.occurrence_count AS occurrence_count
            ORDER BY c.occurrence_count DESC
            """
            results = self._execute_query(query, {"chapter": chapter_number, "act": act_number})
        else:
            query = """
            MATCH (c:Character)-[:APPEARS_IN]->(ch:Chapter {chapter_number: $chapter})
            RETURN c.name AS character_name, c.occurrence_count AS occurrence_count
            ORDER BY c.occurrence_count DESC
            """
            results = self._execute_query(query, {"chapter": chapter_number})
        return results
    
    def query_characters_in_location(self, location_name: str) -> List[Dict]:
        """查询某地点出现的所有角色"""
        query = """
        MATCH (c:Character)-[:LOCATED_AT]->(l:Location {name: $name})
        RETURN c.name AS character_name, c.occurrence_count AS occurrence_count
        ORDER BY c.occurrence_count DESC
        """
        results = self._execute_query(query, {"name": location_name})
        return results
    
    def get_statistics(self) -> Dict:
        """获取图数据库统计信息"""
        query = """
        MATCH (n)
        WITH labels(n)[0] AS type, count(n) AS count
        RETURN type, count
        """
        node_stats = self._execute_query(query)
        
        query = """
        MATCH ()-[r]->()
        WITH type(r) AS type, count(r) AS count
        RETURN type, count
        """
        rel_stats = self._execute_query(query)
        
        return {
            "node_types": {stat["type"]: stat["count"] for stat in node_stats},
            "relationship_types": {stat["type"]: stat["count"] for stat in rel_stats}
        }


def main():
    """测试 Neo4j 图检索"""
    print("=" * 60)
    print("🧪 Neo4j 图检索测试")
    print("=" * 60)
    print()
    
    # 初始化
    retriever = Neo4jGraphRetrieval()
    
    if not retriever.driver:
        print("❌ Neo4j 连接失败，请检查配置")
        return
    
    # 测试查询
    test_character = "秧秧"
    
    print(f"🔍 查询角色: {test_character}")
    print()
    
    # 1. 基本信息
    info = retriever.query_character_info(test_character)
    if info:
        print("📋 基本信息:")
        print(f"   ID: {info.get('id')}")
        print(f"   名称: {info.get('name')}")
        print(f"   描述: {info.get('description')}")
        print(f"   首次出现: {info.get('first_seen_chapter')} {info.get('first_seen_act')}")
        print(f"   出现次数: {info.get('occurrence_count')}")
        print()
    
    # 2. 关系网络
    network = retriever.query_character_network(test_character)
    
    if network.get("relationships"):
        print(f"🤝 关系网络 (共 {len(network['relationships'])} 个关系):")
        for rel in network["relationships"][:5]:
            rel_type = rel.get("relationship_type", "unknown")
            target = rel.get("target_name", "unknown")
            context = rel.get("context", "")
            print(f"   - {rel_type}: {target}")
            print(f"     {context}")
        print()
    
    # 3. 互动角色
    if network.get("interactions"):
        print(f"💬 互动角色 (共 {len(network['interactions'])} 个):")
        for interaction in network["interactions"][:5]:
            char = interaction.get("character_name", "unknown")
            context = interaction.get("context", "")
            print(f"   - {char}: {context}")
        print()
    
    # 4. 出现地点
    if network.get("locations"):
        print(f"📍 出现地点 (共 {len(network['locations'])} 个):")
        for loc in network["locations"][:5]:
            name = loc.get("location_name", "unknown")
            times = loc.get("times", 0)
            print(f"   - {name} (出现 {times} 次)")
        print()
    
    # 5. 统计信息
    stats = retriever.get_statistics()
    print("📊 图数据库统计:")
    print(f"   节点类型: {stats['node_types']}")
    print(f"   关系类型: {stats['relationship_types']}")
    
    retriever.close()
    print()
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
