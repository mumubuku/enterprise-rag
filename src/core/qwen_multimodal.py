from typing import List, Dict, Any, Optional
import base64
import os
import requests


class QwenMultiModalProcessor:
    """通义千问多模态处理器"""
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "qwen-vl-max"
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """使用通义千问VL处理图片"""
        try:
            print(f"[QwenImage] 开始处理图片: {image_path}")
            
            with open(image_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode()
            
            print(f"[QwenImage] 图片大小: {len(image_base64)} bytes")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "image": f"data:image/jpeg;base64,{image_base64}"
                                },
                                {
                                    "text": "请详细描述这张图片中的所有文字内容，包括标题、正文、表格等。请尽可能完整地提取所有文字信息。"
                                }
                            ]
                        }
                    ]
                },
                "parameters": {
                    "result_format": "message"
                }
            }
            
            print(f"[QwenImage] 调用通义千问VL API...")
            response = requests.post(self.base_url, headers=headers, json=payload)
            
            print(f"[QwenImage] API响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"API调用失败: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('message', '')}"
                    print(f"[QwenImage] API错误详情: {error_detail}")
                except:
                    pass
                return {"success": False, "error": error_msg}
            
            result = response.json()
            print(f"[QwenImage] API响应: {result}")
            
            if result.get("output") and result["output"].get("choices"):
                text = result["output"]["choices"][0]["message"]["content"][0]["text"]
                print(f"[QwenImage] 识别成功，文本长度: {len(text)}")
                print(f"[QwenImage] 识别文本: {text[:100]}...")
                
                return {
                    "success": True,
                    "text": text,
                    "type": "image",
                    "metadata": {
                        "file_path": image_path,
                        "file_size": os.path.getsize(image_path),
                        "model": self.model
                    }
                }
            else:
                error_msg = "无法提取图片文字"
                if result.get("message"):
                    error_msg += f": {result['message']}"
                print(f"[QwenImage] 识别失败: {error_msg}")
                return {"success": False, "error": error_msg}
        except Exception as e:
            print(f"[QwenImage] 图片处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": f"图片处理失败: {str(e)}"}
    
    def process_table(self, file_path: str) -> Dict[str, Any]:
        """使用通义千问处理表格"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.xlsx', '.xls', '.csv']:
                import pandas as pd
                
                if file_ext == '.csv':
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                markdown = df.to_markdown(index=False)
                
                return {
                    "success": True,
                    "tables": [{
                        "index": 0,
                        "data": df.to_dict('records'),
                        "markdown": markdown
                    }],
                    "type": "table",
                    "metadata": {
                        "file_path": file_path,
                        "file_size": os.path.getsize(file_path)
                    }
                }
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                with open(file_path, 'rb') as f:
                    image_base64 = base64.b64encode(f.read()).decode()
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "image": f"data:image/jpeg;base64,{image_base64}"
                                    },
                                    {
                                        "text": "请提取这张图片中的表格数据，并以Markdown格式输出。请保持表格的结构和内容完整。"
                                    }
                                ]
                            }
                        ]
                    },
                    "parameters": {
                        "result_format": "message"
                    }
                }
                
                response = requests.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("output") and result["output"].get("choices"):
                    markdown = result["output"]["choices"][0]["message"]["content"][0]["text"]
                    
                    return {
                        "success": True,
                        "tables": [{
                            "index": 0,
                            "markdown": markdown
                        }],
                        "type": "table",
                        "metadata": {
                            "file_path": file_path,
                            "file_size": os.path.getsize(file_path),
                            "model": self.model
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "无法提取表格"
                    }
            else:
                return {"success": False, "error": f"不支持的表格格式: {file_ext}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """使用通义听悟处理音频"""
        try:
            import subprocess
            import tempfile
            
            file_ext = os.path.splitext(audio_path)[1].lower()
            
            print(f"[QwenAudio] 开始处理音频文件: {audio_path}, 格式: {file_ext}")
            
            file_size = os.path.getsize(audio_path)
            print(f"[QwenAudio] 原始文件大小: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
            
            max_size = 10 * 1024 * 1024  # 10MB limit for base64 encoded data
            max_original_size = int(max_size / 1.37)  # Base64 encoding increases size by ~37%
            
            print(f"[QwenAudio] 最大允许原始文件大小: {max_original_size} bytes ({max_original_size / 1024 / 1024:.2f} MB)")
            
            if file_size > max_original_size:
                print(f"[QwenAudio] 文件超过限制，需要压缩")
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    tmp_audio_path = tmp.name
                
                try:
                    print(f"[QwenAudio] 压缩音频: {audio_path} -> {tmp_audio_path}")
                    subprocess.run([
                        'ffmpeg', '-i', audio_path,
                        '-vn', '-acodec', 'libmp3lame',
                        '-b:a', '64k',
                        '-y',
                        tmp_audio_path
                    ], check=True, capture_output=True)
                    
                    compressed_size = os.path.getsize(tmp_audio_path)
                    print(f"[QwenAudio] 压缩后文件大小: {compressed_size} bytes ({compressed_size / 1024 / 1024:.2f} MB)")
                    
                    if compressed_size > max_original_size:
                        print(f"[QwenAudio] 压缩后仍然超过限制，尝试更高质量压缩")
                        subprocess.run([
                            'ffmpeg', '-i', audio_path,
                            '-vn', '-acodec', 'libmp3lame',
                            '-b:a', '32k',
                            '-ar', '16000',
                            '-y',
                            tmp_audio_path
                        ], check=True, capture_output=True)
                        
                        compressed_size = os.path.getsize(tmp_audio_path)
                        print(f"[QwenAudio] 二次压缩后文件大小: {compressed_size} bytes ({compressed_size / 1024 / 1024:.2f} MB)")
                        
                        if compressed_size > max_original_size:
                            print(f"[QwenAudio] 二次压缩后仍然超过限制，无法处理")
                            return {"success": False, "error": f"音频文件过大，无法压缩到限制以下（原始: {file_size / 1024 / 1024:.2f}MB，压缩后: {compressed_size / 1024 / 1024:.2f}MB）"}
                    
                    audio_path = tmp_audio_path
                    print(f"[QwenAudio] 音频压缩完成")
                except Exception as e:
                    print(f"[QwenAudio] 音频压缩失败: {str(e)}")
                    return {"success": False, "error": f"音频压缩失败: {str(e)}"}
            
            if file_ext != '.mp3':
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    tmp_audio_path = tmp.name
                
                try:
                    print(f"[QwenAudio] 转换音频格式: {audio_path} -> {tmp_audio_path}")
                    subprocess.run([
                        'ffmpeg', '-i', audio_path,
                        '-vn', '-acodec', 'libmp3lame',
                        '-q:a', '2',
                        tmp_audio_path,
                        '-y'
                    ], check=True, capture_output=True)
                    audio_path = tmp_audio_path
                    print(f"[QwenAudio] 音频转换完成")
                except Exception as e:
                    print(f"[QwenAudio] 音频转换失败: {str(e)}")
                    return {"success": False, "error": f"音频转换失败: {str(e)}"}
            
            with open(audio_path, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode()
            
            print(f"[QwenAudio] 音频文件大小: {len(audio_base64)} bytes")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "paraformer-v2",
                "input": {
                    "file_urls": [f"data:audio/mp3;base64,{audio_base64}"]
                },
                "parameters": {
                    "format": "mp3",
                    "sample_rate": 16000
                }
            }
            
            url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
            
            print(f"[QwenAudio] 调用通义听悟API...")
            response = requests.post(url, headers=headers, json=payload)
            
            print(f"[QwenAudio] API响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"API调用失败: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('message', '')}"
                    print(f"[QwenAudio] API错误详情: {error_detail}")
                except:
                    pass
                return {"success": False, "error": error_msg}
            
            result = response.json()
            print(f"[QwenAudio] API响应: {result}")
            
            if result.get("output") and result["output"].get("result"):
                text = result["output"]["result"]
                print(f"[QwenAudio] 识别成功，文本长度: {len(text)}")
                print(f"[QwenAudio] 识别文本: {text[:100]}...")
                
                return {
                    "success": True,
                    "text": text,
                    "type": "audio",
                    "metadata": {
                        "file_path": audio_path,
                        "file_size": os.path.getsize(audio_path),
                        "model": "paraformer-v2"
                    }
                }
            else:
                error_msg = "无法识别音频"
                if result.get("message"):
                    error_msg += f": {result['message']}"
                print(f"[QwenAudio] 识别失败: {error_msg}")
                return {"success": False, "error": error_msg}
        except Exception as e:
            print(f"[QwenAudio] 音频处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": f"音频处理失败: {str(e)}"}
    
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
        elif file_ext in ['.xlsx', '.xls', '.csv']:
            return self.process_table(file_path)
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv']:
            return self.process_video(file_path)
        elif file_ext in ['.mp3', '.wav', '.m4a', '.flac']:
            return self.process_audio(file_path)
        else:
            return {"success": False, "error": f"不支持的文件类型: {file_ext}"}


class QwenDocumentProcessor:
    """通义千问文档处理器"""
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "qwen-vl-max"
    ):
        self.processor = QwenMultiModalProcessor(
            api_key=api_key,
            model=model
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