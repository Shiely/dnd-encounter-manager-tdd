# adapters/outbound/in_memory_undo_stack.py
# In-memory undo stack adapter

from collections import deque


class InMemoryUndoStack:
    """In-memory undo stack for commands."""

    def __init__(self, maxlen: int = 5):
        self._stack: deque = deque(maxlen=maxlen)

    def push(self, command):
        """Push a command onto the stack."""
        self._stack.append(command)

    def pop(self):
        """Pop a command from the stack."""
        return self._stack.pop() if self._stack else None

    def is_empty(self) -> bool:
        """Check if the stack is empty."""
        return len(self._stack) == 0

    def depth(self) -> int:
        """Get the current depth of the stack."""
        return len(self._stack)
