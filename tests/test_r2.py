"""Tests for R2Storage — mock boto3 network calls, no real R2."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# R2Storage requires boto3 + botocore at import time (even with network
# calls mocked). Skip cleanly if the 'storage' extra wasn't installed.
pytest.importorskip("boto3")
pytest.importorskip("botocore")


@pytest.fixture
def _r2_env(monkeypatch):
    monkeypatch.setenv("R2_ENDPOINT", "https://fake.r2.cloudflarestorage.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "fake-access")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "fake-secret")
    monkeypatch.setenv("R2_PUBLIC_URL", "https://pub-fake.r2.dev")
    monkeypatch.setenv("R2_BUCKET", "test-bucket")
    from auto_podcast_crs import config
    config.get_settings.cache_clear()


@pytest.fixture
def _mock_boto3(monkeypatch):
    """Install a fake boto3 module into sys.modules so the import succeeds."""
    fake_boto3 = MagicMock()
    fake_client = MagicMock()
    fake_boto3.client.return_value = fake_client
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    yield fake_client


def test_r2_upload_returns_public_url(_r2_env, _mock_boto3, tmp_path: Path):
    from auto_podcast_crs.storage.r2 import R2Storage

    src = tmp_path / "episode.mp3"
    src.write_bytes(b"fake audio")

    r2 = R2Storage()
    url = r2.upload(src, "episodes/test.mp3", content_type="audio/mpeg")

    assert url == "https://pub-fake.r2.dev/episodes/test.mp3"
    _mock_boto3.upload_file.assert_called_once()
    args, kwargs = _mock_boto3.upload_file.call_args
    assert args[0] == str(src)
    assert args[1] == "test-bucket"
    assert args[2] == "episodes/test.mp3"
    assert kwargs["ExtraArgs"]["ContentType"] == "audio/mpeg"


def test_r2_upload_guesses_content_type(_r2_env, _mock_boto3, tmp_path: Path):
    from auto_podcast_crs.storage.r2 import R2Storage

    src = tmp_path / "episode.mp3"
    src.write_bytes(b"fake")
    R2Storage().upload(src, "episodes/a.mp3")

    _, kwargs = _mock_boto3.upload_file.call_args
    assert kwargs["ExtraArgs"]["ContentType"] == "audio/mpeg"


def test_r2_upload_missing_file_raises(_r2_env, _mock_boto3, tmp_path: Path):
    from auto_podcast_crs.storage.r2 import R2Storage
    with pytest.raises(FileNotFoundError):
        R2Storage().upload(tmp_path / "nope.mp3", "x.mp3")


def test_r2_missing_env_raises(monkeypatch):
    # Don't set env vars
    for var in ["R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_PUBLIC_URL"]:
        monkeypatch.delenv(var, raising=False)
    from auto_podcast_crs import config
    config.get_settings.cache_clear()

    from auto_podcast_crs.storage.r2 import R2Storage
    with pytest.raises(RuntimeError, match="R2Storage missing env vars"):
        R2Storage()


def test_r2_exists_returns_false_for_missing_key(_r2_env, _mock_boto3):
    from botocore.exceptions import ClientError

    _mock_boto3.head_object.side_effect = ClientError(
        {"Error": {"Code": "404"}}, "HeadObject"
    )

    from auto_podcast_crs.storage.r2 import R2Storage
    assert R2Storage().exists("does-not-exist") is False


def test_r2_exists_returns_true_for_present_key(_r2_env, _mock_boto3):
    _mock_boto3.head_object.return_value = {}

    from auto_podcast_crs.storage.r2 import R2Storage
    assert R2Storage().exists("present-key") is True
