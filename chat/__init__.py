"""
"""
from typing import List
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

from .knowledge_base import KnowledgeBase


class Chat:
    """ """

    _docs_dir: str
    _db_dir: str
    _urls: List[str]
    _knowledge_base: KnowledgeBase
    _retriever: VectorStoreRetriever
    _qa_chain: RetrievalQA

    def __init__(self, docs_dir: str, db_dir: str, urls: List[str]):
        """ """
        self._docs_dir = docs_dir
        self._db_dir = db_dir
        self._urls = urls
        self._knowledge_base = KnowledgeBase(docs_dir, db_dir, urls)
        self._retriever = self._knowledge_base.retriever
        self._qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model_name="gpt-4"),
            chain_type="stuff",
            retriever=self._retriever,
            return_source_documents=True,
        )

    def _process_llm_response(self, llm_response):
        output = []
        output.append(llm_response["result"])
        output.append("\n\nSources:")
        for source in llm_response["source_documents"]:
            output.append(source.metadata["source"])
        return "\n".join(output)

    def chat(self, query: str):
        """ """
        llm_response = self._qa_chain(query)
        return self._process_llm_response(llm_response)
