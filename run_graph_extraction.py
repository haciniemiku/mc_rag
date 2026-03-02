import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data_preparation import DataPreparationModule
from graph_data_extractor import GraphDataExtractor
from dotenv import load_dotenv

load_dotenv()


def main():
    print("=" * 70)
    print("🕸️  鸣潮剧情知识图谱提取工具")
    print("=" * 70)
    print()
    
    data_path = "md_output"
    output_dir = "graph_data"
    
    if not os.getenv("MOONSHOT_API_KEY"):
        print("❌ 错误：请设置 MOONSHOT_API_KEY 环境变量")
        print("   可以在 .env 文件中设置：MOONSHOT_API_KEY=your_api_key")
        return
    
    print(f"📂 数据源目录: {data_path}")
    print(f"📁 输出目录: {output_dir}")
    print()
    
    print("阶段 1/3: 加载文档数据...")
    print("-" * 70)
    data_prep = DataPreparationModule(data_path)
    documents = data_prep.load_documents()
    
    if not documents:
        print("❌ 错误：未加载到任何文档")
        return
    
    print()
    print("阶段 2/3: 使用LLM提取实体和关系...")
    print("-" * 70)
    print("⚠️  注意：此过程可能需要较长时间，取决于文档数量和API响应速度")
    print()
    
    batch_size = 3
    extractor = GraphDataExtractor(
        model_name="moonshot-v1-8k",
        output_dir=output_dir
    )
    
    nodes, relationships = extractor.extract_from_documents(documents, batch_size=batch_size)
    
    print()
    print("阶段 3/3: 生成CSV和Cypher脚本...")
    print("-" * 70)
    nodes_file, relationships_file = extractor.save_to_csv()
    cypher_file = extractor.generate_neo4j_cypher()
    
    print()
    print("=" * 70)
    print("🎉 知识图谱提取完成！")
    print("=" * 70)
    print()
    print("📊 提取统计:")
    print(f"   • 节点数量: {len(nodes)}")
    print(f"   • 关系数量: {len(relationships)}")
    print()
    print("📁 生成的文件:")
    print(f"   • 节点数据: {nodes_file}")
    print(f"   • 关系数据: {relationships_file}")
    print(f"   • Neo4j脚本: {cypher_file}")
    print()
    print("📖 导入到Neo4j的步骤:")
    print("   1. 确保 Neo4j 数据库已启动")
    print("   2. 将 nodes.csv 和 relationships.csv 复制到 Neo4j 的 import 目录:")
    print("      - Windows: %NEO4J_HOME%\\import\\")
    print("      - Linux/Mac: $NEO4J_HOME/import/")
    print("   3. 在 Neo4j Browser 中运行 import_to_neo4j.cql 脚本")
    print("      或使用命令: neo4j-admin database load full")
    print()
    print("💡 提示:")
    print("   - 可以在 Neo4j Browser 中使用 Cypher 查询图数据")
    print("   - 示例查询: MATCH (c:Character) RETURN c LIMIT 25")
    print("   - 示例查询: MATCH (c:Character)-[r:INTERACTS_WITH]->(c2) RETURN c, r, c2")
    print()


if __name__ == "__main__":
    main()
