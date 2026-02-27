import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from data_preparation import DataPreparationModule
from index_construction import IndexConstructionModule
from retrieval_optimization import RetrievalOptimizationModule
from generation_integration import GenerationIntegrationModule
from config import RAGConfig, DEFAULT_CONFIG

load_dotenv()


class RAGSystem:
    """剧情 RAG 系统"""

    def __init__(self, config: RAGConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.data_module = None
        self.index_module = None
        self.retrieval_module = None
        self.generation_module = None

        # 检查数据路径和 API 密钥
        if not Path(self.config.data_path).exists():
            print(f"⚠️ 警告：数据路径不存在：{self.config.data_path}，请确保先运行数据准备脚本。")

        if not os.getenv("MOONSHOT_API_KEY"):
            raise ValueError("❌ 错误：请设置 MOONSHOT_API_KEY 环境变量 (例如在 .env 文件中)")

    def initialize_system(self):
        """初始化所有模块"""
        print("🔧 正在初始化系统模块...")

        # 1. 初始化数据准备模块
        self.data_module = DataPreparationModule(self.config.data_path)

        # 2. 初始化索引构建模块
        self.index_module = IndexConstructionModule(
            model_name=self.config.embedding_model,
            index_save_path=self.config.index_save_path
        )

        # 3. 初始化生成集成模块
        self.generation_module = GenerationIntegrationModule(
            model_name=self.config.llm_model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        print("✅ 系统模块初始化完成。")

    def build_knowledge_base(self):
        """构建知识库"""
        print("📚 正在构建/加载知识库...")

        # 1. 尝试加载已保存的索引
        vectorstore = self.index_module.load_index()

        if vectorstore is not None:
            print("💾 检测到已有索引，直接加载。")
            # 加载已有索引，但仍需要文档和分块用于检索模块
            self.data_module.load_documents()
            chunks = self.data_module.chunk_documents()
            # 将加载的 vectorstore 赋值给 index_module 以便后续使用
            self.index_module.vectorstore = vectorstore
        else:
            print("🆕 未检测到索引，开始从头构建...")
            # 构建新索引的完整流程
            self.data_module.load_documents()
            chunks = self.data_module.chunk_documents()
            vectorstore = self.index_module.build_vector_index(chunks)
            self.index_module.save_index()

        # 初始化检索优化模块
        self.retrieval_module = RetrievalOptimizationModule(
            vectorstore=vectorstore,
            chunks=chunks,
        )

        print(f"✅ 知识库构建完成。共 {len(chunks)} 个片段。")

    def ask_question(self, question: str, stream: bool = False) -> str:
        """回答用户问题"""
        if not self.retrieval_module:
            return "❌ 系统未初始化，请先构建知识库。"

        # 1. 查询重写
        rewritten_question = self.generation_module.rewrite_query(question)

        # 2. 使用LLM提取结构化实体信息
        entities = self.generation_module.extract_structured_entities(question)
        print(f"🔍 提取到的结构化实体: {entities}")
        
        character_name = entities.get('character', '')
        location = entities.get('location', '')
        chapter = entities.get('chapter', '')
        action = entities.get('action', '')
        time = entities.get('time', '')
        
        print(f"🔍 角色名称: {character_name}, 地点: {location}, 章节: {chapter}, 动作: {action}, 时间: {time}")
        
        # 检查是否是角色首次/最后出现的问题
        is_character_occurrence = (action in ['出现', '登场'] and time in ['首次', '第一次', '最后一次', '最后'])
        
        if is_character_occurrence and character_name:
            # 过滤掉常见的非角色词汇
            common_words = ["游戏", "剧情", "章节", "幕", "首次", "第一次", "最后一次", "最后", "出现", "登场", "哪里", "什么", "在"]
            if character_name not in common_words:
                occurrence_type = "first" if time in ["首次", "第一次"] else "last"
                print(f"🔍 调用角色出现检索: {character_name}, 类型: {occurrence_type}")
                
                # 调用角色出现检索
                occurrence_chunks = self.retrieval_module.character_occurrence_search(character_name, occurrence_type)
                print(f"🔍 检索结果数量: {len(occurrence_chunks)}")
                if occurrence_chunks:
                    # 提取章节和幕信息
                    chunk = occurrence_chunks[0]
                    chapter = chunk.metadata.get('chapter', '未知')
                    act = chunk.metadata.get('act', '未知')
                    chapter_number = chunk.metadata.get('chapter_number', 0)
                    act_number = chunk.metadata.get('act_number', 0)
                    
                    # 构建详细的回答
                    occurrence_desc = "首次" if occurrence_type == "first" else "最后一次"
                    return f"{character_name}在游戏中{occurrence_desc}出现是在第{chapter_number}章《{chapter}》的第{act_number}幕《{act}》。"
                else:
                    print(f"❌ 未找到角色 {character_name} 的出现，继续使用常规检索流程")
            else:
                print(f"⚠️ 角色名称 {character_name} 在常见词列表中，跳过角色出现检索")
        else:
            if not character_name:
                print(f"⚠️ 未提取到角色名称，继续使用常规检索流程")
            elif not is_character_occurrence:
                print(f"⚠️ 不是角色出现类问题，继续使用常规检索流程")

        # 3. 查询路由 (判断意图)
        route_type = self.generation_module.query_router(rewritten_question)
        print(f"🔍 意图识别结果：{route_type}")

        # 4. 处理剧情无关性问答
        if route_type == 'general':
            return "我是鸣潮剧情RAG助手，专门回答关于鸣潮游戏剧情的问题。我可以帮你查询角色信息、剧情事件、章节内容等。请问我关于鸣潮剧情的问题！"

        # 5. 检索相关子块
        relevant_chunks = self.retrieval_module.hybrid_search(
            rewritten_question,
            top_k=self.config.top_k,
        )

        if not relevant_chunks:
            return "😕 抱歉，我在知识库中没有找到相关信息。"

        # 6. 根据路由类型后处理上下文
        context_text = ""
        system_prompt = ""

        if route_type == 'factual':
            # 📋 事实性问题：直接基于检索结果回答
            system_prompt = "你是一个剧情问答助手。请根据提供的剧本片段，准确回答用户的问题。只回答明确在剧本中出现的信息，不要进行推测或编造。"
            context_text = self._format_context(relevant_chunks, mode="factual")

        elif route_type == 'inferential':
            # 🧠 推理性问题：需要基于剧情进行分析和推理
            # 对于推理性问题，增加检索的top_k值
            relevant_chunks = self.retrieval_module.hybrid_search(
                rewritten_question,
                top_k=self.config.top_k * 2,  # 获取更多上下文
            )
            
            system_prompt = "你是一个剧情分析助手。请根据提供的剧本片段，分析角色关系、情感倾向和可能的剧情发展。基于已有信息进行合理推理，但明确区分事实和推测。"
            context_text = self._format_context(relevant_chunks, mode="inferential")

        else:  # general
            # 🌐 通用模式
            system_prompt = "你是一个博学的助手。请根据提供的背景知识回答用户问题。如果知识库中没有答案，请诚实告知，不要编造。"
            context_text = self._format_context(relevant_chunks, mode="general")

        # 7. 调用 LLM 生成回答
        response = self.generation_module.generate(
            question=question,
            context=context_text,
            system_prompt=system_prompt,
            stream=stream
        )

        return response

    def _format_context(self, chunks: List, mode: str = "general") -> str:
        """将 Document 列表格式化为字符串上下文"""
        formatted_lines = []

        for i, chunk in enumerate(chunks):
            meta = chunk.metadata
            content = chunk.page_content

            # 构建来源标记
            source_info = f"[来源：{meta.get('file_name', 'Unknown')}"

            # 添加章节信息
            if meta.get('chapter') and meta.get('chapter') != '未知':
                source_info += f" | 章节：{meta.get('chapter')}"

            # 添加幕信息
            if meta.get('act') and meta.get('act') != '未知':
                source_info += f" | 幕：{meta.get('act')}"

            # 根据模式添加额外信息
            if mode == 'factual' and meta.get('local_characters'):
                source_info += f" | 角色：{', '.join(meta['local_characters'])}"
            elif mode == 'inferential':
                # 推理性模式显示更多元数据
                if meta.get('local_characters'):
                    source_info += f" | 角色：{', '.join(meta['local_characters'])}"
                if meta.get('二级标题'):
                    source_info += f" | 标题：{meta.get('二级标题')}"

            source_info += "]"

            formatted_lines.append(f"{source_info}\n{content}")
            formatted_lines.append("-" * 30)

        return "\n".join(formatted_lines)

    def run_interactive(self):
        """运行交互式问答循环"""
        print("\n" + "=" * 50)
        print("🎮 鸣潮剧情 RAG 助手已启动！")
        print("💡 输入 'quit' 或 'exit' 退出系统。")
        print("=" * 50 + "\n")

        while True:
            try:
                user_input = input("🙋 你: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 再见！祝你游戏愉快！")
                    break

                print("🤖 思考中...", end="\r")
                answer = self.ask_question(user_input, stream=False)

                print("\n" + "-" * 30)
                print(f"🤖 助手: {answer}")
                print("-" * 30 + "\n")

            except KeyboardInterrupt:
                print("\n👋 强制退出。再见！")
                break
            except Exception as e:
                print(f"\n❌ 发生错误：{e}")
                print("请重试或检查系统日志。")


def main():
    """主函数"""
    try:
        # 创建 RAG 系统
        rag_system = RAGSystem()

        # 初始化模块
        rag_system.initialize_system()

        # 构建/加载知识库
        rag_system.build_knowledge_base()

        # 运行交互式问答
        rag_system.run_interactive()

    except Exception as e:
        print(f"💥 系统启动失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()