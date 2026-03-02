"""
图构建器 - 从剧情数据自动构建关系图
"""
from typing import List, Dict
from langchain_core.documents import Document
from graph_module import StoryGraph, NodeType, EdgeType
import re


class GraphBuilder:
    """从剧情文档构建关系图"""
    
    def __init__(self):
        self.graph = StoryGraph()
        self.character_cache: Dict[str, str] = {}  # 角色名 -> 节点ID
        self.chapter_cache: Dict[str, str] = {}    # 章节名 -> 节点ID
        self.location_cache: Dict[str, str] = {}   # 地点名 -> 节点ID
    
    def build_from_documents(self, documents: List[Document]) -> StoryGraph:
        """从文档列表构建图"""
        print("🚀 开始构建剧情关系图...")
        
        # 第一步：提取所有实体（角色、章节、地点）
        self._extract_entities(documents)
        
        # 第二步：构建关系
        self._build_relationships(documents)
        
        # 第三步：计算权重
        self._calculate_weights()
        
        # 打印统计信息
        stats = self.graph.get_statistics()
        print(f"\n✅ 图构建完成!")
        print(f"   节点数: {stats['total_nodes']}")
        print(f"   边数: {stats['total_edges']}")
        print(f"   角色数: {stats['node_types'].get('character', 0)}")
        print(f"   章节数: {stats['node_types'].get('chapter', 0)}")
        
        return self.graph
    
    def _extract_entities(self, documents: List[Document]):
        """从文档中提取实体"""
        print("📊 提取实体...")
        
        for doc in documents:
            # 提取章节信息
            chapter = doc.metadata.get('chapter', '未知')
            act = doc.metadata.get('act', '未知')
            chapter_key = f"{chapter}_{act}"
            
            if chapter_key not in self.chapter_cache:
                chapter_id = f"chap_{len(self.chapter_cache)}"
                self.graph.add_node(
                    chapter_id,
                    NodeType.CHAPTER,
                    f"{chapter} - {act}",
                    {
                        'chapter': chapter,
                        'act': act,
                        'chapter_number': doc.metadata.get('chapter_number', 0),
                        'act_number': doc.metadata.get('act_number', 0)
                    }
                )
                self.chapter_cache[chapter_key] = chapter_id
            
            # 提取角色
            characters = doc.metadata.get('characters', [])
            for char_name in characters:
                if char_name not in self.character_cache:
                    char_id = f"char_{len(self.character_cache)}"
                    self.graph.add_node(
                        char_id,
                        NodeType.CHARACTER,
                        char_name,
                        {'first_appearance': chapter_key}
                    )
                    self.character_cache[char_name] = char_id
            
            # 提取地点（从内容中）
            locations = self._extract_locations(doc.page_content)
            for loc_name in locations:
                if loc_name not in self.location_cache:
                    loc_id = f"loc_{len(self.location_cache)}"
                    self.graph.add_node(
                        loc_id,
                        NodeType.LOCATION,
                        loc_name
                    )
                    self.location_cache[loc_name] = loc_id
    
    def _extract_locations(self, content: str) -> List[str]:
        """从内容中提取地点"""
        # 这里可以使用更复杂的NLP方法
        # 简单示例：匹配常见的地点关键词
        location_keywords = [
            "今州", "云陵谷", "商业区", "瑝珑", "黑海岸", "黎那汐塔", "拉海洛"
        ]
        
        found_locations = []
        for keyword in location_keywords:
            if keyword in content:
                found_locations.append(keyword)
        
        return found_locations
    
    def _build_relationships(self, documents: List[Document]):
        """构建实体之间的关系"""
        print("🔗 构建关系...")
        
        for doc in documents:
            chapter = doc.metadata.get('chapter', '未知')
            act = doc.metadata.get('act', '未知')
            chapter_key = f"{chapter}_{act}"
            chapter_id = self.chapter_cache.get(chapter_key)
            
            if not chapter_id:
                continue
            
            # 获取该章节的所有角色
            characters = doc.metadata.get('characters', [])
            char_ids = [self.character_cache.get(name) for name in characters 
                       if name in self.character_cache]
            
            # 1. 构建角色-章节关系（出现关系）
            for char_id in char_ids:
                self.graph.add_edge(
                    char_id,
                    chapter_id,
                    EdgeType.APPEARS_IN,
                    weight=1.0
                )
            
            # 2. 构建角色-角色关系（互动关系）
            # 如果多个角色在同一章节出现，认为他们有互动
            for i, char1_id in enumerate(char_ids):
                for char2_id in char_ids[i+1:]:
                    self.graph.add_edge(
                        char1_id,
                        char2_id,
                        EdgeType.INTERACTS_WITH,
                        weight=0.5,  # 基础权重
                        properties={'chapter': chapter_key}
                    )
            
            # 3. 构建角色-地点关系
            locations = self._extract_locations(doc.page_content)
            for loc_name in locations:
                loc_id = self.location_cache.get(loc_name)
                if loc_id:
                    for char_id in char_ids:
                        self.graph.add_edge(
                            char_id,
                            loc_id,
                            EdgeType.LOCATED_AT,
                            weight=0.3
                        )
    
    def _calculate_weights(self):
        """计算边的权重"""
        print("⚖️ 计算权重...")
        
        # 根据共同出现次数调整互动权重
        for char_id in self.graph.node_index[NodeType.CHARACTER]:
            # 获取该角色出现的所有章节
            chapters = set()
            for edge in self.graph.edges.get(char_id, []):
                if edge.type == EdgeType.APPEARS_IN:
                    chapters.add(edge.target)
            
            # 调整与其他角色的互动权重
            for edge in self.graph.edges.get(char_id, []):
                if edge.type == EdgeType.INTERACTS_WITH:
                    # 获取目标角色
                    target_id = edge.target
                    target_chapters = set()
                    for target_edge in self.graph.edges.get(target_id, []):
                        if target_edge.type == EdgeType.APPEARS_IN:
                            target_chapters.add(target_edge.target)
                    
                    # 计算共同出现次数
                    common_chapters = chapters & target_chapters
                    if common_chapters:
                        # 权重 = 基础权重 + 共同出现次数 * 系数
                        edge.weight = 0.5 + len(common_chapters) * 0.1
    
    def add_relationship(self, char1_name: str, char2_name: str, 
                        relation_type: str, description: str = ""):
        """手动添加角色关系"""
        char1_id = self.character_cache.get(char1_name)
        char2_id = self.character_cache.get(char2_name)
        
        if not char1_id or not char2_id:
            print(f"❌ 角色不存在: {char1_name} 或 {char2_name}")
            return
        
        self.graph.add_edge(
            char1_id,
            char2_id,
            EdgeType.RELATIONSHIP,
            weight=1.0,
            properties={
                'relation_type': relation_type,
                'description': description
            }
        )
        print(f"✅ 添加关系: {char1_name} -{relation_type}-> {char2_name}")
    
    def query_character_network(self, character_name: str) -> Dict:
        """查询角色的关系网络"""
        char_id = self.character_cache.get(character_name)
        if not char_id:
            return {}
        
        return self.graph.get_character_relationships(char_id)
    
    def find_character_connection(self, char1_name: str, char2_name: str) -> List[List[str]]:
        """查找两个角色之间的关系路径"""
        char1_id = self.character_cache.get(char1_name)
        char2_id = self.character_cache.get(char2_name)
        
        if not char1_id or not char2_id:
            return []
        
        paths = self.graph.find_path(char1_id, char2_id, max_depth=3)
        
        # 将节点ID转换为名称
        named_paths = []
        for path in paths:
            named_path = [self.graph.nodes[node_id].name for node_id in path]
            named_paths.append(named_path)
        
        return named_paths
    
    def export_graph(self, filepath: str):
        """导出图数据"""
        self.graph.export_to_json(filepath)
    
    def import_graph(self, filepath: str):
        """导入图数据"""
        self.graph.import_from_json(filepath)
        
        # 重建缓存
        self.character_cache.clear()
        self.chapter_cache.clear()
        self.location_cache.clear()
        
        for node_id, node in self.graph.nodes.items():
            if node.type == NodeType.CHARACTER:
                self.character_cache[node.name] = node_id
            elif node.type == NodeType.CHAPTER:
                self.chapter_cache[node.name] = node_id
            elif node.type == NodeType.LOCATION:
                self.location_cache[node.name] = node_id


