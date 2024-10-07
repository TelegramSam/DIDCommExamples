import abc
from datetime import datetime
from typing import Any, Dict, Optional

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
        self.contact_contexts = {}
        self.thread_contexts = {}

    def get(self, key: str, context_type: str) -> Optional[Dict[str, Any]]:
        contexts = self.contact_contexts if context_type == 'contact' else self.thread_contexts
        return contexts.get(key)

    def set(self, key: str, value: Any, context_type: str) -> None:
        contexts = self.contact_contexts if context_type == 'contact' else self.thread_contexts
        if key not in contexts:
            contexts[key] = {}
        contexts[key]['value'] = value
        contexts[key]['timestamp'] = datetime.now().isoformat()

    def delete(self, key: str, context_type: str) -> None:
        contexts = self.contact_contexts if context_type == 'contact' else self.thread_contexts
        if key in contexts:
            del contexts[key]

class Context:
    def __init__(self, storage_engine: ContextStorageEngine):
        self.storage_engine = storage_engine

    def get_contact_context(self, did: str) -> Optional[Any]:
        context = self.storage_engine.get(did, 'contact')
        return context['value'] if context else None

    def set_contact_context(self, did: str, value: Any) -> None:
        self.storage_engine.set(did, value, 'contact')

    def get_thread_context(self, thid: str) -> Optional[Any]:
        context = self.storage_engine.get(thid, 'thread')
        return context['value'] if context else None

    def set_thread_context(self, thid: str, value: Any) -> None:
        self.storage_engine.set(thid, value, 'thread')

    def delete_contact_context(self, did: str) -> None:
        self.storage_engine.delete(did, 'contact')

    def delete_thread_context(self, thid: str) -> None:
        self.storage_engine.delete(thid, 'thread')