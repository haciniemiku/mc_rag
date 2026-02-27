from typing import List, Dict, Any
from langchain_core.documents import Document
from pathlib import Path
import uuid
import re
from langchain_text_splitters import MarkdownHeaderTextSplitter

# 章节映射表
CHAPTER_MAPPING = {
    "序章": ["万象新声 · 上", "万象新声 · 下"],
    "第一章": ["嘤鸣初相召", "撞金止行阵", "奔策候残星", 
             "庭际刀刃鸣", "欲知天将雨", "千里卷戎旌 · 上", 
             "千里卷戎旌 · 下", "行路遇新知", "往岁乘霄醒惊蛰"],
    "第二章": ["如一叶小舟穿行于茫茫海洋", "那神圣微风时常吹入", 
             "夜与昼，均请摘下面纱", "昔我悲伤，今却歌唱", "老人鱼海", 
             "圣者，忤逆者，告死者", "荣耀暗面", "燃烧的心", 
             "捕梦于神秘园中", "铁锈，剑与烈阳", "灼我以烈阳", 
             "今夜，注定属于月亮", "已逝的必将归来", "暗潮将映的黎明", 
             "独在异乡为异客", "行至海岸尽头", "曙光停摆于荒地之上", 
             "星光流转于眼眸之间"],
    "第三章": ["未知的既感", "冰原下的星炬", "致第二次日出", "远航星"]
}


