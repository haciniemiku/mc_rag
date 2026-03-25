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
        self.conversation_history = []  # 多轮对话历史

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

        # 1. 构建多轮对话上下文
        context_text = self._build_conversation_context()
        
        # 2. 统一查询分析（一次大模型调用完成查询重写、结构化信息提取、意图判断）
        analysis_result = self.generation_module.analyze_query(question, context_text)
        
        # 从分析结果中提取信息
        rewritten_question = analysis_result.get('rewritten_query', question)
        entities = analysis_result.get('entities', {})
        route_type = analysis_result.get('route_type', 'general')
        is_character_occurrence = analysis_result.get('is_character_occurrence', False)
        character_name = analysis_result.get('character_name', '')
        action = analysis_result.get('action', '')
        time = analysis_result.get('time', '')
        
        print(f"🔍 分析结果:")
        print(f"   - 重写查询: {rewritten_question}")
        print(f"   - 意图类型: {route_type}")
        print(f"   - 实体信息: {entities}")
        print(f"   - 角色: {character_name}, 动作: {action}, 时间: {time}")
        
        # 3. 处理剧情无关性问答
        if route_type == 'general':
            return "我是鸣潮剧情RAG助手，专门回答关于鸣潮游戏剧情的问题。我可以帮你查询角色信息、剧情事件、章节内容等。请问我关于鸣潮剧情的问题！"
        
        # 4. 检索相关子块
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

        # 保存对话历史
        self.conversation_history.append({
            'question': question,
            'answer': response
        })

        return response

    def _build_conversation_context(self, max_turns: int = 5) -> str:
        """构建多轮对话上下文"""
        if not self.conversation_history:
            return ""
        
        # 只保留最近的 max_turns 轮对话
        recent_history = self.conversation_history[-max_turns:]
        
        context_parts = []
        for i, chat in enumerate(recent_history, 1):
            context_parts.append(f"第{i}轮:")
            context_parts.append(f"用户: {chat['question']}")
            context_parts.append(f"助手: {chat['answer']}")
            context_parts.append("")
        
        return "\n".join(context_parts)

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