"""
Document storage service.

Saves generated files (vouchers, invoices, proformas) to:
  - Local: uploads/documents/<request_id>/<filename>
  - Cloud (GCS): gs://<bucket>/documents/<request_id>/<filename>

Routes should call DocumentStorage.save() and record the returned path
in the inbound_document table.
"""
import os
import uuid
from datetime import datetime


class DocumentStorage:
    """Abstraction over local filesystem and GCS for document storage."""

    def __init__(self, app=None):
        self._app = app
        self._bucket = None

    def init_app(self, app):
        self._app = app
        bucket_name = os.environ.get('GCS_BUCKET_NAME')
        if bucket_name:
            try:
                from google.cloud import storage as gcs
                client = gcs.Client()
                self._bucket = client.bucket(bucket_name)
                app.logger.info(f'DocumentStorage: using GCS bucket {bucket_name}')
            except ImportError:
                app.logger.warning('google-cloud-storage not installed — falling back to local storage')
            except Exception as e:
                app.logger.warning(f'GCS init failed ({e}) — falling back to local storage')

    @property
    def _upload_root(self):
        if self._app:
            return os.path.join(self._app.root_path, '..', 'uploads', 'documents')
        return os.path.join(os.getcwd(), 'uploads', 'documents')

    def save(self, file_bytes: bytes, request_id: int, doc_type: str,
             original_filename: str) -> tuple[str, str]:
        """Save file bytes and return (relative_path, stored_filename).

        stored_filename: UUID-based unique name
        relative_path: path relative to upload_root for serving
        """
        ext = os.path.splitext(original_filename)[1].lower() or '.bin'
        stored_filename = f"{doc_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        relative_path = os.path.join(str(request_id), stored_filename)

        if self._bucket:
            return self._save_gcs(file_bytes, relative_path, stored_filename)
        return self._save_local(file_bytes, relative_path, stored_filename)

    def _save_local(self, file_bytes: bytes, relative_path: str,
                    stored_filename: str) -> tuple[str, str]:
        full_path = os.path.join(self._upload_root, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(file_bytes)
        return relative_path, stored_filename

    def _save_gcs(self, file_bytes: bytes, relative_path: str,
                  stored_filename: str) -> tuple[str, str]:
        blob_name = f'documents/{relative_path}'
        blob = self._bucket.blob(blob_name)
        blob.upload_from_string(file_bytes)
        return f'gcs:{blob_name}', stored_filename

    def get_full_path(self, relative_path: str) -> str:
        """Return absolute local path for serving. GCS paths return as-is."""
        if relative_path.startswith('gcs:'):
            return relative_path
        return os.path.join(self._upload_root, relative_path)

    def delete(self, relative_path: str) -> bool:
        """Delete stored file. Returns True if deleted, False if not found."""
        if relative_path.startswith('gcs:'):
            blob_name = relative_path[4:]
            try:
                self._bucket.blob(blob_name).delete()
                return True
            except Exception:
                return False
        full_path = os.path.join(self._upload_root, relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False


document_storage = DocumentStorage()
