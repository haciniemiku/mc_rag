import os
from dotenv import load_dotenv

load_dotenv()

def test_neo4j_integration():
    """测试 Neo4j 集成"""
    print("=" * 60)
    print("🧪 Neo4j 集成测试")
    print("=" * 60)
    print()
    
    # 检查环境变量
    if not os.getenv("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD") == "your_neo4j_password_here":
        print("⚠️  请在 .env 文件中设置 NEO4J_PASSWORD")
        print()
        print("💡 解决方案:")
        print("   1. 复制 .env.example 到 .env")
        print("   2. 修改 NEO4J_PASSWORD 为你的 Neo4j 密码")
        print()
        return False
    
    try:
        from graph_neo4j_retrieval import Neo4jGraphRetrieval
        
        print("🔗 连接 Neo4j...")
        retriever = Neo4jGraphRetrieval()
        
        if not retriever.driver:
            print("❌ Neo4j 连接失败")
            return False
        
        print("✅ Neo4j 连接成功！")
        print()
        
        # 测试查询
        test_character = "秧秧"
        
        print(f"🔍 测试查询角色: {test_character}")
        print()
        
        # 1. 基本信息
        info = retriever.query_character_info(test_character)
        if info:
            print("📋 基本信息:")
            print(f"   • 名称: {info.get('name')}")
            print(f"   • 描述: {info.get('description')}")
            print(f"   • 首次出现: {info.get('first_seen_chapter')} {info.get('first_seen_act')}")
            print(f"   • 出现次数: {info.get('occurrence_count')}")
            print()
        
        # 2. 关系网络
        network = retriever.query_character_network(test_character)
        
        if network.get("relationships"):
            print(f"🔗 关系网络 (共 {len(network['relationships'])} 个关系):")
            for rel in network["relationships"][:3]:
                rel_type = rel.get("relationship_type", "unknown")
                target = rel.get("target_name", "unknown")
                print(f"   • {rel_type}: {target}")
            print()
        
        # 3. 互动角色
        if network.get("interactions"):
            print(f"💬 互动角色 (共 {len(network['interactions'])} 个):")
            for interaction in network["interactions"][:3]:
                char = interaction.get("character_name", "unknown")
                context = interaction.get("context", "")
                print(f"   • {char}: {context}")
            print()
        
        # 4. 出现地点
        if network.get("locations"):
            print(f"📍 出现地点 (共 {len(network['locations'])} 个):")
            for loc in network["locations"][:3]:
                name = loc.get("location_name", "unknown")
                times = loc.get("times", 0)
                print(f"   • {name} (出现 {times} 次)")
            print()
        
        # 5. 统计信息
        stats = retriever.get_statistics()
        print("📊 图数据库统计:")
        print(f"   节点类型: {stats['node_types']}")
        print(f"   关系类型: {stats['relationship_types']}")
        print()
        
        retriever.close()
        
        print("=" * 60)
        print("✅ Neo4j 集成测试完成！")
        print("=" * 60)
        print()
        print("💡 现在可以运行 main.py 测试完整功能:")
        print("   python main.py")
        print()
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print()
        print("💡 解决方案:")
        print("   pip install neo4j")
        print()
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_neo4j_integration()
    exit(0 if success else 1)
