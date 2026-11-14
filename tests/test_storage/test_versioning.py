"""Filesystem regression tests for the legacy version metadata helper."""
import json
from datetime import datetime
from src.storage.versioning import VersioningManager


def test_unknown_image_has_no_versions(tmp_path):
    manager = VersioningManager(str(tmp_path))
    assert manager.get_versions('missing') == []
    assert json.loads((tmp_path / 'versions.json').read_text()) == {}


def test_versions_survive_restart_and_remain_separate(tmp_path):
    manager = VersioningManager(str(tmp_path))
    first = manager.create_version_data('image-a', 'Initial upload')
    second = manager.create_version_data('image-a', 'Corrected description')
    other = manager.create_version_data('image-b', 'Another image')
    manager.add_version('image-a', first)
    manager.add_version('image-b', other)
    manager.add_version('image-a', second)
    restored = VersioningManager(str(tmp_path))
    assert restored.get_versions('image-a') == [first, second]
    assert restored.get_versions('image-b') == [other]
    assert first['image_id'] == 'image-a'
    assert first['description'] == 'Initial upload'
    datetime.fromisoformat(first['timestamp'])
