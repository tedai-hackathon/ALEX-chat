"""
"""
from typing import List
from bs4 import BeautifulSoup
import requests
import re
import os

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import DirectoryLoader


class KnowledgeBase:
    """
    A knowledge base is a collection of documents derived from urls
    that can be searched given a prompt.

    Args:
        _docs_dir (str): The directory where the documents are stored.
        _db_dir (str): The directory where the vector store is stored.
        _loader (DirectoryLoader): The loader used to load the documents.
        _urls (List[str]): The urls used to create the knowledge base.
        _text_splitter (RecursiveCharacterTextSplitter): The text splitter used
        to split the documents.
        _embedding (OpenAIEmbeddings): The embedding used to embed the documents.
        _vector_store (Chroma): The vector store used to store the documents.
    """

    _docs_dir: str
    _db_dir: str
    _loader: DirectoryLoader
    _urls: List[str] = []
    _text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    )
    _embedding: OpenAIEmbeddings = OpenAIEmbeddings()
    _vector_store: Chroma = Chroma()

    def __init__(
        self,
        docs_dir: str,
        db_dir: str,
        urls: List[str],
    ):
        """
        Args:
            docs_dir (str): The directory where the documents are stored.
            db_dir (str): The directory where the vector store is stored.
            urls (List[str]): The urls used to create the knowledge base.
        """
        self._docs_dir = docs_dir
        self._db_dir = db_dir
        self._urls = urls
        self._loader = DirectoryLoader(docs_dir, glob="*.txt")
        self._vector_store = Chroma(
            persist_directory=db_dir, embedding_function=self._embedding
        )

        self._save_docs(self._urls)

    def __del__(self):
        """ """
        self._vector_store.delete_collection()
        self._vector_store.persist()

        # delete all files in docs_dir
        for file in os.listdir(self._docs_dir):
            os.remove(os.path.join(self._docs_dir, file))

    def _save_docs(self, urls: List[str]):
        """ """
        try:
            for url in urls:
                webpage_data = self._get_webpage_data(url)
                child_urls = self._get_child_urls(webpage_data)
                self._urls.extend(child_urls)
                self._save_webpage_text(self._docs_dir, webpage_data)
        except Exception as e:
            print(e)
            return

        doc = self._loader.load()
        texts = self._text_splitter.split_documents(doc)
        self._vector_store.add(documents=texts)
        self._vector_store.persist()

    def _get_webpage_data(self, url: str) -> str:
        """ """
        response = requests.get(url)
        return response.text

    def _get_child_urls(self, data: str) -> List[str]:
        """ """
        soup = BeautifulSoup(data, "html.parser")
        links = soup.find_all("a")
        return [link.get("href") for link in links]

    def _save_webpage_text(self, folder: str, data: str):
        """ """
        soup = BeautifulSoup(data, "html.parser")
        text = soup.get_text()
        text = re.sub(r"\n+", "\n", text)
        text = re.sub(r"\n", "\n\n", text)
        file_name_prefix = soup.title.string
        file_name_prefix = re.sub(r"[^a-zA-Z0-9]+", "_", file_name_prefix)
        file_name = f"{folder}/{file_name_prefix}.txt"
        with open(file_name, "w") as f:
            f.write(text)

    def get_relevant_documents(self, prompt: str) -> List[Document]:
        retriever = self._vector_store.as_retriever()
        docs = retriever.get_relevant_documents(prompt)
        return docs

    @property
    def docs_dir(self):
        """ """
        return self._docs_dir

    @property
    def urls(self):
        """ """
        return self._urls

    @urls.setter
    def urls(self, urls: List[str]):
        """ """
        new_urls = set(urls) - set(self._urls)
        if len(new_urls) == 0:
            return

        self._urls.extend(new_urls)
        self._save_docs(new_urls)
