import os
import pytest
from app.services.storage import DocumentStorage


@pytest.fixture
def storage(tmp_path, app):
    s = DocumentStorage(app)
    # Override upload root to tmp_path for testing
    s._upload_root_override = str(tmp_path)
    return s


def test_save_returns_path_and_filename(app, tmp_path):
    s = DocumentStorage()
    s._app = app
    # Monkey-patch upload root
    original = s._upload_root
    import unittest.mock as mock
    with mock.patch.object(type(s), '_upload_root', new_callable=lambda: property(lambda self: str(tmp_path))):
        path, name = s.save(b'PDF content', request_id=42, doc_type='voucher', original_filename='test.pdf')
        assert '42' in path
        assert name.endswith('.pdf')
        assert 'voucher' in name


def test_save_creates_file_on_disk(app, tmp_path):
    s = DocumentStorage()
    s._app = app
    import unittest.mock as mock
    with mock.patch.object(type(s), '_upload_root', new_callable=lambda: property(lambda self: str(tmp_path))):
        path, _ = s.save(b'test data', request_id=1, doc_type='invoice', original_filename='inv.pdf')
        full = s.get_full_path(path)
        assert os.path.exists(full)
        assert open(full, 'rb').read() == b'test data'


def test_delete_removes_file(app, tmp_path):
    s = DocumentStorage()
    s._app = app
    import unittest.mock as mock
    with mock.patch.object(type(s), '_upload_root', new_callable=lambda: property(lambda self: str(tmp_path))):
        path, _ = s.save(b'to delete', request_id=99, doc_type='proforma', original_filename='p.pdf')
        full = s.get_full_path(path)
        assert os.path.exists(full)
        result = s.delete(path)
        assert result is True
        assert not os.path.exists(full)