class DataPreparationModule:
    """数据准备模块 - 负责数据加载、清洗和预处理"""

    def __init__(self, data_path: str):
        self.data_path = data_path
        self.documents: List[Document] = []
        self.chunks: List[Document] = []
        self.parent_child_map: Dict[str, str] = {}

    def load_documents(self) -> List[Document]:
        """加载文档数据"""
        documents = []
        data_path_obj = Path(self.data_path)

        if not data_path_obj.exists():
            raise FileNotFoundError(f"数据路径不存在：{self.data_path}")

        print(f"📂 开始扫描目录：{self.data_path} ...")

        for md_file in data_path_obj.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not content.strip():
                    continue

                parent_id = str(uuid.uuid4())

                doc = Document(
                    page_content=content,
                    metadata={
                        "source": str(md_file),
                        "file_name": md_file.name,
                        "parent_id": parent_id,
                        "doc_type": "parent"
                    }
                )
                documents.append(doc)
            except Exception as e:
                print(f"⚠️ 读取文件失败 {md_file}: {e}")

        # 增强元数据
        print(f"✨ 正在增强 {len(documents)} 个文档的元数据...")
        success_count = 0
        for i, doc in enumerate(documents):
            self._enhance_metadata(doc)
            chars = doc.metadata.get("characters", [])
            if chars:
                success_count += 1

            # 打印前 5 个文件的结果
            if i < 5:
                chapter = doc.metadata.get("chapter", "未知")
                act = doc.metadata.get("act", "未知")
                print(
                    f"   📄 [{doc.metadata['file_name']}] 章节：{chapter} | 幕：{act} | 提取到角色 ({len(chars)}): {chars[:5]}{'...' if len(chars) > 5 else ''}")
                # 打印完整元数据
                print(f"      完整元数据: {doc.metadata}")

        self.documents = documents
        print(f"✅ 加载完成。共 {len(documents)} 个父文档，其中 {success_count} 个提取到角色。")
        return documents

    def _enhance_metadata(self, doc: Document):
        """增强文档元数据：提取角色、章节和幕信息"""
        characters = self._get_characters(doc)
        
        # 提取章节和幕信息
        chapter_info = self._get_chapter_info(doc.page_content, doc.metadata.get('file_name', ''))
        
        doc.metadata["characters"] = characters
        doc.metadata["character_count"] = len(characters)
        doc.metadata["chapter"] = chapter_info["chapter"]  # 添加章节信息
        doc.metadata["chapter_number"] = chapter_info["chapter_number"]  # 章节编号
        doc.metadata["act"] = chapter_info["act"]  # 幕信息
        doc.metadata["act_number"] = chapter_info["act_number"]  # 幕编号

        # 保留 series (文件夹名)
        source_path = Path(doc.metadata.get('source', ''))
        if source_path.parent.name and source_path.parent.name != 'md_output':
            doc.metadata["series"] = source_path.parent.name
        else:
            doc.metadata["series"] = source_path.stem

    def _get_chapter_info(self, content: str, file_name: str) -> dict:
        """从内容和文件名中提取章节和幕信息"""
        # 初始化默认值
        chapter = "未知"
        chapter_number = 0
        act = "未知"
        act_number = 0
        
        # 首先从文件名匹配
        for chap_name, act_list in CHAPTER_MAPPING.items():
            for act_name in act_list:
                if act_name in file_name:
                    chapter = chap_name
                    act = act_name
                    
                    # 提取章节编号
                    if chap_name == "序章":
                        chapter_number = 0
                    elif "第一章" in chap_name:
                        chapter_number = 1
                    elif "第二章" in chap_name:
                        chapter_number = 2
                    elif "第三章" in chap_name:
                        chapter_number = 3
                    
                    # 提取幕编号
                    # 简化处理，根据文件名顺序分配幕编号
                    act_number = act_list.index(act_name) + 1
                    
                    return {
                        "chapter": chapter,
                        "chapter_number": chapter_number,
                        "act": act,
                        "act_number": act_number
                    }
        
        # 如果文件名匹配失败，尝试从内容中提取
        # 这里可以添加更复杂的逻辑来从内容中识别章节
        
        return {
            "chapter": chapter,
            "chapter_number": chapter_number,
            "act": act,
            "act_number": act_number
        }

    def _get_characters(self, doc: Document) -> List[str]:
        """获取去重后的角色列表"""
        content = doc.page_content

        pattern = r'([\u4e00-\u9fa5]{2,})\s*[\u003a\uff1a]'
        raw_matches = re.findall(pattern, content)

        blacklist = {"注意", "提示", "总结", "心肺复苏"}
        cleaned_chars = [name for name in raw_matches if name not in blacklist]

        return sorted(list(set(cleaned_chars)))

    def chunk_documents(self) -> List[Document]:
        """Markdown 结构感知分块"""
        if not self.documents:
            raise ValueError("请先加载文档")

        chunks = self._markdown_header_split()

        for i, chunk in enumerate(chunks):
            if 'chunk_id' not in chunk.metadata:
                chunk.metadata['chunk_id'] = str(uuid.uuid4())
            chunk.metadata['batch_index'] = i
            chunk.metadata['chunk_size'] = len(chunk.page_content)

        self.chunks = chunks
        return chunks

    def _markdown_header_split(self) -> List[Document]:
        """使用 Markdown 标题分割器进行结构化分割，并增强子块元数据"""
        headers_to_split_on = [
            ("#", "主标题"),
            ("##", "二级标题")
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )

        all_chunks = []

        for doc in self.documents:
            md_chunks = markdown_splitter.split_text(doc.page_content)
            parent_id = doc.metadata["parent_id"]
            parent_chars = doc.metadata.get("characters", [])
            parent_chapter = doc.metadata.get("chapter", "未知")
            parent_chapter_number = doc.metadata.get("chapter_number", 0)
            parent_act = doc.metadata.get("act", "未知")
            parent_act_number = doc.metadata.get("act_number", 0)

            for i, chunk in enumerate(md_chunks):
                # 过滤空块
                if not chunk.page_content or len(chunk.page_content.strip()) < 10:
                    continue

                child_id = str(uuid.uuid4())
                chunk.metadata.update(doc.metadata)

                # 提取局部角色
                local_chars = self._get_characters_from_text(chunk.page_content)

                chunk.metadata.update({
                    "chunk_id": child_id,
                    "parent_id": parent_id,
                    "doc_type": "child",
                    "chunk_index": i,
                    "local_characters": local_chars,
                    "local_character_count": len(local_chars),
                    "chapter": parent_chapter,
                    "chapter_number": parent_chapter_number,
                    "act": parent_act,
                    "act_number": parent_act_number
                })

                self.parent_child_map[child_id] = parent_id
                all_chunks.append(chunk)

                # 打印前 5 个子块的元数据
                if len(all_chunks) <= 5:
                    print(f"   🧩 子块 {len(all_chunks)} 元数据: {chunk.metadata}")

        print(f"✂️  切分完成：共生成 {len(all_chunks)} 个有效片段 (已添加局部角色标签)。")
        return all_chunks

    def _get_characters_from_text(self, text: str) -> List[str]:
        """专门用于提取短文本中的角色列表"""
        if not text:
            return []
        pattern = r'([\u4e00-\u9fa5]{2,})\s*[\u003a\uff1a]'
        raw_matches = re.findall(pattern, text)
        blacklist = {"注意", "提示", "总结", "心肺复苏"}
        cleaned_chars = [name for name in raw_matches if name not in blacklist]
        return sorted(list(set(cleaned_chars)))

    def get_parent_documents(self, child_chunks: List[Document]) -> List[Document]:
        """根据子块获取对应的父文档（智能去重）"""
        # 统计每个父文档被匹配的次数（相关性指标）
        parent_relevance = {}
        parent_docs_map = {}

        # 收集所有相关的父文档ID和相关性分数
        for chunk in child_chunks:
            parent_id = chunk.metadata.get("parent_id")
            if parent_id:
                # 增加相关性计数
                parent_relevance[parent_id] = parent_relevance.get(parent_id, 0) + 1

                # 缓存父文档（避免重复查找）
                if parent_id not in parent_docs_map:
                    for doc in self.documents:
                        if doc.metadata.get("parent_id") == parent_id:
                            parent_docs_map[parent_id] = doc
                            break

        # 按相关性排序并构建去重后的父文档列表
        sorted_parent_ids = sorted(parent_relevance.keys(),
                                   key=lambda x: parent_relevance[x], reverse=True)

        # 构建去重后的父文档列表
        parent_docs = []
        for parent_id in sorted_parent_ids:
            if parent_id in parent_docs_map:
                parent_docs.append(parent_docs_map[parent_id])

        return parent_docs


