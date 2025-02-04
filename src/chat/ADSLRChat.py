"""
This module replicates the Anito-DataStax-Langchain-RAG implementation (ADSLR) from the previous repo
"""

import os
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_astradb import AstraDBVectorStore
from langchain.chains import RetrievalQA
from src.chat.Chat import Chat

from dotenv import load_dotenv
import langchain

from src.schemas.ChatSchemas import ChatMessage

langchain.verbose = False

load_dotenv()


class ADSLRChat(Chat):
    def __init__(self):
        llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            verbose=False,
            temperature=0.3,
        )
        embedding = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_EMB_ENDPOINT"),
            openai_api_key=os.getenv("AZURE_OPENAI_EMB_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_EMB_API_VERSION"),
        )

        self.vstore = AstraDBVectorStore(
            collection_name=os.getenv("BS_COLLECTION_NAME", "funding_for_farmers"),
            embedding=embedding,
            token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
            api_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT"),
            namespace="defra_chatbot_keyspace",
        )

        retriever = self.vstore.as_retriever(search_kwargs={"k": 3})

        self.qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

    # def load_documents(self, collection_name):
    #     jsons = os.listdir("./docs")
    #     for jfile in tqdm(jsons):
    #         with open(f"./docs/" + jfile, "rt") as file:
    #             jobj = json.loads(file.read())
    #             metadata = {"url": jobj["url"]}
    #             docs = []
    #             for i, chunk in enumerate(jobj["chunks"]):
    #                 metadata["chunk_order"] = i
    #                 doc = Document(page_content=chunk, metadata=metadata)
    #                 docs.append(doc)
    #             vstore.add_documents(docs)

    def chat_query(self, chat_history: list[ChatMessage]) -> ChatMessage:
        response = self.qa_chain.invoke(str(chat_history))
        # print(response)
        return ChatMessage(role="assistant", content=response["result"])
