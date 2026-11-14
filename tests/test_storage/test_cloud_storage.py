"""Offline adapter tests; never create a real Google client or read credentials."""
import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def adapter(monkeypatch):
    storage = ModuleType('google.cloud.storage')
    storage.Client = MagicMock()
    cloud = ModuleType('google.cloud')
    cloud.storage = storage
    google = ModuleType('google')
    google.cloud = cloud
    for name, module in [('google', google), ('google.cloud', cloud),
                         ('google.cloud.storage', storage)]:
        monkeypatch.setitem(sys.modules, name, module)
    path = Path(__file__).resolve().parents[2] / 'src/storage/cloud_storage.py'
    cls = runpy.run_path(str(path))['CloudStorage']
    obj = cls('test-bucket')
    storage.Client.assert_called_once_with()
    storage.Client.return_value.bucket.assert_called_once_with('test-bucket')
    return obj


def test_upload_and_download_use_explicit_paths(adapter):
    adapter.upload_image('local.jpg', 'remote/image.jpg')
    adapter.bucket.blob.assert_called_with('remote/image.jpg')
    adapter.bucket.blob.return_value.upload_from_filename.assert_called_once_with('local.jpg')
    adapter.download_image('remote/image.jpg', 'download.jpg')
    adapter.bucket.blob.assert_called_with('remote/image.jpg')
    adapter.bucket.blob.return_value.download_to_filename.assert_called_once_with('download.jpg')


def test_list_and_delete(adapter):
    adapter.bucket.list_blobs.return_value = [SimpleNamespace(name='a.jpg'), SimpleNamespace(name='b.jpg')]
    assert adapter.list_images() == ['a.jpg', 'b.jpg']
    adapter.delete_image('a.jpg')
    adapter.bucket.blob.assert_called_once_with('a.jpg')
    adapter.bucket.blob.return_value.delete.assert_called_once_with()


def test_list_failure_returns_empty_list_and_reports_error(adapter, capsys):
    adapter.bucket.list_blobs.side_effect = RuntimeError('offline test failure')
    assert adapter.list_images() == []
    assert 'offline test failure' in capsys.readouterr().out


@pytest.mark.parametrize('method,args,operation', [
    ('upload_image', ('local.jpg', 'remote.jpg'), 'upload_from_filename'),
    ('download_image', ('remote.jpg', 'local.jpg'), 'download_to_filename'),
    ('delete_image', ('remote.jpg',), 'delete'),
])
def test_mutation_failures_are_reported(adapter, capsys, method, args, operation):
    getattr(adapter.bucket.blob.return_value, operation).side_effect = RuntimeError('offline test failure')
    getattr(adapter, method)(*args)
    assert 'offline test failure' in capsys.readouterr().out
