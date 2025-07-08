from abc import ABC, abstractmethod


class ServiceDiscovery(ABC):
    """Abstract base class for service discovery services.
    This class defines the interface for querying a vector database
    and discovering services based on YAML specifications.
    """

    @abstractmethod
    def query_vector_database(self, content: str):
        """Query the vector database with a YAML string.
        This method should be implemented by subclasses to perform
        the actual query operation.
        """
        pass
