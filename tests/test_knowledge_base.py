import os
import shutil
from chat.knowledge_base import KnowledgeBase


class TestKnowledgeBase:
    """ """

    def test_knowledge_base(self, urls):
        """ """
        os.makedirs("tests/docs", exist_ok=True)
        os.makedirs("tests/db", exist_ok=True)

        knowledge_base = KnowledgeBase(
            docs_dir="tests/docs", db_dir="tests/db", urls=urls
        )
        del knowledge_base
        try:
            shutil.rmtree("tests/docs")
            shutil.rmtree("tests/db")
        except FileNotFoundError:
            pass
