from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from collections import defaultdict


class ContextStorage(ABC):

    def __init(self, namespace_elements:tuple[]):
        self.namespace = ':'.join(namespace_elements)

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass


class InMemoryContextStorage(ContextStorage):
    def __init__(self, namespace):
        super().__init__(namespace)
        self.data = defaultdict(lambda: defaultdict(None))

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self.data[self.namespace][key]

    def set(self, key: str, value: Any) -> None:
        self.data[self.namespace][key] = value

    def delete(self, key: str) -> None:
        del self.data[self.namespace][key]


class Context:
    def __init__(self, storage_engine: ContextStorage, storage_prefix: str):
        self.storage_engine = storage_engine
        self.storage_prefix = storage_prefix

    def get(self, key: str) -> Optional[Tuple[Any, str, str]]:
        return self.storage_engine.get(key, self.storage_prefix)

    def set(self, key: str, value: Any) -> None:
        self.storage_engine.set(key, value, self.storage_prefix)

    def delete(self, key: str) -> None:
        self.storage_engine.delete(key, self.storage_prefix)