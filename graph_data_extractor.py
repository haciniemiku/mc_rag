import os
import json
import csv
import time
from typing import List, Dict, Any, Tuple
from pathlib import Path
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()


class GraphDataExtractor:
    def __init__(self, model_name: str = "moonshot-v1-8k", output_dir: str = "graph_data"):
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            max_tokens=4000,
            openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.moonshot.cn/v1"),
            openai_api_key=os.getenv("MOONSHOT_API_KEY")
        )
        
        self.nodes: Dict[str, Dict] = {}
        self.relationships: List[Dict] = []
        self.node_id_map: Dict[str, str] = {}
        
    def extract_from_documents(self, documents: List[Document], batch_size: int = 5) -> Tuple[List[Dict], List[Dict]]:
        print(f"🔍 开始从 {len(documents)} 个文档中提取图数据...")
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            print(f"📦 处理批次 {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}...")
            
            for doc in batch:
                try:
                    self._extract_from_document(doc)
                    time.sleep(1)
                except Exception as e:
                    print(f"⚠️ 处理文档失败: {doc.metadata.get('file_name', 'unknown')}, 错误: {e}")
                    continue
        
        print(f"✅ 提取完成！共 {len(self.nodes)} 个节点，{len(self.relationships)} 个关系")
        return list(self.nodes.values()), self.relationships
    
    def _extract_from_document(self, doc: Document):
        content = doc.page_content[:3000]
        metadata = doc.metadata
        
        chapter = metadata.get('chapter', '未知')
        act = metadata.get('act', '未知')
        chapter_number = metadata.get('chapter_number', 0)
        act_number = metadata.get('act_number', 0)
        
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的剧情数据提取专家。请从给定的游戏剧情文本中提取实体和关系。

**实体类型**：
1. Character（角色）：剧情中出现的人物
2. Location（地点）：故事发生的场所
3. Event（事件）：重要的剧情事件
4. Item（物品）：关键道具或物品
5. Organization（组织）：势力、团体或组织

**关系类型**：
1. APPEARS_IN：角色出现在章节中
2. LOCATED_AT：角色/事件位于某地点
3. INTERACTS_WITH：角色之间的互动
4. PARTICIPATES_IN：角色参与事件
5. RELATES_TO：实体之间的关联
6. OWNS：角色拥有物品
7. MEMBER_OF：角色属于组织
8. ALLY：同盟关系
9. ENEMY：敌对关系
10. FAMILY：家庭关系

**输出格式**（JSON）：
{{
  "entities": [
    {{
      "name": "实体名称",
      "type": "Character/Location/Event/Item/Organization",
      "properties": {{
        "description": "简短描述",
        "aliases": ["别名1", "别名2"]
      }}
    }}
  ],
  "relations": [
    {{
      "source": "源实体名称",
      "target": "目标实体名称",
      "type": "关系类型",
      "properties": {{
        "context": "关系上下文",
        "chapter": "章节信息"
      }}
    }}
  ]
}}

**注意事项**：
1. 只提取明确提到的实体和关系，不要推测
2. 角色名称要准确，注意区分同名角色
3. 关系要有明确的上下文支持
4. 输出必须是有效的JSON格式"""),
            ("user", """章节信息：第{chapter_number}章《{chapter}》第{act_number}幕《{act}》

剧情文本：
{content}

