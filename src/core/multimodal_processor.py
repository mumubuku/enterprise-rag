from typing import List, Dict, Any, Optional, Tuple
import os
import tempfile
from pathlib import Path
import base64


class MultiModalProcessor:
    """多模态处理器"""
    
    def __init__(
        self,
        use_ocr: bool = True,
        use_table_extraction: bool = True,
        use_video_subtitle: bool = True,
        use_audio_transcription: bool = True,
        use_aliyun_services: bool = False,
        use_qwen_model: bool = False,
        aliyun_access_key_id: str = None,
        aliyun_access_key_secret: str = None,
        aliyun_region_id: str = "cn-hangzhou",
        qwen_api_key: str = None
    ):
        self.use_ocr = use_ocr
        self.use_table_extraction = use_table_extraction
        self.use_video_subtitle = use_video_subtitle
        self.use_audio_transcription = use_audio_transcription
        self.use_aliyun_services = use_aliyun_services
        self.use_qwen_model = use_qwen_model
        
        self._ocr_engine = None
        self._whisper_model = None
        self._aliyun_processor = None
        self._qwen_processor = None
        
        if use_aliyun_services:
            from src.core.aliyun_multimodal import AliyunMultiModalProcessor
            self._aliyun_processor = AliyunMultiModalProcessor(
                access_key_id=aliyun_access_key_id,
                access_key_secret=aliyun_access_key_secret,
                region_id=aliyun_region_id
            )
        
        if use_qwen_model:
            from src.core.qwen_multimodal import QwenMultiModalProcessor
            self._qwen_processor = QwenMultiModalProcessor(
                api_key=qwen_api_key
            )
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """处理图片，提取文字"""
        if not self.use_ocr:
            return {"success": False, "error": "OCR未启用"}
        
        if self.use_qwen_model and self._qwen_processor:
            return self._qwen_processor.process_image(image_path)
        
        if self.use_aliyun_services and self._aliyun_processor:
            return self._aliyun_processor.process_image(image_path)
        
        try:
            text = self._extract_text_from_image(image_path)
            return {
                "success": True,
                "text": text,
                "type": "image",
                "metadata": {
                    "file_path": image_path,
                    "file_size": os.path.getsize(image_path)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_table(self, file_path: str) -> Dict[str, Any]:
        """处理表格文件"""
        if not self.use_table_extraction:
            return {"success": False, "error": "表格提取未启用"}
        
        if self.use_qwen_model and self._qwen_processor:
            return self._qwen_processor.process_table(file_path)
        
        if self.use_aliyun_services and self._aliyun_processor:
            return self._aliyun_processor.process_table(file_path)
        
        try:
            tables = self._extract_tables(file_path)
            return {
                "success": True,
                "tables": tables,
                "type": "table",
                "metadata": {
                    "file_path": file_path,
                    "file_size": os.path.getsize(file_path)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_video(self, video_path: str) -> Dict[str, Any]:
        """处理视频，提取字幕"""
        if not self.use_video_subtitle:
            return {"success": False, "error": "视频字幕提取未启用"}
        
        if self.use_qwen_model and self._qwen_processor:
            return self._qwen_processor.process_video(video_path)
        
        if self.use_aliyun_services and self._aliyun_processor:
            return self._aliyun_processor.process_video(video_path)
        
        try:
            subtitles = self._extract_video_subtitles(video_path)
            return {
                "success": True,
                "subtitles": subtitles,
                "type": "video",
                "metadata": {
                    "file_path": video_path,
                    "file_size": os.path.getsize(video_path)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """处理音频，转文字"""
        if not self.use_audio_transcription:
            return {"success": False, "error": "音频转文字未启用"}
        
        if self.use_qwen_model and self._qwen_processor:
            return self._qwen_processor.process_audio(audio_path)
        
        if self.use_aliyun_services and self._aliyun_processor:
            return self._aliyun_processor.process_audio(audio_path)
        
        try:
            text = self._transcribe_audio(audio_path)
            return {
                "success": True,
                "text": text,
                "type": "audio",
                "metadata": {
                    "file_path": audio_path,
                    "file_size": os.path.getsize(audio_path)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """从图片提取文字（使用Tesseract OCR）"""
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            return text.strip()
        except ImportError:
            raise ImportError("请安装依赖: pip install pytesseract pillow")
        except Exception as e:
            raise Exception(f"OCR处理失败: {str(e)}")
    
    def _extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """从文件提取表格"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return self._extract_tables_from_pdf(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return self._extract_tables_from_excel(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            return self._extract_tables_from_image(file_path)
        else:
            return []
    
    def _extract_tables_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """从PDF提取表格"""
        try:
            import camelot
            
            tables = camelot.read_pdf(pdf_path, pages='all')
            result = []
            
            for idx, table in enumerate(tables):
                df = table.df
                result.append({
                    "index": idx,
                    "data": df.to_dict('records'),
                    "markdown": df.to_markdown(index=False),
                    "page": table.page
                })
            
            return result
        except ImportError:
            raise ImportError("请安装依赖: pip install camelot-py[cv]")
        except Exception as e:
            raise Exception(f"PDF表格提取失败: {str(e)}")
    
    def _extract_tables_from_excel(self, excel_path: str) -> List[Dict[str, Any]]:
        """从Excel提取表格"""
        try:
            import pandas as pd
            
            excel_file = pd.ExcelFile(excel_path)
            result = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                result.append({
                    "sheet_name": sheet_name,
                    "data": df.to_dict('records'),
                    "markdown": df.to_markdown(index=False)
                })
            
            return result
        except ImportError:
            raise ImportError("请安装依赖: pip install pandas openpyxl")
        except Exception as e:
            raise Exception(f"Excel表格提取失败: {str(e)}")
    
    def _extract_tables_from_image(self, image_path: str) -> List[Dict[str, Any]]:
        """从图片提取表格"""
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            return [{
                "index": 0,
                "data": [],
                "markdown": text,
                "raw_text": text
            }]
        except ImportError:
            raise ImportError("请安装依赖: pip install pytesseract pillow")
        except Exception as e:
            raise Exception(f"图片表格提取失败: {str(e)}")
    
    def _extract_video_subtitles(self, video_path: str) -> List[Dict[str, Any]]:
        """从视频提取字幕"""
        try:
            import whisper
            
            if self._whisper_model is None:
                self._whisper_model = whisper.load_model("base")
            
            result = self._whisper_model.transcribe(video_path, language='zh')
            
            subtitles = []
            for segment in result['segments']:
                subtitles.append({
                    "start": segment['start'],
                    "end": segment['end'],
                    "text": segment['text'].strip()
                })
            
            return subtitles
        except ImportError:
            raise ImportError("请安装依赖: pip install openai-whisper")
        except Exception as e:
            raise Exception(f"视频字幕提取失败: {str(e)}")
    
    def _transcribe_audio(self, audio_path: str) -> str:
        """音频转文字"""
        try:
            import whisper
            
            if self._whisper_model is None:
                self._whisper_model = whisper.load_model("base")
            
            result = self._whisper_model.transcribe(audio_path, language='zh')
            return result['text'].strip()
        except ImportError:
            raise ImportError("请安装依赖: pip install openai-whisper")
        except Exception as e:
            raise Exception(f"音频转文字失败: {str(e)}")
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """根据文件类型自动处理"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return self.process_image(file_path)
        elif file_ext in ['.xlsx', '.xls', '.csv']:
            return self.process_table(file_path)
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv']:
            return self.process_video(file_path)
        elif file_ext in ['.mp3', '.wav', '.m4a', '.flac']:
            return self.process_audio(file_path)
        elif file_ext == '.pdf':
            return self._process_pdf(file_path)
        else:
            return {"success": False, "error": f"不支持的文件类型: {file_ext}"}
    
    def _process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """处理PDF文件（包含图片和表格）"""
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            result = {
                "success": True,
                "type": "pdf",
                "pages": [],
                "metadata": {
                    "file_path": pdf_path,
                    "file_size": os.path.getsize(pdf_path),
                    "page_count": len(doc)
                }
            }
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_data = {
                    "page_number": page_num + 1,
                    "text": page.get_text(),
                    "images": [],
                    "tables": []
                }
                
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                        tmp.write(image_bytes)
                        tmp_path = tmp.name
                    
                    try:
                        ocr_result = self.process_image(tmp_path)
                        if ocr_result["success"]:
                            page_data["images"].append({
                                "index": img_index,
                                "text": ocr_result["text"]
                            })
                    finally:
                        os.unlink(tmp_path)
                
                result["pages"].append(page_data)
            
            doc.close()
            return result
        except ImportError:
            raise ImportError("请安装依赖: pip install pymupdf")
        except Exception as e:
            raise Exception(f"PDF处理失败: {str(e)}")


class MultiModalDocumentProcessor:
    """多模态文档处理器"""
    
    def __init__(
        self,
        use_aliyun_services: bool = False,
        use_qwen_model: bool = False,
        aliyun_access_key_id: str = None,
        aliyun_access_key_secret: str = None,
        aliyun_region_id: str = "cn-hangzhou",
        qwen_api_key: str = None
    ):
        self.processor = MultiModalProcessor(
            use_aliyun_services=use_aliyun_services,
            use_qwen_model=use_qwen_model,
            aliyun_access_key_id=aliyun_access_key_id,
            aliyun_access_key_secret=aliyun_access_key_secret,
            aliyun_region_id=aliyun_region_id,
            qwen_api_key=qwen_api_key
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
        
        if result["type"] in ["image", "audio"]:
            text = result.get("text", "")
            chunks.extend(self._chunk_text(text, chunk_size, chunk_overlap))
        
        elif result["type"] == "table":
            for table in result.get("tables", []):
                markdown = table.get("markdown", "")
                chunks.extend(self._chunk_text(markdown, chunk_size, chunk_overlap))
        
        elif result["type"] == "video":
            for subtitle in result.get("subtitles", []):
                text = subtitle.get("text", "")
                chunks.append({
                    "content": text,
                    "metadata": {
                        "type": "video_subtitle",
                        "start": subtitle.get("start"),
                        "end": subtitle.get("end")
                    }
                })
        
        elif result["type"] == "pdf":
            for page in result.get("pages", []):
                page_text = page.get("text", "")
                chunks.extend(self._chunk_text(page_text, chunk_size, chunk_overlap))
                
                for image in page.get("images", []):
                    chunks.append({
                        "content": image.get("text", ""),
                        "metadata": {
                            "type": "pdf_image",
                            "page_number": page.get("page_number")
                        }
                    })
        
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