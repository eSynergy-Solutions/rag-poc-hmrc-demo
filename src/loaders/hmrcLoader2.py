from astrapy import DataAPIClient
from astrapy.constants import VectorMetric
from astrapy.ids import UUID
from astrapy.info import CollectionDefinition


ASTRA_DB_APPLICATION_TOKEN = "AstraCS:..."
ASTRA_DB_API_ENDPOINT = "https://01234567-....apps.astra.datastax.com"

# Connect and create the Database object
my_client = DataAPIClient()
my_database = my_client.get_database(
    ASTRA_DB_API_ENDPOINT,
    token=ASTRA_DB_APPLICATION_TOKEN,
)

# Create a vector collection
my_collection = my_database.create_collection(
    "dreams_collection",
    definition=(
        CollectionDefinition.builder()
        .set_vector_dimension(3)
        .set_vector_metric(VectorMetric.COSINE)
        .build()
    ),
)

# Populate the collection with some documents
my_collection.insert_many(
    [
        {
            "_id": UUID("018e65c9-e33d-749b-9386-e848739582f0"),
            "summary": "Riding the waves",
            "tags": ["sport"],
            "$vector": [0, 0.2, 1],
        },
        {
            "summary": "Friendly aliens in town",
            "tags": ["scifi"],
            "$vector": [-0.3, 0, 0.8],
        },
        {
            "summary": "Meeting Beethoven at the dentist",
            "$vector": [0.2, 0.6, 0],
        },
    ],
)

my_collection.update_one(
    {"tags": "sport"},
    {"$set": {"summary": "Surfers' paradise"}},
)

# Run a vector search
cursor = my_collection.find(
    {},
    sort={"$vector": [0, 0.2, 0.4]},
    limit=2,
    include_similarity=True,
)

for result in cursor:
    print(f"{result['summary']}: {result['$similarity']}")

# This would print:
#   Surfers' paradise: 0.98238194
#   Friendly aliens in town: 0.91873914

# Resource cleanup
my_collection.drop()
