from langchain_community.document_loaders import (
    PDFMinerLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    UnstructuredCSVLoader,
    PyPDFLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Optional, Dict, Any
import os
import hashlib
from datetime import datetime
from src.core.multimodal_processor import MultiModalDocumentProcessor


class DocumentProcessor:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        enable_multimodal: bool = True,
        use_aliyun_services: bool = None,
        use_qwen_model: bool = None,
        aliyun_access_key_id: str = None,
        aliyun_access_key_secret: str = None,
        aliyun_region_id: str = None,
        qwen_api_key: str = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.enable_multimodal = enable_multimodal
        
        if separators is None:
            separators = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=separators
        )
        
        if enable_multimodal:
            from src.config.settings import get_settings
            settings = get_settings()
            
            use_aliyun = use_aliyun_services if use_aliyun_services is not None else settings.use_aliyun_services
            use_qwen = use_qwen_model if use_qwen_model is not None else settings.use_qwen_model
            ak_id = aliyun_access_key_id or settings.alibaba_cloud_access_key_id
            ak_secret = aliyun_access_key_secret or settings.alibaba_cloud_access_key_secret
            region = aliyun_region_id or settings.alibaba_cloud_region_id
            qwen_key = qwen_api_key or settings.qwen_api_key or settings.dashscope_api_key
            
            self.multimodal_processor = MultiModalDocumentProcessor(
                use_aliyun_services=use_aliyun,
                use_qwen_model=use_qwen,
                aliyun_access_key_id=ak_id,
                aliyun_access_key_secret=ak_secret,
                aliyun_region_id=region,
                qwen_api_key=qwen_key
            )
        else:
            self.multimodal_processor = None
        
        self.supported_formats = {
            ".pdf": self._load_pdf,
            ".docx": self._load_docx,
            ".doc": self._load_docx,
            ".txt": self._load_text,
            ".md": self._load_markdown,
            ".html": self._load_html,
            ".htm": self._load_html,
            ".xlsx": self._load_excel,
            ".xls": self._load_excel,
            ".pptx": self._load_pptx,
            ".ppt": self._load_pptx,
            ".csv": self._load_csv,
        }
        
        if enable_multimodal:
            self.multimodal_formats = {
                ".png": self._load_multimodal,
                ".jpg": self._load_multimodal,
                ".jpeg": self._load_multimodal,
                ".gif": self._load_multimodal,
                ".bmp": self._load_multimodal,
                ".mp4": self._load_multimodal,
                ".avi": self._load_multimodal,
                ".mov": self._load_multimodal,
                ".mkv": self._load_multimodal,
                ".mp3": self._load_multimodal,
                ".wav": self._load_multimodal,
                ".m4a": self._load_multimodal,
                ".flac": self._load_multimodal,
            }
            self.supported_formats.update(self.multimodal_formats)

    def _load_pdf(self, file_path: str) -> List[Document]:
        try:
            loader = PyPDFLoader(file_path)
            return loader.load()
        except Exception:
            loader = PDFMinerLoader(file_path)
            return loader.load()

    def _load_docx(self, file_path: str) -> List[Document]:
        loader = Docx2txtLoader(file_path)
        return loader.load()

    def _load_text(self, file_path: str) -> List[Document]:
        loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()

    def _load_markdown(self, file_path: str) -> List[Document]:
        loader = UnstructuredMarkdownLoader(file_path)
        return loader.load()

    def _load_html(self, file_path: str) -> List[Document]:
        loader = UnstructuredHTMLLoader(file_path)
        return loader.load()

    def _load_excel(self, file_path: str) -> List[Document]:
        loader = UnstructuredExcelLoader(file_path)
        return loader.load()

    def _load_pptx(self, file_path: str) -> List[Document]:
        loader = UnstructuredPowerPointLoader(file_path)
        return loader.load()

    def _load_csv(self, file_path: str) -> List[Document]:
        loader = UnstructuredCSVLoader(file_path)
        return loader.load()
    
    def _load_multimodal(self, file_path: str) -> List[Document]:
        """加载多模态文件"""
        if not self.multimodal_processor:
            return []
        
        try:
            chunks = self.multimodal_processor.process_and_chunk(
                file_path,
                self.chunk_size,
                self.chunk_overlap
            )
            
            documents = []
            for chunk in chunks:
                metadata = {
                    "source": file_path,
                    "file_type": os.path.splitext(file_path)[1],
                    "chunk_type": chunk.get("metadata", {}).get("type", "text")
                }
                metadata.update(chunk.get("metadata", {}))
                
                documents.append(Document(
                    page_content=chunk["content"],
                    metadata=metadata
                ))
            
            return documents
        except Exception as e:
            print(f"多模态文件处理失败: {e}")
            return []

    def load_document(self, file_path: str) -> Optional[List[Document]]:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        try:
            loader_func = self.supported_formats[file_extension]
            documents = loader_func(file_path)
            
            for doc in documents:
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata["source"] = file_path
                doc.metadata["file_type"] = file_extension
                doc.metadata["file_name"] = os.path.basename(file_path)
                doc.metadata["file_size"] = os.path.getsize(file_path)
                doc.metadata["loaded_at"] = datetime.utcnow().isoformat()
            
            return documents
        except Exception as e:
            raise Exception(f"Error loading document {file_path}: {str(e)}")

    def split_document(
        self,
        document: Document,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        chunks = self.text_splitter.split_documents([document])
        
        for idx, chunk in enumerate(chunks):
            if metadata:
                chunk.metadata.update(metadata)
            chunk.metadata["chunk_index"] = idx
            chunk.metadata["chunk_id"] = self._generate_chunk_id(document.metadata.get("source", ""), idx)
        
        return chunks

    def process_file(
        self,
        file_path: str,
        original_filename: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        documents = self.load_document(file_path)
        if not documents:
            return []
        
        all_chunks = []
        for doc in documents:
            if original_filename:
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata["file_name"] = original_filename
            chunks = self.split_document(doc, additional_metadata)
            all_chunks.extend(chunks)
        
        return all_chunks

    def process_directory(
        self,
        directory_path: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        all_chunks = []
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    chunks = self.process_file(file_path, additional_metadata)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Warning: Failed to process {file_path}: {str(e)}")
                    continue
        
        return all_chunks

    def _generate_chunk_id(self, source: str, chunk_index: int) -> str:
        content = f"{source}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_stat = os.stat(file_path)
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1].lower()
        
        return {
            "file_name": file_name,
            "file_path": file_path,
            "file_size": file_stat.st_size,
            "file_type": file_extension,
            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "is_supported": file_extension in self.supported_formats
        }

    def is_supported_format(self, file_path: str) -> bool:
        file_extension = os.path.splitext(file_path)[1].lower()
        return file_extension in self.supported_formats

    def get_supported_formats(self) -> List[str]:
        return list(self.supported_formats.keys())