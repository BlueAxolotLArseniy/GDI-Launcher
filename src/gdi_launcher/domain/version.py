from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class GameVersion:
    id: str
    display_name: str
    game_url: str
    geode_supported: bool = False
    geode_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_manifest_item(cls, item: dict[str, Any]) -> "GameVersion":
        geode = item.get("geode") or {}

        return cls(
            id=str(item.get("id", "")),
            display_name=str(item.get("display_name", item.get("id", ""))),
            game_url=str(item.get("game_url", "")),
            geode_supported=bool(geode.get("supported", False)),
            geode_url=geode.get("url"),
            raw=item,
        )

    def to_manifest_item(self) -> dict[str, Any]:
        if self.raw:
            return dict(self.raw)

        return {
            "id": self.id,
            "display_name": self.display_name,
            "game_url": self.game_url,
            "geode": {
                "supported": self.geode_supported,
                "url": self.geode_url,
            },
        }

