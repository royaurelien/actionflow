import threading
from typing import Any, Dict


class Context:
    """A thread-safe singleton class to hold shared context."""

    _instance = None
    _lock = threading.Lock()  # Lock object for thread-safe access

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:  # Ensure only one thread can execute this block
                if cls._instance is None:
                    cls._instance = super(Context, cls).__new__(cls)
                    cls._instance.data = {}
        return cls._instance

    def initialize(self, initial_data: Dict[str, Any]):
        """
        Initialize the context with data.
        Can only be called the first time.
        """
        with self._lock:
            if not self.data:  # Only initialize if no data exists
                self.data.update(initial_data)
            else:
                raise ValueError("Context has already been initialized.")

    def __getattr__(self, name: str) -> Any:
        """Get an attribute from the context data."""
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'Context' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any):
        """Set an attribute in the context data."""
        if name == "data" or name.startswith("_"):  # For internal attributes
            super().__setattr__(name, value)
        else:
            self.data[name] = value

    def __delattr__(self, name: str):
        """Delete an attribute from the context data."""
        if name in self.data:
            del self.data[name]
        else:
            raise AttributeError(f"'Context' object has no attribute '{name}'")

    def set(self, key: str, value: Any):
        """Set a key-value pair in the context."""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context."""
        return self.data.get(key, default)

    def clear(self):
        """Clear all data in the context."""
        self.data.clear()
