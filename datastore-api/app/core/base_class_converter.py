from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..models.datastore import Datastore
from ..models.document import Document
from ..models.index import Index
from ..models.query import QueryResult


class BaseClassConverter(ABC):
    """
    Provides an abstract interface for a class that converts between datastore api model objects and backend-specific objects.
    """

    @abstractmethod
    def convert_from_datastore(self, datastore: Datastore) -> Dict[str, Any]:
        """
        Converts a datastore object to a backend-specific object.
        """
        pass

    @abstractmethod
    def convert_to_datastore(self, datastore_name: str, obj: Dict[str, Any]) -> Datastore:
        """
        Converts a backend-specific object to a datastore object.
        """
        pass

    @abstractmethod
    def convert_from_index(self, index: Index) -> Dict[str, Any]:
        """
        Converts an index object to a backend-specific object.
        """
        pass

    @abstractmethod
    def convert_to_index(self, obj: Dict[str, Any]) -> Index:
        """
        Converts a backend-specific object to an index object.
        """
        pass

    @abstractmethod
    def convert_from_document(self, document: Document) -> Dict[str, Any]:
        """
        Converts a document object to a backend-specific object.
        """
        pass

    @abstractmethod
    def convert_to_document(self, obj: Dict[str, Any], document_id: str) -> Document:
        """
        Converts a backend-specific object to a document object.
        """
        pass

    @abstractmethod
    def convert_to_query_results(self, obj: Dict[str, Any]) -> List[QueryResult]:
        """
        Converts a backend-specific object to a list of query results.
        """
        pass
