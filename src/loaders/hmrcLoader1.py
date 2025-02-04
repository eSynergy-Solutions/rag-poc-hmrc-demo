"""this is a loader for creating an astradb with some information from their API documentation

It does implement any fancy chunking or metadata
it simply takes the openapi yaml paths and embeds their descriptions

There will be no need to run it again once I have created the db, but I am saving this code in case someone needs to reuse or reread it later.
"""

import litellm
from astrapy import DataAPIClient, Collection
from dotenv import load_dotenv
import os
import yaml
from pathlib import Path
from icecream import ic
from math import ceil

load_dotenv()

client = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))
database = client.get_database(os.getenv("ASTRA_DB_API_ENDPOINT"))


def create_astradb_collection(name="HMRC_API_ROTOTYPE1_CHUNKED"):
    database.create_collection(
        name=name, dimension=1536
    )  # the embeddings will come from openai's ada-02 model


def load_yamls(
    directory_path: str = "/Users/juliusvidal/code/rag-poc-backend/src/loaders/data/hmrc_prototype1",
):
    """
    Loads all YAML files from the specified directory and returns a list of dictionaries.

    Parameters:
        directory_path (str or Path): The path to the directory containing YAML files.

    Returns:
        List[dict]: A list of dictionaries parsed from the YAML files.
    """
    yaml_dicts = []
    directory = Path(directory_path)

    if not directory.is_dir():
        raise ValueError(f"The path '{directory_path}' is not a valid directory.")

    # Iterate through all files in the directory
    for file_path in directory.iterdir():
        # Check if the file has a .yaml or .yml extension
        if file_path.is_file() and file_path.suffix.lower() in [".yaml", ".yml"]:
            try:
                with file_path.open("r", encoding="utf-8") as file:
                    # Parse the YAML file
                    data = yaml.safe_load(file)
                    yaml_dicts.append(data)
            except yaml.YAMLError as e:
                print(f"Error parsing YAML file '{file_path}': {e}")
            except Exception as e:
                print(f"Unexpected error with file '{file_path}': {e}")

    return yaml_dicts


def get_endpoints(api_dict):
    "a function that takes returns the list of all the yaml endpoint objects in one api_dict"
    return [d for d in api_dict["paths"].items()]


def embed(input: str) -> list[float]:
    "A function that calls the embed client to get the vector embedding of a given string"
    embedding = litellm.embedding(
        "azure/text-embedding-ada-002",
        input=input,
    ).data[0]["embedding"]
    return embedding


def make_db_entries(endpoint_t: tuple[str, dict]):
    "given the dict representation of an endpoint, return an object ready for loading to astradb as kwargs including the vector"
    path, endpoint = endpoint_t
    try:
        description = f"{list(endpoint.values())[0]["description"]}"
    except Exception:
        try:
            description = f"{list(endpoint.values())[0]["summary"]}"
        except Exception as ee:
            ic(list(endpoint.values())[0].keys())
            raise ee
    embedding = embed(description)
    payload = yaml.dump(endpoint)
    entry = {"path": path, "$vector": embedding}
    chunks = [
        {"path": path, "content": payload[3000 * i : 3000 * (i + 1)], "chunk": i}
        for i in range(ceil(len(payload) / 3000))
    ]
    chunks.append(entry)
    return chunks


def extra_embeddings(endpoint_t: tuple[str, dict]):
    "given the dict representation of an endpoint, return an object ready for loading to astradb as kwargs including the vectors for all the other requests you can make"
    path, endpoint = endpoint_t
    vecs = []
    for d in list(endpoint.values())[1:]:
        try:
            description = f"{d["description"]}"
        except Exception:
            try:
                description = f"{d["summary"]}"
            except Exception as ee:
                ic(d.keys())
                raise ee
        embedding = embed(description)

        entry = {"path": path, "$vector": embedding, "description": description}
        vecs.append(entry)

    ic(path, len(vecs))
    return vecs


def load_to_db(collection: Collection, entries: list[dict]):
    insert_result = collection.insert_many(entries)
    print(insert_result)


