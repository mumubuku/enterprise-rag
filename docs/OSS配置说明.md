# OSS配置说明

## 1. 环境变量配置

在 `.env.local` 文件中添加以下配置：

```bash
# 文件存储类型：local 或 oss
FILE_STORAGE_TYPE=oss

# 阿里云OSS配置
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
ALIBABA_CLOUD_REGION_ID=oss-cn-hangzhou
OSS_BUCKET_NAME=your_bucket_name
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
```

## 2. 配置说明

### 2.1 必需配置项

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `FILE_STORAGE_TYPE` | 文件存储类型 | `local` 或 `oss` |
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | 阿里云AccessKey ID | `LTAI5t...` |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | 阿里云AccessKey Secret | `xxx...` |
| `ALIBABA_CLOUD_REGION_ID` | 阿里云区域ID | `oss-cn-hangzhou` |
| `OSS_BUCKET_NAME` | OSS存储桶名称 | `my-bucket` |

### 2.2 可选配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OSS_ENDPOINT` | OSS自定义端点 | 自动生成 |

## 3. 阿里云OSS配置步骤

### 3.1 创建阿里云账号

1. 访问 [阿里云官网](https://www.aliyun.com/)
2. 注册并登录账号

### 3.2 开通OSS服务

1. 进入控制台
2. 搜索"对象存储OSS"
3. 点击"立即开通"

### 3.3 创建AccessKey

1. 进入"访问控制" → "用户"
2. 创建用户或使用现有用户
3. 为用户创建AccessKey
4. 记录 `AccessKey ID` 和 `AccessKey Secret`

### 3.4 创建存储桶

1. 进入OSS控制台
2. 点击"创建Bucket"
3. 配置Bucket信息：
   - Bucket名称：例如 `enterprise-rag-files`
   - 区域：选择合适的区域（如华东1-杭州）
   - 读写权限：建议选择"私有"
   - 其他配置按需设置

### 3.5 配置权限

为用户添加OSS相关权限：
- `AliyunOSSFullAccess`：OSS完整权限（推荐）
- 或自定义权限：只读、只写等

## 4. 代码位置

### 4.1 OSS存储实现

**文件位置：** `src/services/file_storage_service.py`

**核心类：** `OSSFileStorage`

```python
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
```

### 4.2 配置文件

**文件位置：** `src/config/settings.py`

```python
class Settings(BaseSettings):
    # 文件存储配置
    file_storage_type: str = "local"
    oss_bucket_name: Optional[str] = None
    oss_endpoint: Optional[str] = None
    alibaba_cloud_access_key_id: Optional[str] = None
    alibaba_cloud_access_key_secret: Optional[str] = None
    alibaba_cloud_region_id: Optional[str] = "oss-cn-hangzhou"
```

### 4.3 文件存储服务

**文件位置：** `src/services/file_storage_service.py`

```python
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
        return self._backend
```

## 5. 使用方法

### 5.1 上传文件

```python
from src.services.file_storage_service import FileStorageService

# 初始化存储服务
storage_service = FileStorageService(storage_type="oss")

# 上传文件
file_path, file_url = await storage_service.backend.save_file(
    file_content=file_content,
    filename="document.pdf",
    subfolder="kb/123"
)
```

### 5.2 删除文件

```python
# 删除文件
success = await storage_service.backend.delete_file(file_path)
```

### 5.3 获取文件URL

```python
# 获取文件URL
file_url = await storage_service.backend.get_file_url(file_path)
```

## 6. 常见问题

### 6.1 OSS连接失败

**问题：** 无法连接到OSS

**解决方案：**
1. 检查AccessKey是否正确
2. 检查Bucket名称是否正确
3. 检查区域ID是否正确
4. 检查网络连接

### 6.2 权限不足

**问题：** 上传或删除文件时提示权限不足

**解决方案：**
1. 检查用户是否有OSS权限
2. 为用户添加 `AliyunOSSFullAccess` 权限
3. 检查Bucket的读写权限设置

### 6.3 文件上传失败

**问题：** 文件上传失败

**解决方案：**
1. 检查文件大小是否超过限制
2. 检查Bucket存储空间是否充足
3. 检查文件名是否包含非法字符

## 7. OSS区域列表

| 区域ID | 区域名称 |
|--------|----------|
| oss-cn-hangzhou | 华东1-杭州 |
| oss-cn-shanghai | 华东2-上海 |
| oss-cn-qingdao | 华北1-青岛 |
| oss-cn-beijing | 华北2-北京 |
| oss-cn-zhangjiakou | 华北3-张家口 |
| oss-cn-shenzhen | 华南1-深圳 |
| oss-cn-guangzhou | 华南2-广州 |
| oss-cn-chengdu | 西南1-成都 |
| oss-cn-hongkong | 中国香港 |
| oss-us-east-1 | 美国东部1 |
| oss-us-west-1 | 美国西部1 |

## 8. 安装依赖

使用OSS存储需要安装 `oss2` 库：

```bash
pip install oss2
```

## 9. 切换存储类型

### 从本地存储切换到OSS

1. 修改 `.env.local` 文件：
   ```bash
   FILE_STORAGE_TYPE=oss
   ```

2. 添加OSS配置（见第1节）

3. 重启后端服务

### 从OSS切换到本地存储

1. 修改 `.env.local` 文件：
   ```bash
   FILE_STORAGE_TYPE=local
   ```

2. 重启后端服务

## 10. 注意事项

1. **安全性：** 不要将AccessKey Secret提交到代码仓库
2. **成本：** OSS存储和流量会产生费用，注意监控使用量
3. **备份：** 建议定期备份重要文件
4. **权限：** 合理设置Bucket和文件的访问权限
5. **区域：** 选择离用户最近的区域以降低延迟