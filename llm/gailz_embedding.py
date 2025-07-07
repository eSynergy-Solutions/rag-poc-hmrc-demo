import requests
from typing import List
import json


class GailzEmbedding:
    """
    A class to interact with the Gailz Embedding API for generating text embeddings.
    Supports both single text embedding and batch document embedding.
    """

    def __init__(
        self,
        base_url: str,
        logger,
    ):
        self._embedding_api_string = base_url
        self._logger = logger

    def _make_embedding_request(self, texts: List[str]) -> List[List[float]]:
        """
        Internal method to make embedding requests to the Gailz API.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (list of floats)

        Raises:
            requests.RequestException: If the API request fails
        """
        url = self._embedding_api_string
        headers = {"Content-Type": "application/json"}
        payload = {
            "input": texts,
        }

        self._logger.debug(f"Embedding request payload:\n{json.dumps(payload)}")
        self._logger.debug(f"Request headers:\n{json.dumps(headers)}")

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            self._logger.debug(
                f"Embedding response status code: {response.status_code}"
            )
            self._logger.debug(f"Embedding response content:\n{json.dumps(result)}")
            self._logger.debug(f"Embedding response received for {len(texts)} texts")

            if "data" not in result or not isinstance(result["data"], list):
                self._logger.error(
                    "Unexpected response format: 'data' key missing or not a list"
                )
                raise ValueError("Unexpected response format from embedding API")

            # Extract embeddings from response
            # Assuming response format: {"data": [{"embedding": [...]}, ...]}
            embeddings = [item["embedding"] for item in result["data"]]
            self._logger.info(f"Extracted {len(embeddings)} embeddings from response")
            return embeddings

        except requests.RequestException as e:
            self._logger.error(f"Embedding request failed: {str(e)}")
            raise
        except (KeyError, IndexError) as e:
            self._logger.error(f"Unexpected response format: {str(e)}")
            raise ValueError(f"Unexpected response format from embedding API: {str(e)}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents (texts).

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors, where each vector is a list of floats

        Raises:
            ValueError: If texts list is empty
            requests.RequestException: If the API request fails
        """
        if not texts:
            raise ValueError("Cannot embed empty list of texts")

        self._logger.info(f"Embedding {len(texts)} documents")

        # Handle batch processing if API has limits
        max_batch_size = 100  # Adjust based on API limitations
        all_embeddings = []

        for i in range(0, len(texts), max_batch_size):
            batch = texts[i : i + max_batch_size]
            self._logger.debug(
                f"Processing batch {i//max_batch_size + 1}: {len(batch)} texts"
            )

            batch_embeddings = self._make_embedding_request(batch)
            all_embeddings.extend(batch_embeddings)

        self._logger.info(f"Successfully embedded {len(all_embeddings)} documents")
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector as a list of floats

        Raises:
            ValueError: If text is empty
            requests.RequestException: If the API request fails
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty or whitespace-only text")

        self._logger.debug(f"Embedding single query text (length: {len(text)})")

        embeddings = self._make_embedding_request([text])

        if not embeddings:
            raise ValueError("No embedding returned from API")

        return embeddings[0]

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        Makes a test request with a small text to determine dimension.

        Returns:
            Integer dimension of embedding vectors
        """
        try:
            test_embedding = self.embed_query("test")
            dimension = len(test_embedding)
            self._logger.info(f"Embedding dimension: {dimension}")
            return dimension
        except Exception as e:
            self._logger.error(f"Failed to determine embedding dimension: {str(e)}")
            raise ValueError(
                "Could not determine embedding dimension. Ensure the API is reachable and functioning."
            )
