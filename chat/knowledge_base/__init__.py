"""
"""
from typing import List
from bs4 import BeautifulSoup
import requests
from requests.exceptions import InvalidSchema, ConnectionError
import re
import os
import shutil
from urllib.parse import urlparse, unquote

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
    _vector_store: Chroma
    _urls: List[str] = []
    _text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    )
    _embedding: OpenAIEmbeddings = OpenAIEmbeddings()

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

        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        self._urls = urls

        self._save_docs(self._urls)

        self._loader = DirectoryLoader(self._docs_dir)
        doc = self._loader.load()
        texts = self._text_splitter.split_documents(doc)
        self._vector_store = Chroma.from_documents(
            documents=texts, embedding=self._embedding, persist_directory=db_dir
        )

    def _save_docs(self, urls: List[str]):
        """ """
        all_urls = []
        for url in urls:
            if url is None or type(url) != str:
                continue
            if not url.startswith("http://") and not url.startswith("https://"):
                continue
            all_urls.append(url)
            webpage_data = self._get_webpage_data(url)
            if webpage_data is None:
                continue
            child_urls = self._get_child_urls(webpage_data.text)
            all_urls.extend(self._add_base_path(url, child_urls))

        for url in all_urls:
            if url is None or type(url) != str:
                continue
            if not url.startswith("http://") and not url.startswith("https://"):
                continue
            webpage_data = self._get_webpage_data(url)
            if webpage_data is None:
                continue
            self._save_webpage_text(self._docs_dir, webpage_data, url)

    def _get_webpage_data(self, url: str) -> requests.Response:
        """ """
        try:
            response = requests.get(url, timeout=5)
        except (InvalidSchema, ConnectionError):
            return None
        return response

    def _get_child_urls(self, data: str) -> List[str]:
        """ """
        soup = BeautifulSoup(data, "html.parser")
        list_links = []
        for link in soup.find_all("a", href=True):
            list_links.append(link["href"])
        return list_links

    def _add_base_path(self, website_link, list_links):
        list_links_with_base_path = []

        for link in list_links:
            if link.startswith("http://") or link.startswith("https://"):
                list_links_with_base_path.append(link)

            elif not link.startswith("/"):
                link_with_base_path = website_link + link
                list_links_with_base_path.append(link_with_base_path)

            elif link.startswith("."):
                link_with_base_path = website_link + link.split("/")[-1]
                list_links_with_base_path.append(link_with_base_path)

        return list_links_with_base_path

    def _save_webpage_text(self, folder: str, data, url: str = None):
        """ """
        if url.endswith(".pdf"):
            parsed_url = urlparse(url)
            file_name = unquote(os.path.basename(parsed_url.path))
            with open(f"{folder}/{file_name}", "wb") as f:
                f.write(data.content)
            return file_name

        soup = BeautifulSoup(data.text, "html.parser")
        text = soup.get_text()
        text = re.sub(r"\n+", "\n", text)
        text = re.sub(r"\n", "\n\n", text)

        file_name_prefix = "unknown" + str(len(os.listdir(folder)))
        if soup.title is not None:
            file_name_prefix = soup.title.string

        file_name_prefix = re.sub(r"[^a-zA-Z0-9]+", "_", file_name_prefix)
        file_extension = ".txt"

        file_name = f"{folder}/{file_name_prefix}{file_extension}"
        with open(file_name, "w") as f:
            f.write(text)
        return file_name_prefix

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

    @property
    def retriever(self):
        """ """
        return self._vector_store.as_retriever()

    @urls.setter
    def urls(self, urls: List[str]):
        """ """
        new_urls = set(urls) - set(self._urls)
        if len(new_urls) == 0:
            return

        self._urls.extend(new_urls)
        self._save_docs(new_urls)
