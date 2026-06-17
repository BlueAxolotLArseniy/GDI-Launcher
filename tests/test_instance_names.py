from __future__ import annotations

from gdi_launcher.services.instance_service import (
    get_instance_name_validation_error,
    is_valid_instance_name,
)


def test_accepts_regular_instance_name() -> None:
    assert is_valid_instance_name("GD 2.206")
    assert get_instance_name_validation_error("GD 2.206") == ""


def test_rejects_empty_instance_name() -> None:
    assert not is_valid_instance_name("   ")


def test_rejects_windows_reserved_name() -> None:
    assert not is_valid_instance_name("CON")
    assert not is_valid_instance_name("CON.txt")


def test_rejects_invalid_path_characters() -> None:
    assert not is_valid_instance_name("bad/name")