def retrieve(
    query: str,
    collection: Collection = database.get_collection("HMRC_API_ROTOTYPE1_CHUNKED"),
    endpoint_limit=1,
):
    "A special retriever to deal with the chunking"
    embedding = embed(query)
    api = retrieve_api(embedding, collection=collection)
    endpoints = collection.find(
        {"path": {"$exists": True}},
        sort={"$vector": embedding},
        limit=endpoint_limit,
    )
    ls = [api]
    for p in endpoints:
        path = p["path"]
        chunks = collection.find({"path": path}, limit=20)
        cs: list[dict] = sorted(list(chunks), key=lambda x: x.get("chunk", -1))
        c = cs[0]["path"]
        for ch in cs[1:]:
            c += ch.get("content", "")

        ls.append(c)
    return ls


def retrieve_api(
    query_embedding: list[float],
    collection: Collection = database.get_collection("HMRC_API_ROTOTYPE1_CHUNKED"),
):
    api = collection.find_one(
        {"api": {"$exists": True}}, sort={"$vector": query_embedding}
    )
    return api["api"]


### here we will manually load the api descriptions (this is just a stopgap solution for demo purposes)

agent_auth = """
Name: Agent Authorisation API,
Documentation URL: https://developer.service.hmrc.gov.uk/api-documentation/docs/api/service/agent-authorisation-api/1.0
Description:
    Use the Agent Authorisation API to:
    - request authorisation to act on a client's behalf for either Making Tax Digital for VAT or Making Tax Digital for Income Tax
    cancel an authorisation request
    - check the status of authorisations already requested
    - query active or inactive relationships
"""

IRR = """
Name: Interest Restriction Return (IRR) API
Documentation URL: https://developer.service.hmrc.gov.uk/api-documentation/docs/api/service/interest-restriction-return/1.
Description:
The API in its current state supports the following functions:
Revoke an existing Reporting Company from submitting Interest Restriction Returns
Appoint a new Reporting Company for submitting Interest Restriction Returns
Submit an Interest Restriction Return (full)
Submit an Interest Restriction Return (abbreviated)
"""

CTC = """
Name: CTC Traders API
Documentation URL: https://developer.service.hmrc.gov.uk/api-documentation/docs/api/service/common-transit-convention-traders/2.1
Description: Use the CTC Traders API to:

send departure and arrival movement notifications to the New Computerised Transit System (NCTS)
retrieve messages sent from customs offices of departure and destination
The API endpoints relate only to Great Britain and Northern Ireland.

You can also use the HMRC sandbox environment to run tests for Great Britain and Northern Ireland transit movements."""


APIs = [agent_auth, IRR, CTC]


def load_APIs(
    collection: Collection = database.get_collection("HMRC_API_ROTOTYPE1_CHUNKED"),
    apis: list[str] = APIs,
):
    data = []
    for api in apis:
        emb = embed(api)
        datum = {"$vector": emb, "api": api}
        data.append(datum)

    ic(collection.insert_many(data))


if __name__ == "__main__":
    # create_astradb_collection()
    yaml_dicts = load_yamls()
    endpoints = [ep for api in yaml_dicts for ep in get_endpoints(api)]
    # entries = map(make_db_entries, endpoints)
    extra_vectors = map(extra_embeddings, endpoints)
    docs = [d for ep in extra_vectors for d in ep]
    # with open(
    #     "/Users/juliusvidal/code/rag-poc-backend/src/loaders/data/hmrc_prototype1/extra_vectors.json",
    #     "w",
    # ) as f:
    #     json.dump(list(docs), f)
    # load_APIs()
    # ic(retreive("initialise and agent")[0])

    # with open(
    #     "/Users/juliusvidal/code/rag-poc-backend/src/loaders/data/hmrc_prototype1/stored_db_entries.json",
    #     "r",
    # ) as f:
    #     entries = json.load(f)
    # ic(retrieve("id like to grant authorisation to an agent"))
    # # sizes = [(sys.getsizeof(obj["content"]), obj) for obj in entries]
    # # sizes.sort(key=lambda x: x[0], reverse=True)
    # # ic([d[0] for d in sizes])
    # # biggest = sizes[0][1]["content"]
    # # ic(len(biggest))
    # # ic(biggest[:100])

    collection = database.get_collection(name="HMRC_API_ROTOTYPE1_CHUNKED")

    load_to_db(collection=collection, entries=docs)

    # ic(collection.count_documents({}, upper_bound=500))