# ==========================================
# 🧪 自动化测试单元 (Main)
# ==========================================
if __name__ == "__main__":
    target_dir = "md_output"

    print("🚀 开始运行数据准备模块自动化测试...\n")

    try:
        loader = DataPreparationModule(target_dir)

        # --- Test 1: 加载文档 ---
        print("--- [Test 1] 加载文档与全局角色提取 ---")
        docs = loader.load_documents()

        # 断言 1: 必须加载到文档
        assert len(docs) > 0, "❌ 测试失败：未加载到任何文档，请检查 md_output 目录是否存在且包含 .md 文件"
        print(f"✅ 通过：成功加载 {len(docs)} 个文档")

        # 断言 2: 第一个文档必须有角色
        first_doc = docs[0]
        chars = first_doc.metadata.get('characters', [])
        assert len(chars) > 0, f"❌ 测试失败：第一个文档 '{first_doc.metadata['file_name']}' 未提取到任何角色"
        print(f"✅ 通过：第一个文档提取到角色 {chars}")

        # 断言 3: 必须包含 series 元数据
        assert 'series' in first_doc.metadata, "❌ 测试失败：缺少 'series' 元数据"
        print(f"✅ 通过：系列名称提取正确 '{first_doc.metadata['series']}'")

        # 断言 4: 必须包含章节相关元数据
        assert 'chapter' in first_doc.metadata, "❌ 测试失败：缺少 'chapter' 元数据"
        assert 'chapter_number' in first_doc.metadata, "❌ 测试失败：缺少 'chapter_number' 元数据"
        assert 'act' in first_doc.metadata, "❌ 测试失败：缺少 'act' 元数据"
        assert 'act_number' in first_doc.metadata, "❌ 测试失败：缺少 'act_number' 元数据"
        print(f"✅ 通过：章节信息提取正确 - 章节：{first_doc.metadata['chapter']} (编号：{first_doc.metadata['chapter_number']}) | 幕：{first_doc.metadata['act']} (编号：{first_doc.metadata['act_number']})")

        # --- Test 2: 文档切分 ---
        print("\n--- [Test 2] 文档切分与局部角色 ---")
        chunks = loader.chunk_documents()

        # 断言 5: 必须生成切片
        assert len(chunks) > 0, "❌ 测试失败：未生成任何 Chunk"
        print(f"✅ 通过：成功生成 {len(chunks)} 个片段")

        # 断言 6: 检查父子映射
        first_chunk = chunks[0]
        c_id = first_chunk.metadata['chunk_id']
        p_id = first_chunk.metadata['parent_id']

        assert c_id in loader.parent_child_map, "❌ 测试失败：Chunk ID 未在 parent_child_map 中注册"
        assert loader.parent_child_map[c_id] == p_id, "❌ 测试失败：父子映射关系不一致"
        print(f"✅ 通过：父子映射关系正确 (Chunk: {c_id[:8]}... -> Parent: {p_id[:8]}...)")

        # 断言 7: 检查局部角色 (local_characters)
        local_chars = first_chunk.metadata.get('local_characters', [])
        # 注意：有些纯旁白的 chunk 可能没有角色，所以这里只验证字段存在，或者如果有角色则验证类型
        assert 'local_characters' in first_chunk.metadata, "❌ 测试失败：Chunk 缺少 'local_characters' 字段"
        assert isinstance(local_chars, list), "❌ 测试失败：'local_characters' 必须是列表"

        # 尝试找一个有角色的 chunk 进行深度验证
        chunk_with_chars = next((c for c in chunks if len(c.metadata.get('local_characters', [])) > 0), None)
        if chunk_with_chars:
            l_chars = chunk_with_chars.metadata['local_characters']
            g_chars = chunk_with_chars.metadata['characters']  # 全局
            # 局部角色应该是全局角色的子集
            is_subset = all(c in g_chars for c in l_chars)
            assert is_subset, f"❌ 测试失败：局部角色 {l_chars} 不全是全局角色 {g_chars} 的子集"
            print(f"✅ 通过：局部角色逻辑正确 (示例：{l_chars})")
        else:
            print("⚠️ 警告：所有 Chunk 均未提取到局部角色（可能是数据全为旁白）")

        # 断言 8: 检查子块是否继承了章节信息
        assert 'chapter' in first_chunk.metadata, "❌ 测试失败：Chunk 缺少 'chapter' 元数据"
        assert 'chapter_number' in first_chunk.metadata, "❌ 测试失败：Chunk 缺少 'chapter_number' 元数据"
        assert 'act' in first_chunk.metadata, "❌ 测试失败：Chunk 缺少 'act' 元数据"
        assert 'act_number' in first_chunk.metadata, "❌ 测试失败：Chunk 缺少 'act_number' 元数据"
        print(f"✅ 通过：子块继承章节信息正确 - 章节：{first_chunk.metadata['chapter']} | 幕：{first_chunk.metadata['act']}")

        # --- Test 3: 元数据完整性 ---
        print("\n--- [Test 3] 元数据完整性检查 ---")
        required_keys = ['source', 'file_name', 'parent_id', 'doc_type', 'series', 'characters', 'chunk_id',
                         'local_characters', 'chapter', 'chapter_number', 'act', 'act_number']
        missing_keys = [k for k in required_keys if k not in first_chunk.metadata]

        assert not missing_keys, f"❌ 测试失败：Chunk 元数据缺失关键键：{missing_keys}"
        print(f"✅ 通过：所有关键元数据字段均已存在")

        print("\n" + "=" * 50)
        print("🎉 所有测试通过！数据准备模块运行正常。")
        print("=" * 50)
        print(f"📊 最终统计:")
        print(f"   - 父文档数：{len(docs)}")
        print(f"   - 子片段数：{len(chunks)}")
        print(f"   - 平均每个文档切分：{len(chunks) / len(docs):.2f} 个片段")

    except AssertionError as e:
        print("\n" + "=" * 50)
        print("❌ 测试失败 (Assertion Error)")
        print(f"   原因：{e}")
        print("=" * 50)
        exit(1)  # 非零退出码表示失败

    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ 测试运行出错 (Exception)")
        print(f"   错误信息：{e}")
        print("=" * 50)
        import traceback

        traceback.print_exc()
        exit(1)