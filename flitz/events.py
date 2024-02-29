"""
Events that are produced by parts of flitz.

All of those events can be consumed by other parts of flitz.
The Event class should not be used anywhere else in flitz.
"""

from collections.abc import Callable


class Event:
    """
    An event that can be consumed by listeners.

    Attributes
      name: The name of the event.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.listeners: list[Callable[[], None]] = []

    def consumed_by(self, consumer: Callable[[], None]) -> None:
        """Register a consumer."""
        self.listeners.append(consumer)

    def produce(self) -> None:
        """Produce an event and inform all listeners."""
        for listener in self.listeners:
            listener()


current_path_changed = Event("current_path_changed")

# either contents or the folder itself:
current_folder_changed = Event("current_folder_changed")


# Display modes: SEARCH, LIST
display_mode_changed = Event("display_mode_changed")
