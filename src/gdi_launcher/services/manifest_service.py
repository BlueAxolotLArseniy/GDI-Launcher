from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from gdi_launcher.config import GITHUB_MANIFEST_URL, VERSIONS_FILE


class ManifestService:
    def __init__(
        self,
        manifest_url: str = GITHUB_MANIFEST_URL,
        local_manifest_path: str | Path = VERSIONS_FILE,
    ) -> None:
        self.manifest_url = manifest_url
        self.local_manifest_path = Path(local_manifest_path)

    def load_versions(self, timeout: int = 5) -> list[dict[str, Any]]:
        with urllib.request.urlopen(self.manifest_url, timeout=timeout) as response:
            raw_json = response.read().decode("utf-8")

        return self._parse_versions(raw_json)

    def load_local_versions(self) -> list[dict[str, Any]]:
        raw_json = self.local_manifest_path.read_text(encoding="utf-8")
        return self._parse_versions(raw_json)

    def load_versions_or_fallback(self, timeout: int = 5) -> list[dict[str, Any]]:
        try:
            return self.load_versions(timeout=timeout)
        except Exception as error:
            print(f"[-] Не удалось загрузить манифест: {error}")

        try:
            return self.load_local_versions()
        except Exception as error:
            print(f"[-] Не удалось загрузить локальный манифест: {error}")

        return [
            {
                "id": "offline_fallback",
                "display_name": "Нет подключения к сети (проверьте интернет)",
                "game_url": "",
                "geode": {
                    "supported": False,
                    "url": None,
                },
            }
        ]

    def _parse_versions(self, raw_json: str) -> list[dict[str, Any]]:
        data = json.loads(raw_json)
        versions = data.get("versions", [])

        if not isinstance(versions, list):
            raise ValueError("Manifest field 'versions' must be a list.")

        return versions