请提取实体和关系（JSON格式）：""")
        ])
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                chain = extraction_prompt | self.llm
                result = chain.invoke({
                    "chapter_number": chapter_number,
                    "chapter": chapter,
                    "act_number": act_number,
                    "act": act,
                    "content": content
                })
                
                result_text = result.content.strip()
                
                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.startswith("```"):
                    result_text = result_text[3:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
                
                data = json.loads(result_text)
                
                self._process_extracted_data(data, chapter, act, chapter_number, act_number)
                break
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON解析失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                print(f"❌ 文档 {metadata.get('file_name', 'unknown')} 提取失败，跳过")
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "overloaded" in error_msg.lower():
                    print(f"⚠️ API限流，等待{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                print(f"❌ 提取失败: {e}")
                break
    
    def _process_extracted_data(self, data: Dict, chapter: str, act: str, chapter_number: int, act_number: int):
        entities = data.get('entities', [])
        relations = data.get('relations', [])
        
        for entity in entities:
            name = entity.get('name', '').strip()
            entity_type = entity.get('type', 'Character')
            properties = entity.get('properties', {})
            
            if not name:
                continue
            
            node_key = f"{entity_type}_{name}"
            
            if node_key not in self.nodes:
                node_id = f"{entity_type.lower()}_{len(self.nodes)}"
                self.node_id_map[name] = node_id
                
                self.nodes[node_key] = {
                    'id': node_id,
                    'name': name,
                    'type': entity_type,
                    'description': properties.get('description', ''),
                    'aliases': '|'.join(properties.get('aliases', [])),
                    'first_seen_chapter': f"第{chapter_number}章",
                    'first_seen_act': f"第{act_number}幕",
                    'occurrence_count': 1
                }
            else:
                self.nodes[node_key]['occurrence_count'] += 1
        
        chapter_node_key = f"Chapter_第{chapter_number}章_{act}"
        if chapter_node_key not in self.nodes:
            chapter_node_id = f"chapter_{len(self.nodes)}"
            self.nodes[chapter_node_key] = {
                'id': chapter_node_id,
                'name': f"第{chapter_number}章《{chapter}》第{act_number}幕《{act}》",
                'type': 'Chapter',
                'description': f'{chapter} - {act}',
                'chapter_number': chapter_number,
                'act_number': act_number,
                'aliases': '',
                'occurrence_count': 1
            }
        
        for relation in relations:
            source_name = relation.get('source', '').strip()
            target_name = relation.get('target', '').strip()
            relation_type = relation.get('type', 'RELATES_TO')
            properties = relation.get('properties', {})
            
            if not source_name or not target_name:
                continue
            
            source_id = self.node_id_map.get(source_name)
            target_id = self.node_id_map.get(target_name)
            
            if not source_id:
                source_id = f"entity_{len(self.nodes)}"
                self.node_id_map[source_name] = source_id
                self.nodes[f"Entity_{source_name}"] = {
                    'id': source_id,
                    'name': source_name,
                    'type': 'Entity',
                    'description': '',
                    'aliases': '',
                    'occurrence_count': 1
                }
            
            if not target_id:
                target_id = f"entity_{len(self.nodes)}"
                self.node_id_map[target_name] = target_id
                self.nodes[f"Entity_{target_name}"] = {
                    'id': target_id,
                    'name': target_name,
                    'type': 'Entity',
                    'description': '',
                    'aliases': '',
                    'occurrence_count': 1
                }
            
            self.relationships.append({
                'source_id': source_id,
                'source_name': source_name,
                'target_id': target_id,
                'target_name': target_name,
                'type': relation_type,
                'context': properties.get('context', ''),
                'chapter': f"第{chapter_number}章",
                'act': f"第{act_number}幕",
                'weight': 1.0
            })
    
    def save_to_csv(self):
        nodes_file = self.output_dir / "nodes.csv"
        relationships_file = self.output_dir / "relationships.csv"
        
        print(f"💾 保存节点到 {nodes_file}...")
        with open(nodes_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['id', 'name', 'type', 'description', 'aliases', 'first_seen_chapter', 'first_seen_act', 'occurrence_count', 'chapter_number', 'act_number']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.nodes.values())
        
        print(f"💾 保存关系到 {relationships_file}...")
        with open(relationships_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['source_id', 'source_name', 'target_id', 'target_name', 'type', 'context', 'chapter', 'act', 'weight']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.relationships)
        
        print(f"✅ 数据已保存！")
        print(f"   📊 节点数: {len(self.nodes)}")
        print(f"   🔗 关系数: {len(self.relationships)}")
        
        return nodes_file, relationships_file
    
    def generate_neo4j_cypher(self, output_file: str = "import_to_neo4j.cql"):
        cypher_file = self.output_dir / output_file
        
        print(f"📝 生成Neo4j Cypher脚本...")
        
        cypher_lines = [
            "// Neo4j 数据导入脚本",
            "// 生成时间: " + time.strftime("%Y-%m-%d %H:%M:%S"),
            "",
            "// 清理现有数据（可选）",
            "// MATCH (n) DETACH DELETE n;",
            "",
            "// 创建约束和索引",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Character) REQUIRE c.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (ch:Chapter) REQUIRE ch.id IS UNIQUE;",
            "",
            "// 导入节点数据",
            f"LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row",
            "CALL {",
            "  WITH row",
            "  FOREACH (_ IN CASE WHEN row.type = 'Character' THEN [1] ELSE [] END |",
            "    CREATE (n:Character {",
            "      id: row.id,",
            "      name: row.name,",
            "      description: row.description,",
            "      aliases: row.aliases,",
            "      first_seen_chapter: row.first_seen_chapter,",
            "      first_seen_act: row.first_seen_act,",
            "      occurrence_count: toInteger(row.occurrence_count)",
            "    })",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'Location' THEN [1] ELSE [] END |",
            "    CREATE (n:Location {",
            "      id: row.id,",
            "      name: row.name,",
            "      description: row.description,",
            "      aliases: row.aliases",
            "    })",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'Event' THEN [1] ELSE [] END |",
            "    CREATE (n:Event {",
            "      id: row.id,",
            "      name: row.name,",
            "      description: row.description",
            "    })",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'Item' THEN [1] ELSE [] END |",
            "    CREATE (n:Item {",
            "      id: row.id,",
            "      name: row.name,",
            "      description: row.description",
            "    })",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'Organization' THEN [1] ELSE [] END |",
            "    CREATE (n:Organization {",
            "      id: row.id,",
            "      name: row.name,",
            "      description: row.description",
            "    })",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'Chapter' THEN [1] ELSE [] END |",
            "    CREATE (n:Chapter {",
            "      id: row.id,",
            "      name: row.name,",
            "      chapter_number: toInteger(row.chapter_number),",
            "      act_number: toInteger(row.act_number)",
            "    })",
            "  )",
            "} IN TRANSACTIONS OF 1000 ROWS;",
            "",
            "// 导入关系数据",
            f"LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row",
            "CALL {",
            "  WITH row",
            "  MATCH (source {id: row.source_id})",
            "  MATCH (target {id: row.target_id})",
            "  FOREACH (_ IN CASE WHEN row.type = 'APPEARS_IN' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:APPEARS_IN {context: row.context, chapter: row.chapter, weight: toFloat(row.weight)}]->(target)",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'LOCATED_AT' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:LOCATED_AT {context: row.context}]->(target)",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'INTERACTS_WITH' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:INTERACTS_WITH {context: row.context, chapter: row.chapter, weight: toFloat(row.weight)}]->(target)",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'PARTICIPATES_IN' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:PARTICIPATES_IN {context: row.context}]->(target)",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'RELATES_TO' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:RELATES_TO {context: row.context}]->(target)",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'OWNS' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:OWNS {context: row.context}]->(target)",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'MEMBER_OF' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:MEMBER_OF {context: row.context}]->(target)",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'ALLY' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:ALLY {context: row.context}]->(target)",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'ENEMY' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:ENEMY {context: row.context}]->(target)",
            "  )",
            "  FOREACH (_ IN CASE WHEN row.type = 'FAMILY' THEN [1] ELSE [] END |",
            "    CREATE (source)-[:FAMILY {context: row.context}]->(target)",
            "  )",
            "} IN TRANSACTIONS OF 1000 ROWS;",
            "",
            "// 验证导入结果",
            "MATCH (n) RETURN count(n) AS node_count;",
            "MATCH ()-[r]->() RETURN count(r) AS relationship_count;"
        ]
        
        with open(cypher_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cypher_lines))
        
        print(f"✅ Cypher脚本已生成: {cypher_file}")
        return cypher_file


def main():
    from data_preparation import DataPreparationModule
    
    print("🚀 开始图数据提取流程...")
    
    data_prep = DataPreparationModule("md_output")
    documents = data_prep.load_documents()
    
    extractor = GraphDataExtractor(
        model_name="moonshot-v1-8k",
        output_dir="graph_data"
    )
    
    nodes, relationships = extractor.extract_from_documents(documents, batch_size=3)
    
    nodes_file, relationships_file = extractor.save_to_csv()
    cypher_file = extractor.generate_neo4j_cypher()
    
    print("\n" + "="*60)
    print("🎉 图数据提取完成！")
    print("="*60)
    print(f"📊 生成的文件：")
    print(f"   - 节点数据: {nodes_file}")
    print(f"   - 关系数据: {relationships_file}")
    print(f"   - Neo4j脚本: {cypher_file}")
    print("\n📖 使用说明：")
    print("1. 将 nodes.csv 和 relationships.csv 复制到 Neo4j 的 import 目录")
    print("2. 在 Neo4j Browser 中运行 import_to_neo4j.cql 脚本")
    print("3. 或使用 neo4j-admin database load full 命令导入")


if __name__ == "__main__":
    main()
