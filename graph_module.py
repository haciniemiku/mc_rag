"""
图数据模块 - 用于构建和分析剧情关系图
"""
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class NodeType(Enum):
    """节点类型"""
    CHARACTER = "character"      # 角色
    CHAPTER = "chapter"          # 章节
    EVENT = "event"              # 事件
    LOCATION = "location"        # 地点


class EdgeType(Enum):
    """边类型"""
    APPEARS_IN = "appears_in"           # 出现在
    INTERACTS_WITH = "interacts_with"   # 互动
    LOCATED_AT = "located_at"           # 位于
    HAPPENS_IN = "happens_in"           # 发生在
    RELATIONSHIP = "relationship"       # 关系


@dataclass
class Node:
    """图节点"""
    id: str
    type: NodeType
    name: str
    properties: Dict = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Node):
            return self.id == other.id
        return False


@dataclass
class Edge:
    """图边"""
    source: str          # 源节点ID
    target: str          # 目标节点ID
    type: EdgeType       # 边类型
    weight: float = 1.0  # 权重
    properties: Dict = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.source, self.target, self.type.value))
    
    def __eq__(self, other):
        if isinstance(other, Edge):
            return (self.source == other.source and 
                   self.target == other.target and 
                   self.type == other.type)
        return False


class StoryGraph:
    """剧情关系图"""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}           # 节点字典
        self.edges: Dict[str, List[Edge]] = {}     # 邻接表
        self.node_index: Dict[NodeType, Set[str]] = {  # 按类型索引
            node_type: set() for node_type in NodeType
        }
    
    def add_node(self, node_id: str, node_type: NodeType, name: str, 
                 properties: Dict = None) -> Node:
        """添加节点"""
        if node_id in self.nodes:
            print(f"⚠️ 节点 {node_id} 已存在，跳过添加")
            return self.nodes[node_id]
        
        node = Node(
            id=node_id,
            type=node_type,
            name=name,
            properties=properties or {}
        )
        
        self.nodes[node_id] = node
        self.node_index[node_type].add(node_id)
        self.edges[node_id] = []
        
        print(f"✅ 添加节点: {name} ({node_type.value})")
        return node
    
    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType,
                 weight: float = 1.0, properties: Dict = None) -> Edge:
        """添加边"""
        if source_id not in self.nodes:
            print(f"❌ 源节点 {source_id} 不存在")
            return None
        
        if target_id not in self.nodes:
            print(f"❌ 目标节点 {target_id} 不存在")
            return None
        
        edge = Edge(
            source=source_id,
            target=target_id,
            type=edge_type,
            weight=weight,
            properties=properties or {}
        )
        
        # 检查是否已存在
        existing_edges = self.edges.get(source_id, [])
        if edge in existing_edges:
            print(f"⚠️ 边已存在，跳过添加")
            return edge
        
        self.edges[source_id].append(edge)
        print(f"✅ 添加边: {source_id} -> {target_id} ({edge_type.value})")
        return edge
    
    def get_neighbors(self, node_id: str, edge_type: EdgeType = None) -> List[Tuple[Node, Edge]]:
        """获取邻居节点"""
        if node_id not in self.nodes:
            return []
        
        neighbors = []
        for edge in self.edges.get(node_id, []):
            if edge_type is None or edge.type == edge_type:
                target_node = self.nodes.get(edge.target)
                if target_node:
                    neighbors.append((target_node, edge))
        
        return neighbors
    
    def find_path(self, start_id: str, end_id: str, 
                  max_depth: int = 5) -> List[List[str]]:
        """查找两个节点之间的路径（BFS）"""
        if start_id not in self.nodes or end_id not in self.nodes:
            return []
        
        paths = []
        visited = set()
        queue = [(start_id, [start_id])]
        
        while queue and len(paths) < 10:  # 限制路径数量
            current_id, path = queue.pop(0)
            
            if current_id == end_id:
                paths.append(path)
                continue
            
            if len(path) >= max_depth:
                continue
            
            visited.add(current_id)
            
            for edge in self.edges.get(current_id, []):
                next_id = edge.target
                if next_id not in visited:
                    queue.append((next_id, path + [next_id]))
        
        return paths
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """获取特定类型的所有节点"""
        node_ids = self.node_index.get(node_type, set())
        return [self.nodes[node_id] for node_id in node_ids if node_id in self.nodes]
    
    def get_character_relationships(self, character_id: str) -> Dict:
        """获取角色的关系网络"""
        if character_id not in self.nodes:
            return {}
        
        relationships = {
            'appears_in': [],      # 出现的章节
            'interacts_with': [],  # 互动的角色
            'located_at': [],      # 出现的地点
            'relationships': []    # 其他关系
        }
        
        for edge in self.edges.get(character_id, []):
            target_node = self.nodes.get(edge.target)
            if not target_node:
                continue
            
            if edge.type == EdgeType.APPEARS_IN:
                relationships['appears_in'].append({
                    'chapter': target_node.name,
                    'weight': edge.weight
                })
            elif edge.type == EdgeType.INTERACTS_WITH:
                relationships['interacts_with'].append({
                    'character': target_node.name,
                    'weight': edge.weight,
                    'details': edge.properties
                })
            elif edge.type == EdgeType.LOCATED_AT:
                relationships['located_at'].append({
                    'location': target_node.name,
                    'weight': edge.weight
                })
            elif edge.type == EdgeType.RELATIONSHIP:
                relationships['relationships'].append({
                    'target': target_node.name,
                    'type': edge.properties.get('relation_type', 'unknown'),
                    'weight': edge.weight
                })
        
        return relationships
    
    def find_cooccurrence(self, character1_id: str, character2_id: str) -> List[Node]:
        """查找两个角色共同出现的章节"""
        # 获取角色1出现的所有章节
        chapters1 = set()
        for edge in self.edges.get(character1_id, []):
            if edge.type == EdgeType.APPEARS_IN:
                chapters1.add(edge.target)
        
        # 获取角色2出现的所有章节
        chapters2 = set()
        for edge in self.edges.get(character2_id, []):
            if edge.type == EdgeType.APPEARS_IN:
                chapters2.add(edge.target)
        
        # 求交集
        common_chapters = chapters1 & chapters2
        return [self.nodes[ch_id] for ch_id in common_chapters if ch_id in self.nodes]
    
    def export_to_json(self, filepath: str):
        """导出图为JSON格式"""
        data = {
            'nodes': [
                {
                    'id': node.id,
                    'type': node.type.value,
                    'name': node.name,
                    'properties': node.properties
                }
                for node in self.nodes.values()
            ],
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'type': edge.type.value,
                    'weight': edge.weight,
                    'properties': edge.properties
                }
                for edges in self.edges.values()
                for edge in edges
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 图数据已导出到: {filepath}")
    
    def import_from_json(self, filepath: str):
        """从JSON导入图数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 清空现有数据
        self.nodes.clear()
        self.edges.clear()
        for node_type in NodeType:
            self.node_index[node_type].clear()
        
        # 导入节点
        for node_data in data.get('nodes', []):
            self.add_node(
                node_id=node_data['id'],
                node_type=NodeType(node_data['type']),
                name=node_data['name'],
                properties=node_data.get('properties', {})
            )
        
        # 导入边
        for edge_data in data.get('edges', []):
            self.add_edge(
                source_id=edge_data['source'],
                target_id=edge_data['target'],
                edge_type=EdgeType(edge_data['type']),
                weight=edge_data.get('weight', 1.0),
                properties=edge_data.get('properties', {})
            )
        
        print(f"✅ 图数据已从 {filepath} 导入")
    
    def get_statistics(self) -> Dict:
        """获取图的统计信息"""
        return {
            'total_nodes': len(self.nodes),
            'total_edges': sum(len(edges) for edges in self.edges.values()),
            'node_types': {
                node_type.value: len(self.node_index[node_type])
                for node_type in NodeType
            }
        }


# 使用示例
if __name__ == "__main__":
    # 创建图
    graph = StoryGraph()
    
    # 添加角色节点
    graph.add_node("char_1", NodeType.CHARACTER, "漂泊者", {"description": "主角"})
    graph.add_node("char_2", NodeType.CHARACTER, "秧秧", {"description": "女主角"})
    graph.add_node("char_3", NodeType.CHARACTER, "炽霞", {"description": "巡尉"})
    
    # 添加章节节点
    graph.add_node("chap_1", NodeType.CHAPTER, "第一章", {"number": 1})
    graph.add_node("chap_2", NodeType.CHAPTER, "第二章", {"number": 2})
    
    # 添加地点节点
    graph.add_node("loc_1", NodeType.LOCATION, "今州", {"description": "主城"})
    
    # 添加关系边
    graph.add_edge("char_1", "chap_1", EdgeType.APPEARS_IN, weight=1.0)
    graph.add_edge("char_2", "chap_1", EdgeType.APPEARS_IN, weight=1.0)
    graph.add_edge("char_1", "char_2", EdgeType.INTERACTS_WITH, weight=0.8, 
                   properties={"scene": "初次相遇"})
    graph.add_edge("char_1", "loc_1", EdgeType.LOCATED_AT, weight=1.0)
    
    # 查询角色关系
    relationships = graph.get_character_relationships("char_1")
    print(f"\n📊 漂泊者的关系网络:")
    print(json.dumps(relationships, ensure_ascii=False, indent=2))
    
    # 查找共同出现的章节
    cooccurrence = graph.find_cooccurrence("char_1", "char_2")
    print(f"\n🤝 漂泊者和秧秧共同出现的章节:")
    for chapter in cooccurrence:
        print(f"  - {chapter.name}")
    
    # 获取统计信息
    stats = graph.get_statistics()
    print(f"\n📈 图统计信息:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))