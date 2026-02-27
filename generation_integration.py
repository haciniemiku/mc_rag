

class GenerationIntegrationModule:
    """生成集成模块 - 负责LLM集成和回答生成"""

    def __init__(self, model_name: str = "kimi-k2-0711-preview",
                 temperature: float = 0.1, max_tokens: int = 2048):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = None
        self.setup_llm()

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    # 假设你已经初始化了 self.llm (例如 ChatOpenAI, ChatGLM, QwenChat 等)
    # from langchain_openai import ChatOpenAI
    # self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    def query_router(self, query: str) -> str:
        """
        查询路由 - 根据用户问题自动分类为 'chapter', 'character', 或 'general'
        """

        # 1. 定义 Prompt 模板 (补全了示例和说明)
        router_prompt = ChatPromptTemplate.from_template("""
    你是一个智能查询分类助手。请分析用户的问题，将其归类为以下三种类型之一：

    1. 'chapter' (章节/剧情查询): 
       - 用户询问特定章节、地点、剧情事件或故事进展。
       - 关键词示例："哪一章", "剧情", "发生在...", "之后发生了什么", "北落峡谷", "悬浮废墟"。
       - 例子："忌炎在北落峡谷遇到了什么？", "第二章讲了什么？", "故事最后结局如何？"

    2. 'character' (角色查询): 
       - 用户询问特定角色的台词、性格、关系或具体说了什么。
       - 关键词示例："谁说的", "...的台词", "...的性格", "忌炎", "秧秧", "角色关系"。
       - 例子："炽霞说过哪些搞笑的话？", "忌炎和秧秧是什么关系？", "谁是今州令尹？"

    3. 'general' (一般性查询): 
       - 不属于上述两类的其他问题，如世界观设定、术语解释、或者无法明确归类的问题。
       - 例子："什么是共鸣者？", "瑝珑有几个州？", "你好", "今天天气怎么样"。

    请严格只返回一个分类标签（'chapter', 'character', 或 'general'），不要包含任何标点符号或额外解释。

    用户问题: {query}

    分类结果:""")

        # 2. 构建 LCEL 链
        # 假设 self.llm 已经初始化，且 temperature 设为 0 以保证输出稳定
        chain = (
                {"query": RunnablePassthrough()}
                | router_prompt
                | self.llm
                | StrOutputParser()
        )

        try:
            # 3. 执行推理
            result = chain.invoke(query)

            # 4. 清洗结果 (去除可能的空格、换行、标点)
            cleaned_result = result.strip().lower().replace("'", "").replace('"', '').replace('.', '')

            # 5. 验证结果是否在预期范围内，防止 LLM 幻觉
            valid_categories = ['chapter', 'character', 'general']
            if cleaned_result in valid_categories:
                return cleaned_result
            else:
                # 如果 LLM 返回了奇怪的东西，默认降级为 general
                print(f"⚠️ 路由分类结果异常: '{result}', 默认归类为 'general'")
                return 'general'

        except Exception as e:
            print(f"❌ 路由分类失败: {e}")
            return 'general'  # 出错时默认走通用流程


