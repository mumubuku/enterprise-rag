from typing import Dict, List, Optional, Any
from src.core.llm import BaseLLM
from src.models.database import Intent, Slot
import re
import json


class IntentService:
    def __init__(self, llm: BaseLLM, db_manager=None):
        self.llm = llm
        self.db_manager = db_manager
        self._intent_cache = {}
        self._load_intents()

    def _load_intents(self):
        if self.db_manager:
            session = self.db_manager.get_session()
            try:
                intents = session.query(Intent).filter(Intent.is_active == True).all()
                for intent in intents:
                    self._intent_cache[intent.name] = {
                        'id': intent.id,
                        'name': intent.name,
                        'description': intent.description,
                        'category': intent.category,
                        'training_examples': intent.training_examples or []
                    }
            finally:
                session.close()

    def classify_intent(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        intent_list = list(self._intent_cache.keys())
        
        if not intent_list:
            return {
                'intent': 'general_inquiry',
                'confidence': 0.5,
                'category': 'general'
            }

        intent_descriptions = "\n".join([
            f"- {name}: {info.get('description', '')}"
            for name, info in self._intent_cache.items()
        ])

        prompt = f"""你是一个智能客服意图识别系统。请分析用户消息并识别其意图。

用户消息：{user_message}

可能的意图类别：
{intent_descriptions}

请返回JSON格式：
{{
    "intent": "最匹配的意图名称",
    "confidence": 0.0-1.0之间的置信度,
    "category": "意图类别",
    "reasoning": "识别理由"
}}

如果用户消息不匹配任何预定义意图，返回 "general_inquiry"。"""

        try:
            response = self.llm.generate(prompt, temperature=0.1)
            result = self._parse_intent_response(response)
            
            if result['intent'] not in self._intent_cache and result['intent'] != 'general_inquiry':
                result['intent'] = 'general_inquiry'
            
            return result
        except Exception as e:
            print(f"意图识别失败: {e}")
            return {
                'intent': 'general_inquiry',
                'confidence': 0.3,
                'category': 'general',
                'reasoning': '识别失败，使用默认意图'
            }

    def _parse_intent_response(self, response: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'intent': result.get('intent', 'general_inquiry'),
                    'confidence': float(result.get('confidence', 0.5)),
                    'category': result.get('category', 'general'),
                    'reasoning': result.get('reasoning', '')
                }
        except Exception as e:
            print(f"解析意图响应失败: {e}")
        
        return {
            'intent': 'general_inquiry',
            'confidence': 0.5,
            'category': 'general',
            'reasoning': '解析失败'
        }

    def extract_slots(self, user_message: str, intent: str) -> Dict[str, Any]:
        slots = self._get_slot_definitions(intent)
        extracted_slots = {}
        
        for slot in slots:
            slot_name = slot['name']
            slot_type = slot['type']
            
            if slot_type == 'order_id':
                order_id = self._extract_order_id(user_message)
                if order_id:
                    extracted_slots[slot_name] = order_id
            elif slot_type == 'phone':
                phone = self._extract_phone(user_message)
                if phone:
                    extracted_slots[slot_name] = phone
            elif slot_type == 'email':
                email = self._extract_email(user_message)
                if email:
                    extracted_slots[slot_name] = email
            elif slot_type == 'product_name':
                product = self._extract_product_name(user_message)
                if product:
                    extracted_slots[slot_name] = product
            elif slot_type == 'amount':
                amount = self._extract_amount(user_message)
                if amount:
                    extracted_slots[slot_name] = amount
            elif slot_type == 'date':
                date = self._extract_date(user_message)
                if date:
                    extracted_slots[slot_name] = date
        
        return extracted_slots

    def _get_slot_definitions(self, intent: str) -> List[Dict]:
        if self.db_manager:
            session = self.db_manager.get_session()
            try:
                intent_obj = session.query(Intent).filter(Intent.name == intent).first()
                if intent_obj:
                    return [
                        {
                            'name': slot.name,
                            'type': slot.type,
                            'required': slot.required,
                            'prompt_template': slot.prompt_template
                        }
                        for slot in intent_obj.slots
                    ]
            finally:
                session.close()
        
        return self._get_default_slots(intent)

    def _get_default_slots(self, intent: str) -> List[Dict]:
        default_slots = {
            'query_order': [
                {'name': 'order_id', 'type': 'order_id', 'required': True}
            ],
            'refund_request': [
                {'name': 'order_id', 'type': 'order_id', 'required': True},
                {'name': 'reason', 'type': 'text', 'required': True}
            ],
            'product_inquiry': [
                {'name': 'product_name', 'type': 'product_name', 'required': True}
            ],
            'complaint': [
                {'name': 'order_id', 'type': 'order_id', 'required': False},
                {'name': 'issue', 'type': 'text', 'required': True}
            ]
        }
        return default_slots.get(intent, [])

    def _extract_order_id(self, text: str) -> Optional[str]:
        patterns = [
            r'订单号[:：]?\s*([A-Za-z0-9]+)',
            r'订单[:：]?\s*([A-Za-z0-9]+)',
            r'([A-Z]{2}\d{10,})',
            r'(\d{10,})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        patterns = [
            r'1[3-9]\d{9}',
            r'\d{3,4}-\d{7,8}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_product_name(self, text: str) -> Optional[str]:
        keywords = ['产品', '商品', '购买', '买']
        for keyword in keywords:
            if keyword in text:
                parts = text.split(keyword)
                if len(parts) > 1:
                    return parts[1].strip()[:50]
        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        pattern = r'(\d+(?:\.\d+)?)\s*(?:元|块|钱)'
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def get_missing_slots(self, intent: str, extracted_slots: Dict) -> List[str]:
        slot_definitions = self._get_slot_definitions(intent)
        missing = []
        
        for slot in slot_definitions:
            if slot['required'] and slot['name'] not in extracted_slots:
                missing.append(slot['name'])
        
        return missing

    def generate_slot_prompt(self, intent: str, missing_slot: str) -> str:
        slot_definitions = self._get_slot_definitions(intent)
        
        for slot in slot_definitions:
            if slot['name'] == missing_slot and slot.get('prompt_template'):
                return slot['prompt_template']
        
        prompts = {
            'order_id': '请提供您的订单号',
            'phone': '请提供您的联系电话',
            'email': '请提供您的邮箱地址',
            'product_name': '请问您想了解哪个产品？',
            'reason': '请说明退款原因',
            'issue': '请详细描述您遇到的问题',
            'amount': '请说明涉及金额'
        }
        
        return prompts.get(missing_slot, f'请提供{missing_slot}')

    def create_intent(self, name: str, description: str, category: str, training_examples: List[str]) -> Intent:
        if self.db_manager:
            session = self.db_manager.get_session()
            try:
                intent = Intent(
                    name=name,
                    description=description,
                    category=category,
                    training_examples=training_examples
                )
                session.add(intent)
                session.commit()
                session.refresh(intent)
                
                self._intent_cache[name] = {
                    'id': intent.id,
                    'name': intent.name,
                    'description': intent.description,
                    'category': intent.category,
                    'training_examples': training_examples
                }
                
                return intent
            finally:
                session.close()
        return None

    def list_intents(self) -> List[Dict]:
        return list(self._intent_cache.values())