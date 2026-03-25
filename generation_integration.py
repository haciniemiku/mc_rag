import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any


class EntityInfo(BaseModel):
    character: str = Field(description="角色名称，如果没有则为空字符串")
    location: str = Field(description="地点名称，如果没有则为空字符串")
    chapter: str = Field(description="章节信息，如果没有则为空字符串")
    action: str = Field(description="动作类型，如'出现'、'战斗'等")
    time: str = Field(description="时间信息，如'第一次'、'最后'等")


class QueryAnalysisResult(BaseModel):
    rewritten_query: str = Field(description="重写后的查询，用于向量检索，需包含关键实体")
    entities: EntityInfo
    route_type: Literal['factual', 'inferential', 'general'] = Field(description="意图类型")
    is_character_occurrence: bool = Field(description="是否是角色出现查询")
    character_name: str = Field(description="提取到的主要角色名，若无则为空")
    action: str = Field(description="主要动作")
    time: str = Field(description="主要时间词")


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

        try:
            # 执行推理
            rewritten_query = full_chain.invoke({"query": query})
            print(f"🔄 查询重写：{query} → {rewritten_query}")
            return rewritten_query
        except Exception as e:
            print(f"❌ 查询重写失败: {e}")
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
            print(f"❌ 路由分类失败: {e}")
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
            print(f"❌ 结构化实体提取失败: {e}")
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

        try:
            response = full_chain.invoke({
                "system_prompt": system_prompt,
                "context": context,
                "question": question
            })
            return response
        except Exception as e:
            return f"❌ 生成回答时出错: {str(e)}"

    def analyze_query(self, query: str, conversation_history: str = "") -> dict:
        """
        统一查询分析 - 一次大模型调用完成查询重写、结构化信息提取、意图判断
        
        返回:
            dict: 包含以下字段
                - rewritten_query: 重写后的查询
                - entities: 结构化实体信息
                - route_type: 意图类型 ('factual', 'inferential', 'general')
                - is_character_occurrence: 是否是角色出现查询
                - character_name: 角色名称
                - action: 动作类型
                - time: 时间信息
        """
        if not self.llm:
            return self._get_default_result(query)

        analysis_prompt = ChatPromptTemplate.from_template("""
你是一个专业的查询分析引擎。请严格按照以下步骤处理用户输入：

【步骤 1：实体提取】
首先从查询和对话历史中精确提取实体（角色、地点、章节、动作、时间）。
- 如果用户说"他"或"她"，请根据【对话历史】解析为具体角色名。
- 动作和时间必须精确匹配原文词汇。

【步骤 2：意图分类】
基于提取的实体，判断意图：
- 'factual': 询问明确的事实（时间、地点、事件）。
- 'inferential': 需要推理（关系、原因、情感）。
- 'general': 闲聊或系统问题。

【步骤 3：查询重写】
结合实体和意图，将查询重写为一个独立的、包含完整上下文的句子，用于向量检索。
- 必须将代词（他/她/它）替换为具体实体名。
- 必须保留时间和动作限定词。

【输入数据】
对话历史：{conversation_history}
当前查询：{query}

【输出要求】
请直接输出符合 Schema 定义的 JSON 对象，不要包含任何 Markdown 标记，不要包含任何解释性文字。
""")

        try:
            structured_llm = self.llm.with_structured_output(QueryAnalysisResult)
            chain = analysis_prompt | structured_llm
            
            result = chain.invoke({
                "conversation_history": conversation_history,
                "query": query
            })
            
            if isinstance(result, BaseModel):
                return result.model_dump()
            
        except Exception as e:
            print(f"⚠️ 结构化输出失败，使用降级方案: {e}")
            return self._analyze_query_fallback(query, conversation_history)
        
        return self._get_default_result(query)
    
    def _analyze_query_fallback(self, query: str, conversation_history: str = "") -> dict:
        """降级方案：使用原来的 StrOutputParser + json.loads 逻辑"""
        analysis_prompt = ChatPromptTemplate.from_template("""
你是一个专业的查询分析引擎。请严格按照以下步骤处理用户输入：

【步骤 1：实体提取】
首先从查询和对话历史中精确提取实体（角色、地点、章节、动作、时间）。

【步骤 2：意图分类】
- 'factual': 询问明确的事实（时间、地点、事件）。
- 'inferential': 需要推理（关系、原因、情感）。
- 'general': 闲聊或系统问题。

【步骤 3：查询重写】
将查询重写为一个独立的、包含完整上下文的句子，用于向量检索。

【对话历史】
{conversation_history}

【当前查询】
{query}

请返回 JSON 格式的分析结果：
""")
        
        import json
        import time
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                chain = analysis_prompt | self.llm | StrOutputParser()
                result = chain.invoke({
                    "conversation_history": conversation_history,
                    "query": query
                }).strip()
                
                clean_result = result.replace("```json", "").replace("```", "").strip()
                analysis_result = json.loads(clean_result)
                
                analysis_result.setdefault('rewritten_query', query)
                analysis_result.setdefault('entities', {})
                analysis_result.setdefault('route_type', 'general')
                analysis_result.setdefault('is_character_occurrence', False)
                analysis_result.setdefault('character_name', '')
                analysis_result.setdefault('action', '')
                analysis_result.setdefault('time', '')
                
                return analysis_result
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "overloaded" in error_msg.lower():
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                print(f"❌ 降级方案分析失败: {e}")
        
        return self._get_default_result(query)
    
    def _get_default_result(self, query: str) -> dict:
        """提取默认值逻辑，避免代码重复"""
        return {
            'rewritten_query': query,
            'entities': {},
            'route_type': 'general',
            'is_character_occurrence': False,
            'character_name': '',
            'action': '',
            'time': ''
        }