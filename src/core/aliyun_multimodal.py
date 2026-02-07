from typing import List, Dict, Any, Optional
import base64
import os


class AliyunMultiModalProcessor:
    """阿里云多模态处理器"""
    
    def __init__(
        self,
        access_key_id: str = None,
        access_key_secret: str = None,
        region_id: str = "cn-hangzhou"
    ):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region_id = region_id
        
        self._ocr_client = None
        self._document_client = None
        self._nls_client = None
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """使用阿里云OCR处理图片"""
        try:
            import alibabacloud_ocr_api20210707 as ocr
            import alibabacloud_tea_openapi as open_api
            
            config = open_api.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret
            )
            config.endpoint = f'ocr-api.{self.region_id}.aliyuncs.com'
            
            client = ocr.Client(config)
            
            with open(image_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode()
            
            request = ocr.RecognizeGeneralRequest()
            request.body = image_base64
            
            response = client.recognize_general(request)
            
            if response.status_code == 200:
                text = ""
                if response.body.data:
                    for result in response.body.data:
                        if result.content:
                            text += result.content + "\n"
                
                return {
                    "success": True,
                    "text": text.strip(),
                    "type": "image",
                    "metadata": {
                        "file_path": image_path,
                        "file_size": os.path.getsize(image_path)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"OCR失败: {response.status_code}"
                }
        except ImportError:
            return {"success": False, "error": "请安装依赖: pip install alibabacloud-ocr-api20210707"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_table(self, file_path: str) -> Dict[str, Any]:
        """使用阿里云文档智能服务处理表格"""
        try:
            import alibabacloud_docmind_api20220729 as docmind
            import alibabacloud_tea_openapi as open_api
            
            config = open_api.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret
            )
            config.endpoint = f'docmind-api.{self.region_id}.aliyuncs.com'
            
            client = docmind.Client(config)
            
            with open(file_path, 'rb') as f:
                file_base64 = base64.b64encode(f.read()).decode()
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                request = docmind.GetTableStructureRequest()
                request.file_name = os.path.basename(file_path)
                request.file_base64 = file_base64
                request.file_type = file_ext[1:]
                
                response = client.get_table_structure(request)
                
                if response.status_code == 200:
                    tables = []
                    if response.body.tables:
                        for table in response.body.tables:
                            tables.append({
                                "index": table.index,
                                "headers": table.headers,
                                "rows": table.rows,
                                "markdown": self._table_to_markdown(table)
                            })
                    
                    return {
                        "success": True,
                        "tables": tables,
                        "type": "table",
                        "metadata": {
                            "file_path": file_path,
                            "file_size": os.path.getsize(file_path)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"表格提取失败: {response.status_code}"
                    }
            else:
                return {"success": False, "error": f"不支持的表格格式: {file_ext}"}
        except ImportError:
            return {"success": False, "error": "请安装依赖: pip install alibabacloud-docmind-api20220729"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _table_to_markdown(self, table) -> str:
        """将表格转换为Markdown"""
        if not table.headers or not table.rows:
            return ""
        
        markdown = "| " + " | ".join(table.headers) + " |\n"
        markdown += "| " + " | ".join(["---"] * len(table.headers)) + " |\n"
        
        for row in table.rows:
            markdown += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
        return markdown
    
    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """使用阿里云语音识别处理音频"""
        try:
            import alibabacloud_nls_cloud_meta as nls
            import alibabacloud_tea_openapi as open_api
            
            config = open_api.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret
            )
            config.endpoint = f'nls-meta.{self.region_id}.aliyuncs.com'
            
            client = nls.Client(config)
            
            with open(audio_path, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode()
            
            request = nls.CreateTranscriptionRequest()
            request.file_url = f"data:audio/mp3;base64,{audio_base64}"
            request.format = "mp3"
            request.sample_rate = 16000
            request.model = "paraformer-v2"
            
            response = client.create_transcription(request)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "text": response.body.result,
                    "type": "audio",
                    "metadata": {
                        "file_path": audio_path,
                        "file_size": os.path.getsize(audio_path)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"语音识别失败: {response.status_code}"
                }
        except ImportError:
            return {"success": False, "error": "请安装依赖: pip install alibabacloud-nls-cloud-meta"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_video(self, video_path: str) -> Dict[str, Any]:
        """处理视频（提取音频后转文字）"""
        try:
            import subprocess
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tmp_audio_path = tmp.name
            
            try:
                subprocess.run([
                    'ffmpeg', '-i', video_path,
                    '-vn', '-acodec', 'libmp3lame',
                    '-q:a', '2',
                    tmp_audio_path,
                    '-y'
                ], check=True, capture_output=True)
                
                result = self.process_audio(tmp_audio_path)
                
                if result["success"]:
                    result["type"] = "video"
                    result["metadata"]["original_file"] = video_path
                
                return result
            finally:
                if os.path.exists(tmp_audio_path):
                    os.unlink(tmp_audio_path)
        except Exception as e:
            return {"success": False, "error": f"视频处理失败: {str(e)}"}
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """根据文件类型自动处理"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return self.process_image(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return self.process_table(file_path)
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv']:
            return self.process_video(file_path)
        elif file_ext in ['.mp3', '.wav', '.m4a', '.flac']:
            return self.process_audio(file_path)
        else:
            return {"success": False, "error": f"不支持的文件类型: {file_ext}"}


class AliyunDocumentProcessor:
    """阿里云文档处理器"""
    
    def __init__(
        self,
        access_key_id: str = None,
        access_key_secret: str = None,
        region_id: str = "cn-hangzhou"
    ):
        self.processor = AliyunMultiModalProcessor(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=region_id
        )
    
    def process_and_chunk(
        self,
        file_path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """处理文件并分块"""
        result = self.processor.process_file(file_path)
        
        if not result["success"]:
            return []
        
        chunks = []
        
        if result["type"] in ["image", "audio", "video"]:
            text = result.get("text", "")
            chunks.extend(self._chunk_text(text, chunk_size, chunk_overlap))
        
        elif result["type"] == "table":
            for table in result.get("tables", []):
                markdown = table.get("markdown", "")
                chunks.extend(self._chunk_text(markdown, chunk_size, chunk_overlap))
        
        return chunks
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """文本分块"""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk_text = text[start:end]
            
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    "type": "text",
                    "start": start,
                    "end": end
                }
            })
            
            start = end - chunk_overlap
        
        return chunks