import os
from supabase import create_client


class StorageUtil:
    @staticmethod
    def _get_client():
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url:
            raise ValueError("SUPABASE_URL is not configured")

        if not service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is not configured")

        return create_client(supabase_url, service_role_key)

    @staticmethod
    def upload_bytes(
        bucket: str,
        path: str,
        file_bytes: bytes,
        content_type: str = "application/octet-stream"
    ) -> dict:
        client = StorageUtil._get_client()

        client.storage.from_(bucket).upload(
            path,
            file_bytes,
            {"content-type": content_type}
        )

        public_url = client.storage.from_(bucket).get_public_url(path)

        return {
            "path": path,
            "url": public_url
        }

    @staticmethod
    def delete_file(bucket: str, path: str) -> None:
        if not path:
            return

        client = StorageUtil._get_client()
        client.storage.from_(bucket).remove([path])