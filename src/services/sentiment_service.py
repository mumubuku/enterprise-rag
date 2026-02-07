from typing import Dict, List, Optional, Any
from src.core.llm import BaseLLM
import re
import json


class SentimentService:
    def __init__(self, llm: BaseLLM):
        self.llm = llm
        self._negative_keywords = [
            '投诉', '差评', '垃圾', '骗子', '退款', '退货', 
            '不满意', '糟糕', '失望', '生气', '愤怒', '讨厌',
            '慢', '拖延', '不负责', '态度差', '服务差',
            '问题', '故障', '坏了', '不能用', '失败'
        ]
        self._positive_keywords = [
            '满意', '好', '优秀', '棒', '赞', '感谢', '谢谢',
            '快速', '及时', '专业', '热情', '友好', '耐心',
            '解决', '帮助', '支持', '推荐', '喜欢'
        ]

    def analyze_sentiment(self, message: str) -> Dict[str, Any]:
        negative_score = self._calculate_keyword_score(message, self._negative_keywords)
        positive_score = self._calculate_keyword_score(message, self._positive_keywords)
        
        if negative_score > 0 or positive_score > 0:
            category, intensity = self._determine_sentiment_from_keywords(
                negative_score, positive_score
            )
        else:
            category, intensity = self._analyze_with_llm(message)
        
        keywords = self._extract_sentiment_keywords(message)
        
        return {
            'category': category,
            'intensity': intensity,
            'keywords': keywords,
            'negative_score': negative_score,
            'positive_score': positive_score
        }

    def _calculate_keyword_score(self, message: str, keywords: List[str]) -> float:
        score = 0.0
        for keyword in keywords:
            count = message.count(keyword)
            if count > 0:
                weight = 1.0
                if keyword in ['投诉', '差评', '垃圾', '骗子']:
                    weight = 2.0
                elif keyword in ['满意', '优秀', '棒', '赞']:
                    weight = 1.5
                score += count * weight
        return score

    def _determine_sentiment_from_keywords(self, negative_score: float, positive_score: float) -> tuple:
        if negative_score > positive_score:
            intensity = min(10, int(negative_score * 2))
            return 'negative', intensity
        elif positive_score > negative_score:
            intensity = min(10, int(positive_score * 2))
            return 'positive', intensity
        else:
            return 'neutral', 1

    def _analyze_with_llm(self, message: str) -> tuple:
        prompt = f"""分析以下用户消息的情绪：

用户消息：{message}

请返回JSON格式：
{{
    "category": "positive（正面）/negative（负面）/neutral（中性）",
    "intensity": 1-10之间的情绪强度
}}

如果消息没有明显的情绪倾向，返回 neutral 和 1。"""

        try:
            response = self.llm.generate(prompt, temperature=0.1)
            result = self._parse_sentiment_response(response)
            return result['category'], result['intensity']
        except Exception as e:
            print(f"LLM情感分析失败: {e}")
            return 'neutral', 1

    def _parse_sentiment_response(self, response: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                category = result.get('category', 'neutral')
                if category not in ['positive', 'negative', 'neutral']:
                    category = 'neutral'
                intensity = int(result.get('intensity', 1))
                intensity = max(1, min(10, intensity))
                return {
                    'category': category,
                    'intensity': intensity
                }
        except Exception as e:
            print(f"解析情感响应失败: {e}")
        
        return {
            'category': 'neutral',
            'intensity': 1
        }

    def _extract_sentiment_keywords(self, message: str) -> List[str]:
        keywords = []
        
        for keyword in self._negative_keywords:
            if keyword in message:
                keywords.append(keyword)
        
        for keyword in self._positive_keywords:
            if keyword in message:
                keywords.append(keyword)
        
        return keywords

    def should_transfer_to_human(self, sentiment: Dict, conversation_history: Optional[List[Dict]] = None) -> bool:
        if sentiment['category'] == 'negative' and sentiment['intensity'] >= 7:
            return True
        
        if conversation_history and len(conversation_history) >= 3:
            recent_messages = conversation_history[-5:]
            negative_count = sum(
                1 for msg in recent_messages 
                if msg.get('sentiment', {}).get('category') == 'negative'
            )
            if negative_count >= 3:
                return True
        
        if '投诉' in sentiment.get('keywords', []):
            return True
        
        return False

    def get_sentiment_summary(self, messages: List[Dict]) -> Dict[str, Any]:
        if not messages:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'avg_intensity': 0,
                'dominant_sentiment': 'neutral'
            }
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        total_intensity = 0
        
        for msg in messages:
            sentiment = msg.get('sentiment', {})
            category = sentiment.get('category', 'neutral')
            intensity = sentiment.get('intensity', 1)
            
            if category == 'positive':
                positive_count += 1
            elif category == 'negative':
                negative_count += 1
            else:
                neutral_count += 1
            
            total_intensity += intensity
        
        total = len(messages)
        avg_intensity = total_intensity / total if total > 0 else 0
        
        dominant_sentiment = 'neutral'
        if positive_count > negative_count and positive_count > neutral_count:
            dominant_sentiment = 'positive'
        elif negative_count > positive_count and negative_count > neutral_count:
            dominant_sentiment = 'negative'
        
        return {
            'total': total,
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count,
            'avg_intensity': round(avg_intensity, 2),
            'dominant_sentiment': dominant_sentiment
        }

    def get_escalation_recommendation(self, sentiment: Dict, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        should_escalate = self.should_transfer_to_human(sentiment, conversation_history)
        
        if should_escalate:
            reasons = []
            
            if sentiment['category'] == 'negative' and sentiment['intensity'] >= 7:
                reasons.append(f"用户情绪负面且强度高（{sentiment['intensity']}/10）")
            
            if conversation_history:
                recent_messages = conversation_history[-5:]
                negative_count = sum(
                    1 for msg in recent_messages 
                    if msg.get('sentiment', {}).get('category') == 'negative'
                )
                if negative_count >= 3:
                    reasons.append(f"连续{negative_count}条负面情绪消息")
            
            if '投诉' in sentiment.get('keywords', []):
                reasons.append("用户提到投诉")
            
            priority = 'high' if sentiment['intensity'] >= 8 else 'medium'
            
            return {
                'should_escalate': True,
                'priority': priority,
                'reasons': reasons,
                'suggested_action': '转接人工客服'
            }
        
        return {
            'should_escalate': False,
            'priority': 'low',
            'reasons': [],
            'suggested_action': '继续AI对话'
        }