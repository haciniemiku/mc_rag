import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


class GenerationIntegrationModule:
    """生成集成模块 - 负责LLM集成和回答生成"""

    def __init__(self, model_name: str = "moonshot-v1-8k",
                 temperature: float = 0.1, max_tokens: int = 2048):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 1. 获取 API Key
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            raise ValueError("❌ 错误：未找到 MOONSHOT_API_KEY 环境变量。请检查 .env 文件。")

        # 2. 初始化 LLM
        # Moonshot 兼容 OpenAI 接口，但需要指定 base_url
        try:
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url="https://api.moonshot.cn/v1",  # 关键：Moonshot 的 API 地址
                temperature=temperature,
                max_tokens=max_tokens
            )
            print(f"✅ LLM 初始化成功: {model_name}")
        except Exception as e:
            print(f"❌ LLM 初始化失败: {e}")
            self.llm = None

    def rewrite_query(self, query: str) -> str:
        """
        查询重写 - 优化用户查询以提高检索效果
        """
        if not self.llm:
            return query

        # 定义查询重写的 Prompt 模板
        rewrite_prompt = ChatPromptTemplate.from_template("""
你是一个智能查询重写助手。请根据以下要求重写用户查询：

1. 识别查询中的关键实体（如角色名、章节等）
2. 明确查询意图（如关系查询、事件查询、出现位置查询等）
3. 重写为更清晰、更具体的查询，便于向量检索
4. 保持原始查询的核心意图不变

例如：
- 原始查询："漂泊者和谁是一对？" → 重写："漂泊者的伴侣是谁？漂泊者与哪个角色是情侣关系？"
- 原始查询："漂泊者最恨谁？" → 重写："漂泊者最痛恨的角色是谁？漂泊者与哪个角色有仇？"
- 原始查询："第一章漂泊者做了什么？" → 重写："第一章中漂泊者的行动和经历是什么？"
- 原始查询："菲比第一次出现在第几章？" → 重写："菲比这个角色首次出现的章节是哪一章？"

用户查询: {query}

重写后的查询:""")

        # 构建 LCEL 链
        full_chain = rewrite_prompt | self.llm | StrOutputParser()

        # 添加重试机制
        import time
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 执行推理
                rewritten_query = full_chain.invoke({"query": query})
                print(f"🔄 查询重写：{query} → {rewritten_query}")
                return rewritten_query
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "overloaded" in error_msg.lower():
                    print(f"⚠️ API限流，等待{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        print(f"❌ 查询重写失败，返回原始查询")
                        return query
                else:
                    print(f"❌ 查询重写失败: {e}")
                    return query
        
        return query

    def query_router(self, query: str) -> str:
        """
        查询路由 - 根据用户问题自动分类
        """
        if not self.llm:
            print("⚠️ LLM 未初始化，路由默认返回 'general'")
            return 'general'

        # 1. 定义 Prompt 模板
        router_prompt = ChatPromptTemplate.from_template("""
你是一个智能查询分类助手。请分析用户的问题，将其归类为以下三种类型之一：

1. 'factual' (基于剧情的事实性问题): 
   - 用户询问剧情中明确发生的事实、事件、时间、地点等。
   - 关键词示例："第一次出现在", "和谁战斗过", "发生在哪一章", "说了什么", "做了什么"。
   - 示例问题："漂泊者第一次出现在哪个章节？"、"菲比和谁战斗过？"、"第一章发生了什么？"

2. 'inferential' (基于剧情的推理性问题): 
   - 用户询问需要基于剧情进行推理、分析角色关系、情感倾向等。
   - 关键词示例："可能", "最", "好感", "恨", "喜欢", "关系", "为什么"。
   - 示例问题："谁对漂泊者可能有好感？"、"漂泊者最恨谁？"、"为什么角色A会这样做？"

3. 'general' (剧情无关性问答): 
   - 用户询问与剧情无关的问题，如系统功能、身份等。
   - 关键词示例："你是谁", "有什么功能", "能做什么", "怎么用"。
   - 示例问题："你是谁？"、"你有什么功能？"、"怎么使用你？"

请严格只返回一个分类标签（'factual', 'inferential', 或 'general'），不要包含任何标点符号或额外解释。

用户问题: {query}

分类结果:""")

        # 2. 构建 LCEL 链
        full_chain = router_prompt | self.llm | StrOutputParser()

        # 添加重试机制
        import time
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 3. 执行推理
                result = full_chain.invoke({"query": query})

                # 4. 清洗结果
                cleaned_result = result.strip().lower().replace("'", "").replace('"', '').replace('.', '')

                # 5. 验证结果
                valid_categories = ['factual', 'inferential', 'general']
                if cleaned_result in valid_categories:
                    return cleaned_result
                else:
                    print(f"⚠️ 路由分类结果异常: '{result}', 默认归类为 'general'")
                    return 'general'

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "overloaded" in error_msg.lower():
                    print(f"⚠️ API限流，等待{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        print(f"❌ 路由分类失败，默认返回 'general'")
                        return 'general'
                else:
                    print(f"❌ 路由分类失败: {e}")
                    return 'general'
        
        return 'general'

    def extract_character_name(self, query: str) -> str:
        """
        使用LLM提取查询中的角色名称
        """
        if not self.llm:
            return ""

        extract_prompt = ChatPromptTemplate.from_template("""
你是一个智能实体提取助手。请从用户查询中提取角色名称。

要求：
1. 只提取角色名称，不要包含其他词汇
2. 如果查询中没有角色名称，返回空字符串
3. 角色名称通常是2-4个中文字符
4. 不要提取地点、时间、动作等非角色实体

例如：
- "炽霞第一次在哪里出现" → "炽霞"
- "秧秧首次出现" → "秧秧"
- "漂泊者最后一次登场" → "漂泊者"
- "第一章发生了什么" → ""

用户查询: {query}

角色名称:""")

        full_chain = extract_prompt | self.llm | StrOutputParser()

        try:
            character_name = full_chain.invoke({"query": query}).strip()
            print(f"🎯 LLM提取的角色名称: {character_name}")
            return character_name
        except Exception as e:
            print(f"❌ 角色名称提取失败: {e}")
            return ""

    def extract_structured_entities(self, query: str) -> dict:
        """
        使用LLM从查询中提取结构化实体信息
        
        返回格式:
        {
            "character": "角色名称或空字符串",
            "location": "地点名称或空字符串", 
            "chapter": "章节信息或空字符串",
            "action": "动作类型或空字符串",
            "time": "时间信息或空字符串"
        }
        """
        if not self.llm:
            return {}

        extract_prompt = ChatPromptTemplate.from_template("""
你是一个智能实体提取助手。请从用户查询中提取结构化实体信息。

要求：
1. 严格按照JSON格式返回，不要添加任何其他文字
2. 如果某个实体在查询中不存在，返回空字符串
3. 角色名称通常是2-4个中文字符
4. 章节信息可能是"第一章"、"第二章"、"序章"等
5. 地点可能是地图区域、城市名称等
6. 动作类型可能是"出现"、"战斗"、"对话"、"死亡"等
7. 时间可能是"第一次"、"最后一次"、"开始"、"结束"等

JSON格式示例:
{{"character": "炽霞", "location": "", "chapter": "", "action": "出现", "time": "第一次"}}

用户查询: {query}

请返回JSON格式的实体信息:""")

        full_chain = extract_prompt | self.llm | StrOutputParser()

        # 添加重试机制
        import time
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                result = full_chain.invoke({"query": query}).strip()
                print(f"🎯 LLM提取的结构化实体: {result}")
                
                # 尝试解析JSON
                import json
                try:
                    entities = json.loads(result)
                    return entities
                except json.JSONDecodeError:
                    print(f"⚠️ JSON解析失败，返回空字典")
                    return {}
                    
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "overloaded" in error_msg.lower():
                    print(f"⚠️ API限流，等待{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                        continue
                    else:
                        print(f"❌ 达到最大重试次数，返回空字典")
                        return {}
                else:
                    print(f"❌ 结构化实体提取失败: {e}")
                    return {}
        
        return {}

    def generate(self, question: str, context: str, system_prompt: str, stream: bool = False) -> str:
        """生成最终回答"""
        if not self.llm:
            return "❌ 系统错误：LLM 未初始化，无法生成回答。"

        # 构建回答用的 Prompt
        generation_prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            ("human", "背景知识:\n{context}\n\n用户问题: {question}")
        ])

        # 构建完整的链
        full_chain = generation_prompt | self.llm | StrOutputParser()

        # 添加重试机制
        import time
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = full_chain.invoke({
                    "system_prompt": system_prompt,
                    "context": context,
                    "question": question
                })
                return response
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "overloaded" in error_msg.lower():
                    print(f"⚠️ API限流，等待{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        return f"❌ API服务繁忙，请稍后再试。"
                else:
                    return f"❌ 生成回答时出错: {str(e)}"
        
        return "❌ 生成回答失败，请稍后再试。"