# 使用示例
if __name__ == "__main__":
    from data_preparation import DataPreparationModule
    
    # 加载数据
    data_module = DataPreparationModule("md_output")
    documents = data_module.load_documents()
    
    # 构建图
    builder = GraphBuilder()
    graph = builder.build_from_documents(documents)
    
    # 查询角色关系
    print("\n" + "="*50)
    print("📊 角色关系查询示例")
    print("="*50)
    
    # 查询漂泊者的关系网络
    if "漂泊者" in builder.character_cache:
        relationships = builder.query_character_network("漂泊者")
        print(f"\n🎭 漂泊者的关系网络:")
        print(f"   出现的章节: {len(relationships.get('appears_in', []))} 个")
        print(f"   互动的角色: {len(relationships.get('interacts_with', []))} 个")
        print(f"   出现的地点: {len(relationships.get('located_at', []))} 个")
    
    # 查找两个角色的关系路径
    if "漂泊者" in builder.character_cache and "秧秧" in builder.character_cache:
        paths = builder.find_character_connection("漂泊者", "秧秧")
        print(f"\n🔗 漂泊者和秧秧的关系路径:")
        for i, path in enumerate(paths[:3], 1):
            print(f"   路径{i}: {' -> '.join(path)}")
    
    # 导出图数据
    builder.export_graph("story_graph.json")
    print("\n✅ 图数据已导出到 story_graph.json")