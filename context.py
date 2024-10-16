import abc
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


class ContextStorageEngine(abc.ABC):
    @abc.abstractmethod
    def get(self, key: str, context_type: str) -> Optional[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def set(self, key: str, value: Any, context_type: str) -> None:
        pass

    @abc.abstractmethod
    def delete(self, key: str, context_type: str) -> None:
        pass


class InMemoryContextStorage(ContextStorageEngine):
    def __init__(self):
        self.contexts = {'contact': {}, 'thread': {}}

    def get(self, key: str, context_type: str) -> Optional[Dict[str, Any]]:
        return self.contexts[context_type].get(key)

    def set(self, key: str, value: Any, context_type: str) -> None:
        if key not in self.contexts[context_type]:
            self.contexts[context_type][key] = {}
        self.contexts[context_type][key]['value'] = value
        self.contexts[context_type][key]['timestamp'] = datetime.now().isoformat()

    def delete(self, key: str, context_type: str) -> None:
        if key in self.contexts[context_type]:
            del self.contexts[context_type][key]


class Context:
    def __init__(self, storage_engine: ContextStorageEngine):
        self.storage_engine = storage_engine

    def get(self, key: str, context_type: str = 'thread') -> Optional[Tuple[Any, str, str]]:
        thread_context = self.storage_engine.get(key, 'thread')
        if thread_context:
            return (thread_context['value'], 'thread', thread_context['timestamp'])

        if context_type == 'thread':
            contact_context = self.storage_engine.get(key, 'contact')
            if contact_context:
                return (contact_context['value'], 'contact', contact_context['timestamp'])

        return None

    def set(self, key: str, value: Any, context_type: str = 'thread') -> None:
        self.storage_engine.set(key, value, context_type)

    def delete(self, key: str, context_type: str = 'thread') -> None:
        self.storage_engine.delete(key, context_type)