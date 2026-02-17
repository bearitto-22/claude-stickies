"""Note data model."""

from dataclasses import dataclass, field
import uuid
import time


@dataclass
class Note:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    color: str = "purple"
    content: list = field(default_factory=list)  # Rich text runs
    width: int = 300
    height: int = 350
    always_on_top: bool = False
    translucent: bool = True
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "color": self.color,
            "content": self.content,
            "width": self.width,
            "height": self.height,
            "always_on_top": self.always_on_top,
            "translucent": self.translucent,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            color=data.get("color", "yellow"),
            content=data.get("content", []),
            width=data.get("width", 300),
            height=data.get("height", 350),
            always_on_top=data.get("always_on_top", False),
            translucent=data.get("translucent", False),
            created_at=data.get("created_at", time.time()),
        )
