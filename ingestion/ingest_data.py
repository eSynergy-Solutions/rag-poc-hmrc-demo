"""this is an ingestor for creating a vectordb with some information from their API documentation

It does not implement any fancy chunking or metadata
it simply takes the openapi yaml paths and embeds their descriptions

"""

import getpass
import os
from langchain_postgres import PGVector
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document
from typing import List
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("AZURE_OPENAI_API_KEY"):
    os.environ["AZURE_OPENAI_API_KEY"] = getpass.getpass("Enter API key for Azure: ")


embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)


# Conect to PostgreSQL using psycopg3

# Placeholder names
connection = os.getenv("PGVECTOR_DB_URL")
if not connection:
    raise ValueError("PGVECTOR_DB_URL environment variable is not set.")
collection_name = os.getenv("PGVECTOR_CONNECTION_NAME")
if not collection_name:
    raise ValueError("PGVECTOR_CONNECTION_NAME environment variable is not set.")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
)

# docs: List[Document]

# vector_store.add_documents(docs, ids=[doc.metadata["id"] for doc in docs])
