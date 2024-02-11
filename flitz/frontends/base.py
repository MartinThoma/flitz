from abc import ABC, abstractmethod


class Frontend(ABC):
    def __init__(self, cfg):
        self.cfg = cfg
        self.width = None
        self.height = None
        self.x = None
        self.y = None

    def set_geometry(self, width: int, height: int, x=0, y=0) -> None:
        self.width = width
        self.height = height
        self.x = x
        self.y = y

    def set_title(self, title: str) -> None:
        self.title = title

    def bind(self, event, callback) -> None:
        self.root.bind(event, callback)

    @abstractmethod
    def run(self):
        pass
