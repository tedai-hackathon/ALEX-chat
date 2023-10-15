import os
from chat import Chat


class TestChat:
    """ """

    def test_chat(self, urls):
        """ """
        os.makedirs("tests/docs", exist_ok=True)
        os.makedirs("tests/db", exist_ok=True)

        chat = Chat(docs_dir="tests/docs", db_dir="tests/db", urls=urls)
        del chat
