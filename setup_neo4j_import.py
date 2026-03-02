import os
import shutil
from pathlib import Path
import glob

def find_neo4j_import_dir():
    """查找 Neo4j import 目录"""
    # Windows Neo4j Desktop 默认路径
    neo4j_base = Path.home() / ".neo4j" / "neo4jDatabases"
    
    if not neo4j_base.exists():
        print(f"❌ 未找到 Neo4j 数据库目录: {neo4j_base}")
        return None
    
    # 查找最新的数据库目录
    db_dirs = list(neo4j_base.glob("database-*"))
    if not db_dirs:
        print(f"❌ 未找到 Neo4j 数据库")
        return None
    
    # 选择最新的数据库
    latest_db = max(db_dirs, key=lambda x: x.stat().st_mtime)
    print(f"📁 找到 Neo4j 数据库: {latest_db}")
    
    # 查找 installation 目录
    install_dirs = list(latest_db.glob("installation-*"))
    if not install_dirs:
        print(f"❌ 未找到 installation 目录")
        return None
    
    latest_install = max(install_dirs, key=lambda x: x.stat().st_mtime)
    import_dir = latest_install / "import"
    
    print(f"📁 Neo4j import 目录: {import_dir}")
    return import_dir

def copy_csv_files(csv_dir: str, import_dir: Path):
    """复制 CSV 文件到 Neo4j import 目录"""
    csv_path = Path(csv_dir)
    
    if not csv_path.exists():
        print(f"❌ CSV 目录不存在: {csv_dir}")
        return False
    
    nodes_file = csv_path / "nodes.csv"
    relationships_file = csv_path / "relationships.csv"
    
    if not nodes_file.exists():
        print(f"❌ nodes.csv 不存在: {nodes_file}")
        return False
    
    if not relationships_file.exists():
        print(f"❌ relationships.csv 不存在: {relationships_file}")
        return False
    
    try:
        shutil.copy2(nodes_file, import_dir / "nodes.csv")
        shutil.copy2(relationships_file, import_dir / "relationships.csv")
        print(f"✅ CSV 文件已复制到 Neo4j import 目录")
        print(f"   - nodes.csv")
        print(f"   - relationships.csv")
        return True
    except Exception as e:
        print(f"❌ 复制文件失败: {e}")
        return False

def main():
    print("=" * 60)
    print("🔄 Neo4j CSV 文件复制工具")
    print("=" * 60)
    print()
    
    csv_dir = "graph_data"
    
    # 查找 Neo4j import 目录
    import_dir = find_neo4j_import_dir()
    
    if not import_dir:
        print()
        print("💡 手动设置方法:")
        print("   1. 打开 Neo4j Browser (http://localhost:7474)")
        print("   2. 运行以下命令查看 import 目录:")
        print("      CALL dbms.listConfig() YIELD name, value")
        print("      WHERE name = 'dbms.directories.import'")
        print("   3. 将 CSV 文件复制到显示的目录")
        return
    
    # 复制文件
    if copy_csv_files(csv_dir, import_dir):
        print()
        print("=" * 60)
        print("✅ 准备就绪！")
        print("=" * 60)
        print()
        print("下一步:")
        print("   1. 打开 Neo4j Browser: http://localhost:7474")
        print("   2. 登录 (用户名: neo4j, 密码: 你设置的密码)")
        print("   3. 复制并运行 graph_data/import_to_neo4j.cql 的内容")
        print()
    else:
        print()
        print("❌ 复制失败，请检查错误信息")

if __name__ == "__main__":
    main()
