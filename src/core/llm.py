from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from typing import List, Optional, Dict, Any, Iterator
from abc import ABC, abstractmethod
from src.config.settings import get_settings
import dashscope
import zhipuai

settings = get_settings()


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages: List[BaseMessage], **kwargs) -> str:
        pass

    @abstractmethod
    def stream(self, messages: List[BaseMessage], **kwargs) -> Iterator[str]:
        pass


class OpenAILLM(BaseLLM):
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None
    ):
        self.model = model or settings.openai_model
        self.temperature = temperature or settings.openai_temperature
        self.max_tokens = max_tokens or settings.openai_max_tokens
        self.api_key = api_key or settings.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            openai_api_key=self.api_key
        )

    def generate(self, messages: List[BaseMessage], **kwargs) -> str:
        response = self.llm.invoke(messages, **kwargs)
        return response.content

    def stream(self, messages: List[BaseMessage], **kwargs) -> Iterator[str]:
        for chunk in self.llm.stream(messages, **kwargs):
            yield chunk.content


class AlibabaLLM(BaseLLM):
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None
    ):
        self.model = model or settings.dashscope_model
        self.temperature = temperature or settings.openai_temperature
        self.max_tokens = max_tokens or settings.openai_max_tokens
        self.api_key = api_key or settings.dashscope_api_key
        
        if not self.api_key:
            raise ValueError("DashScope API key is required")
        
        dashscope.api_key = self.api_key

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        converted = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                converted.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                converted.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                converted.append({"role": "system", "content": msg.content})
        return converted

    def generate(self, messages: List[BaseMessage], **kwargs) -> str:
        dashscope_messages = self._convert_messages(messages)
        response = dashscope.Generation.call(
            model=self.model,
            messages=dashscope_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs
        )
        
        if response.status_code == 200:
            if response.output.choices:
                return response.output.choices[0].message.content
            elif response.output.text:
                return response.output.text
            else:
                raise Exception(f"Failed to call Alibaba LLM: No valid response content - {response}")
        else:
            raise Exception(f"Failed to call Alibaba LLM: {response}")

    def stream(self, messages: List[BaseMessage], **kwargs) -> Iterator[str]:
        dashscope_messages = self._convert_messages(messages)
        responses = dashscope.Generation.call(
            model=self.model,
            messages=dashscope_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
            **kwargs
        )
        
        for response in responses:
            if response.status_code == 200 and response.output.choices:
                yield response.output.choices[0].message.content


class ZhipuLLM(BaseLLM):
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None
    ):
        self.model = model or settings.zhipuai_model
        self.temperature = temperature or settings.openai_temperature
        self.max_tokens = max_tokens or settings.openai_max_tokens
        self.api_key = api_key or settings.zhipuai_api_key
        
        if not self.api_key:
            raise ValueError("ZhipuAI API key is required")
        
        zhipuai.api_key = self.api_key

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        converted = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                converted.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                converted.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                converted.append({"role": "system", "content": msg.content})
        return converted

    def generate(self, messages: List[BaseMessage], **kwargs) -> str:
        zhipu_messages = self._convert_messages(messages)
        response = zhipuai.model_api.invoke(
            model=self.model,
            messages=zhipu_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs
        )
        
        if response and 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0]['message']['content']
        else:
            raise Exception(f"Failed to call ZhipuAI LLM: {response}")

    def stream(self, messages: List[BaseMessage], **kwargs) -> Iterator[str]:
        zhipu_messages = self._convert_messages(messages)
        response = zhipuai.model_api.invoke(
            model=self.model,
            messages=zhipu_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
            **kwargs
        )
        
        for chunk in response:
            if chunk and 'choices' in chunk and len(chunk['choices']) > 0:
                yield chunk['choices'][0]['delta'].get('content', '')


class LLMFactory:
    @staticmethod
    def create(
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseLLM:
        provider = provider.lower()
        
        if provider == "openai":
            return OpenAILLM(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        elif provider == "alibaba" or provider == "dashscope":
            return AlibabaLLM(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        elif provider == "zhipuai" or provider == "zhipu":
            return ZhipuLLM(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


def get_llm(provider: str = "openai", **kwargs) -> BaseLLM:
    return LLMFactory.create(provider, **kwargs)


class LLMManager:
    def __init__(self):
        self._llms: Dict[str, BaseLLM] = {}

    def get_llm(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseLLM:
        cache_key = f"{provider}_{model}_{temperature}_{max_tokens}"
        
        if cache_key not in self._llms:
            self._llms[cache_key] = LLMFactory.create(
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        return self._llms[cache_key]

    def clear_cache(self):
        self._llms.clear()


llm_manager = LLMManager()