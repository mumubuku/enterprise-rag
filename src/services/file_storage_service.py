import os
import uuid
import aiofiles
from typing import Optional, Tuple
from pathlib import Path
from abc import ABC, abstractmethod
from src.config.settings import get_settings

settings = get_settings()


class FileStorageBackend(ABC):
    """文件存储后端抽象基类"""

    @abstractmethod
    async def save_file(self, file_content: bytes, filename: str, subfolder: str = "") -> Tuple[str, str]:
        """保存文件，返回 (file_path, file_url)"""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """获取文件访问URL"""
        pass


class LocalFileStorage(FileStorageBackend):
    """本地文件存储"""

    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or settings.upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_file(self, file_content: bytes, filename: str, subfolder: str = "") -> Tuple[str, str]:
        """保存文件到本地"""
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"

        if subfolder:
            target_dir = os.path.join(self.upload_dir, subfolder)
            os.makedirs(target_dir, exist_ok=True)
            file_path = os.path.join(target_dir, unique_filename)
        else:
            file_path = os.path.join(self.upload_dir, unique_filename)

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        file_url = f"/uploads/{subfolder}/{unique_filename}" if subfolder else f"/uploads/{unique_filename}"
        return file_path, file_url

    async def delete_file(self, file_path: str) -> bool:
        """删除本地文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    async def get_file_url(self, file_path: str) -> str:
        """获取本地文件URL"""
        relative_path = os.path.relpath(file_path, self.upload_dir)
        return f"/uploads/{relative_path}"


class OSSFileStorage(FileStorageBackend):
    """阿里云OSS文件存储"""

    def __init__(
        self,
        access_key_id: str = None,
        access_key_secret: str = None,
        bucket_name: str = None,
        endpoint: str = None,
        region: str = None
    ):
        self.access_key_id = access_key_id or settings.alibaba_cloud_access_key_id
        self.access_key_secret = access_key_secret or settings.alibaba_cloud_access_key_secret
        self.bucket_name = bucket_name or settings.oss_bucket_name
        self.endpoint = endpoint or settings.oss_endpoint
        self.region = region or settings.alibaba_cloud_region_id
        self._client = None

    @property
    def client(self):
        """懒加载OSS客户端"""
        if self._client is None:
            try:
                import oss2
                auth = oss2.Auth(self.access_key_id, self.access_key_secret)
                if self.endpoint:
                    self._client = oss2.Bucket(auth, self.endpoint, self.bucket_name)
                else:
                    self._client = oss2.Bucket(auth, f"https://oss-{self.region}.aliyuncs.com", self.bucket_name)
            except ImportError:
                raise ImportError("请安装 oss2 库: pip install oss2")
        return self._client

    async def save_file(self, file_content: bytes, filename: str, subfolder: str = "") -> Tuple[str, str]:
        """上传文件到OSS"""
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"

        if subfolder:
            object_key = f"{subfolder}/{unique_filename}"
        else:
            object_key = unique_filename

        self.client.put_object(object_key, file_content)

        file_path = object_key
        file_url = f"https://{self.bucket_name}.oss-{self.region}.aliyuncs.com/{object_key}"
        return file_path, file_url

    async def delete_file(self, file_path: str) -> bool:
        """删除OSS文件"""
        try:
            self.client.delete_object(file_path)
            return True
        except Exception:
            return False

    async def get_file_url(self, file_path: str) -> str:
        """获取OSS文件URL"""
        return f"https://{self.bucket_name}.oss-{self.region}.aliyuncs.com/{file_path}"


class FileStorageService:
    """文件存储服务"""

    def __init__(self, storage_type: str = "local"):
        self.storage_type = storage_type
        self._backend = None

    @property
    def backend(self) -> FileStorageBackend:
        """获取存储后端"""
        if self._backend is None:
            if self.storage_type == "local":
                self._backend = LocalFileStorage()
            elif self.storage_type == "oss":
                self._backend = OSSFileStorage()
            else:
                raise ValueError(f"不支持的存储类型: {self.storage_type}")
        return self._backend

    async def save_file(self, file_content: bytes, filename: str, subfolder: str = "") -> Tuple[str, str]:
        """保存文件"""
        return await self.backend.save_file(file_content, filename, subfolder)

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        return await self.backend.delete_file(file_path)

    async def get_file_url(self, file_path: str) -> str:
        """获取文件URL"""
        return await self.backend.get_file_url(file_path)


def get_file_storage_service(storage_type: str = None) -> FileStorageService:
    """获取文件存储服务实例"""
    if storage_type is None:
        storage_type = getattr(settings, 'file_storage_type', 'local')
    return FileStorageService(storage_type)