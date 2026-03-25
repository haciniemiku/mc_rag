"""
自动生成评测数据集
自动读取 FAISS 索引和元数据，调用 Kimi 生成测试问题
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()


class TestDatasetGenerator:
    """自动生成测试数据集"""

    def __init__(self, index_path: str = "./vector_index"):
        self.index_path = index_path
        self.qa_pairs: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        
        # 初始化 Kimi LLM
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            raise ValueError("❌ 错误：未找到 MOONSHOT_API_KEY 环境变量")
        
        self.llm = ChatOpenAI(
            model="kimi-k2-0711-preview",
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
            temperature=0.7,
            max_tokens=4096
        )
        
        print("✅ Kimi LLM 初始化成功")

    def load_index_and_documents(self) -> List[Dict[str, Any]]:
        """加载 FAISS 索引和文档"""
        print(f"📂 加载索引: {self.index_path}")
        
        # 加载 FAISS 索引
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings
        
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh-v1.5",
            model_kwargs={'device': 'cpu'}
        )
        
        vectorstore = FAISS.load_local(
            self.index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # 获取所有文档
        chunks = []
        
        # 方法1: 使用 docstore 获取所有文档
        try:
            docstore = vectorstore.docstore
            docs = docstore._dict
            
            for idx, (doc_id, doc) in enumerate(docs.items()):
                chunks.append({
                    'id': idx,
                    'content': doc.page_content,
                    'metadata': doc.metadata
                })
        except Exception as e:
            print(f"⚠️ docstore 方法失败: {e}")
            # 方法2: 使用 similarity_search 获取所有文档
            try:
                # 通过搜索获取所有文档（使用一个会匹配所有内容的查询）
                all_docs = vectorstore.similarity_search("*", k=10000)
                for idx, doc in enumerate(all_docs):
                    chunks.append({
                        'id': idx,
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    })
            except Exception as e2:
                print(f"⚠️ similarity_search 方法也失败: {e2}")
                raise ValueError(f"无法从 FAISS 索引中获取文档: {e2}")
        
        print(f"✅ 加载了 {len(chunks)} 个文档片段")
        return chunks

    def generate_qa_for_chunk(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为一个文档片段生成问答对"""
        content = chunk['content']
        chunk_id = chunk['id']
        metadata = chunk['metadata']
        
        # 提取关键信息
        file_name = metadata.get('file_name', '未知')
        chapter = metadata.get('chapter', '')
        act = metadata.get('act', '')
        
        source_info = f"{file_name}"
        if chapter:
            source_info += f" | 章节: {chapter}"
        if act:
            source_info += f" | 幕: {act}"
        
        # 生成问题的 Prompt
        prompt = ChatPromptTemplate.from_template("""
你是一个专业的测试题生成专家。根据以下剧情片段，生成3个高质量的测试问题。

【片段内容】
{content}

【来源信息】
{source_info}

【任务要求】
请生成以下3种类型的问题：

1. 事实类问题 (factual)：
   - 基于片段中明确的事实信息
   - 询问时间、地点、人物、事件等
   - 答案必须能从片段中直接找到

2. 逻辑类问题 (logical)：
   - 需要基于片段内容进行推理
   - 可以询问原因、关系、意图等
   - 需要一定的分析和推理

3. 否定类问题 (negative)：
   - 询问片段中未提及的信息
   - 询问"没有发生"或"不是"的情况
   - 用于测试模型是否会产生幻觉

【输出格式】
请严格按照以下 JSON 格式输出，不要包含任何 Markdown 标记：
[
    {{
        "question": "事实类问题内容",
        "answer": "问题答案",
        "type": "factual",
        "key_entities": ["角色A", "角色B", "地点X"],
        "source_chunk_id": {chunk_id},
        "source_info": "{source_info}"
    }},
    {{
        "question": "逻辑类问题内容",
        "answer": "问题答案",
        "type": "logical",
        "key_entities": ["角色A", "事件X"],
        "source_chunk_id": {chunk_id},
        "source_info": "{source_info}"
    }},
    {{
        "question": "否定类问题内容",
        "answer": "问题答案",
        "type": "negative",
        "key_entities": ["角色A"],
        "source_chunk_id": {chunk_id},
        "source_info": "{source_info}"
    }}
]
""")
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                'content': content[:2000],  # 限制内容长度
                'source_info': source_info,
                'chunk_id': chunk_id
            }).content
            
            # 清理 JSON
            clean_response = response.replace("```json", "").replace("```", "").strip()
            qa_pairs = json.loads(clean_response)
            
            return qa_pairs
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 解析失败 (chunk {chunk_id}): {e}")
            self.errors.append({
                'chunk_id': chunk_id,
                'error': f'JSON解析失败: {e}'
            })
            return []
        except Exception as e:
            print(f"⚠️ 生成失败 (chunk {chunk_id}): {e}")
            self.errors.append({
                'chunk_id': chunk_id,
                'error': str(e)
            })
            return []

    def generate_dataset(self, output_path: str = "./evaluation/test_dataset.json", max_chunks: int = None, 
                        resume: bool = True, retry_errors: bool = True, max_retries: int = 3):
        """生成完整的测试数据集
        
        Args:
            output_path: 输出文件路径
            max_chunks: 最大处理片段数量
            resume: 是否从断点继续（默认 True）
            retry_errors: 是否重试之前失败的片段（默认 True）
            max_retries: 最大重试次数
        """
        print("🚀 开始生成测试数据集...")
        
        # 加载文档
        all_chunks = self.load_index_and_documents()
        
        # 限制处理数量
        if max_chunks:
            all_chunks = all_chunks[:max_chunks]
        
        print(f"📝 共 {len(all_chunks)} 个文档片段待处理")
        
        # 断点记忆：检查是否有之前的进度
        checkpoint_path = output_path.replace('.json', '_checkpoint.json')
        processed_ids = set()
        
        if resume and Path(checkpoint_path).exists():
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    processed_ids = set(checkpoint_data.get('processed_chunk_ids', []))
                    # 加载之前生成的部分数据
                    self.qa_pairs = checkpoint_data.get('qa_pairs', [])
                    self.errors = checkpoint_data.get('errors', [])
                    print(f"📂 检测到断点文件，已处理 {len(processed_ids)} 个片段，继续生成...")
            except Exception as e:
                print(f"⚠️ 读取断点文件失败，将重新开始: {e}")
                processed_ids = set()
        
        # 过滤出未处理的片段
        chunks_to_process = [c for c in all_chunks if c['id'] not in processed_ids]
        print(f"⏳ 待处理: {len(chunks_to_process)} 个片段")
        
        if not chunks_to_process:
            print("✅ 所有片段已处理完成！")
            self.save_dataset(output_path)
            return self.qa_pairs
        
        # 遍历每个片段生成问答对
        for chunk in tqdm(chunks_to_process, desc="生成问题"):
            chunk_id = chunk['id']
            
            # 重传机制：失败的片段可以重试
            current_retry = 0
            while current_retry < max_retries:
                qa_pairs = self.generate_qa_for_chunk(chunk)
                
                if qa_pairs:
                    # 成功，添加到结果中
                    self.qa_pairs.extend(qa_pairs)
                    processed_ids.add(chunk_id)
                    break
                else:
                    # 失败，重试
                    current_retry += 1
                    if current_retry < max_retries:
                        print(f"🔄 重试 chunk {chunk_id} ({current_retry}/{max_retries})...")
                        import time
                        time.sleep(2)  # 失败后多等一会儿
                    else:
                        print(f"❌ 跳过 chunk {chunk_id}，已达到最大重试次数")
            
            # 保存断点（每处理10个片段保存一次）
            if len(processed_ids) % 10 == 0:
                self._save_checkpoint(checkpoint_path, processed_ids)
            
            # 每次生成后稍微休息一下，避免 API 限流
            import time
            time.sleep(0.5)
        
        # 处理完成后，清理断点文件
        if Path(checkpoint_path).exists():
            Path(checkpoint_path).unlink()
            print("🗑️ 断点文件已清理")
        
        print(f"\n✅ 共生成 {len(self.qa_pairs)} 个问答对")
        
        # 保存结果
        self.save_dataset(output_path)
        
        # 保存错误日志
        if self.errors:
            error_path = output_path.replace('.json', '_errors.json')
            with open(error_path, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, ensure_ascii=False, indent=2)
            print(f"⚠️ 有 {len(self.errors)} 个片段处理失败，已记录到 {error_path}")
        
        return self.qa_pairs
    
    def _save_checkpoint(self, checkpoint_path: str, processed_ids: set):
        """保存断点信息"""
        # 确保目录存在
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint_data = {
            'processed_chunk_ids': list(processed_ids),
            'qa_pairs': self.qa_pairs,
            'errors': self.errors
        }
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 断点已保存: {len(processed_ids)} 个片段已处理")

    def save_dataset(self, output_path: str):
        """保存数据集到文件"""
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.qa_pairs, f, ensure_ascii=False, indent=2)
        
        print(f"💾 数据集已保存到: {output_path}")
        
        # 统计信息
        type_counts = {}
        for qa in self.qa_pairs:
            qtype = qa.get('type', 'unknown')
            type_counts[qtype] = type_counts.get(qtype, 0) + 1
        
        print(f"📊 问题类型统计:")
        for qtype, count in type_counts.items():
            print(f"   - {qtype}: {count} 个")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自动生成测试数据集')
    parser.add_argument('--output', type=str, default='./evaluation/test_dataset.json',
                        help='输出文件路径')
    parser.add_argument('--max_chunks', type=int, default=None,
                        help='最大处理片段数量（用于测试）')
    parser.add_argument('--index_path', type=str, default='./vector_index',
                        help='FAISS 索引路径')
    
    args = parser.parse_args()
    
    # 创建生成器
    generator = TestDatasetGenerator(index_path=args.index_path)
    
    # 生成数据集
    qa_pairs = generator.generate_dataset(
        output_path=args.output,
        max_chunks=args.max_chunks
    )
    
    print(f"\n🎉 测试数据集生成完成！")
    print(f"   - 总问答对数: {len(qa_pairs)}")
    print(f"   - 输出文件: {args.output}")


if __name__ == "__main__":
    main()
