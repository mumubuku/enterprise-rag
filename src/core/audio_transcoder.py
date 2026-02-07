from typing import List, Dict, Any, Optional
import base64
import os
import requests


class QwenAudioTranscoder:
    """通义千问音频转码器"""
    
    def __init__(
        self,
        api_key: str = None
    ):
        self.api_key = api_key
    
    def transcode_audio(
        self,
        audio_path: str,
        target_bitrate: str = "64k",
        target_sample_rate: int = 16000
    ) -> Optional[str]:
        """使用阿里云音频转码API压缩音频"""
        try:
            with open(audio_path, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": {
                    "file_urls": [f"data:audio/mp3;base64,{audio_base64}"]
                },
                "parameters": {
                    "format": "mp3",
                    "bitrate": target_bitrate,
                    "sample_rate": target_sample_rate
                }
            }
            
            url = "https://dashscope.aliyuncs.com/api/v1/services/audio/transcoding"
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                print(f"[AudioTranscoder] 转码失败: {response.status_code}")
                return None
            
            result = response.json()
            
            if result.get("output") and result.get("output").get("file_url"):
                return result["output"]["file_url"]
            
            return None
        except Exception as e:
            print(f"[AudioTranscoder] 转码异常: {str(e)}")
            return None
    
    def download_transcoded_audio(self, file_url: str, output_path: str) -> bool:
        """下载转码后的音频"""
        try:
            response = requests.get(file_url)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"[AudioTranscoder] 下载失败: {str(e)}")
            return False