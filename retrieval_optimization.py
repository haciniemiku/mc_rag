import logging
from typing import List, Dict, Any

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document


class RetrievalOptimizationModule:
    """检索优化模块 - 负责混合检索和过滤"""

    def __init__(self, vectorstore: FAISS, chunks: List[Document]):
        self.vectorstore = vectorstore
        self.chunks = chunks
        self.setup_retrievers()

    def setup_retrievers(self):
        """设置向量检索器和BM25检索器"""
        # 向量检索器
        self.vector_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )

        # BM25检索器
        self.bm25_retriever = BM25Retriever.from_documents(
            self.chunks,
            k=5
        )

    def hybrid_search(self, query: str, top_k: int = 3) -> List[Document]:
        """混合检索 - 结合向量检索和BM25检索，使用RRF重排"""
        # 分别获取向量检索和BM25检索结果
        vector_docs = self.vector_retriever.get_relevant_documents(query)
        bm25_docs = self.bm25_retriever.get_relevant_documents(query)

        # 使用RRF重排
        reranked_docs = self._rrf_rerank(vector_docs, bm25_docs)
        return reranked_docs[:top_k]

    def _rrf_rerank(self, vector_results: List[Document], bm25_results: List[Document]) -> List[Document]:
        """RRF (Reciprocal Rank Fusion) 重排"""

        # RRF融合算法
        rrf_scores = {}
        k = 60  # RRF参数

        # 计算向量检索的RRF分数
        for rank, doc in enumerate(vector_results):
            doc_id = id(doc)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)

        # 计算BM25检索的RRF分数
        for rank, doc in enumerate(bm25_results):
            doc_id = id(doc)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)

        # 合并所有文档并按RRF分数排序
        all_docs = {id(doc): doc for doc in vector_results + bm25_results}
        sorted_docs = sorted(all_docs.items(),
                             key=lambda x: rrf_scores.get(x[0], 0),
                             reverse=True)

        return [doc for _, doc in sorted_docs]

    def metadata_filtered_search(self, query: str, filters: Dict[str, Any],
                                 top_k: int = 5) -> List[Document]:
        """基于元数据过滤的检索"""
        # 先进行向量检索
        vector_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": top_k * 3, "filter": filters}  # 扩大检索范围
        )

        results = vector_retriever.invoke(query)
        return results[:top_k]
