from __future__ import annotations

import json

from gdi_launcher.services.manifest_service import ManifestService


def test_load_local_versions(tmp_path) -> None:
    manifest_path = tmp_path / "versions.json"
    manifest_path.write_text(
        json.dumps(
            {
                "versions": [
                    {
                        "id": "2.206",
                        "display_name": "Geometry Dash 2.206",
                        "game_url": "https://example.com/gd.zip",
                        "geode": {
                            "supported": True,
                            "url": "https://example.com/geode.zip",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    service = ManifestService(local_manifest_path=manifest_path)

    versions = service.load_local_versions()

    assert versions[0]["id"] == "2.206"
    assert versions[0]["geode"]["supported"] is True


def test_rejects_manifest_with_non_list_versions(tmp_path) -> None:
    manifest_path = tmp_path / "versions.json"
    manifest_path.write_text(json.dumps({"versions": {}}), encoding="utf-8")
    service = ManifestService(local_manifest_path=manifest_path)

    try:
        service.load_local_versions()
    except ValueError as error:
        assert "versions" in str(error)
    else:
        raise AssertionError("Expected invalid manifest to raise ValueError.")

