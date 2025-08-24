import requests
import json
from typing import Dict, Any, Optional
from config import Config

class AIProcessor:
    def __init__(self):
        self.config = Config()
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Optional
            "X-Title": "AI Document Processor"  # Optional
        }
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create a structured prompt for field extraction and classification"""
        prompt = f"""
You are an AI document processing assistant. Analyze the following document text and extract structured information.

Document Text:
{text}

Please provide a JSON response with the following structure:
{{
    "document_type": "invoice|receipt|contract|letter|form|other",
    "confidence_score": 0.0-1.0,
    "extracted_fields": {{
        "names": ["list of person/company names found"],
        "dates": ["list of dates found in YYYY-MM-DD format"],
        "amounts": ["list of monetary amounts with currency"],
        "addresses": ["list of addresses found"],
        "phone_numbers": ["list of phone numbers found"],
        "email_addresses": ["list of email addresses found"],
        "key_terms": ["important keywords or phrases"]
    }},
    "summary": "A concise 2-3 sentence summary of the document content",
    "metadata": {{
        "language": "detected language",
        "page_count": estimated_pages,
        "word_count": estimated_word_count
    }}
}}

Important: Respond ONLY with valid JSON. Do not include any explanation or additional text.
"""
        return prompt
    
    def process_document_text(self, text: str) -> Dict[str, Any]:
        """Process extracted text using AI to get structured data"""
        try:
            prompt = self._create_extraction_prompt(text)
            
            payload = {
                "model": self.config.AI_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Parse the JSON response
            try:
                structured_data = json.loads(ai_response)
                return self._validate_and_clean_response(structured_data)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from response
                return self._extract_json_from_text(ai_response)
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing document with AI: {str(e)}")
    
    def _validate_and_clean_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the AI response"""
        cleaned_data = {
            "document_type": data.get("document_type", "other"),
            "confidence_score": float(data.get("confidence_score", 0.0)),
            "extracted_fields": {
                "names": data.get("extracted_fields", {}).get("names", []),
                "dates": data.get("extracted_fields", {}).get("dates", []),
                "amounts": data.get("extracted_fields", {}).get("amounts", []),
                "addresses": data.get("extracted_fields", {}).get("addresses", []),
                "phone_numbers": data.get("extracted_fields", {}).get("phone_numbers", []),
                "email_addresses": data.get("extracted_fields", {}).get("email_addresses", []),
                "key_terms": data.get("extracted_fields", {}).get("key_terms", [])
            },
            "summary": data.get("summary", ""),
            "metadata": {
                "language": data.get("metadata", {}).get("language", "unknown"),
                "page_count": data.get("metadata", {}).get("page_count", 1),
                "word_count": data.get("metadata", {}).get("word_count", 0)
            }
        }
        
        return cleaned_data
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text if direct parsing fails"""
        try:
            # Find JSON-like content between braces
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
            else:
                # Fallback with basic structure
                return self._create_fallback_response(text)
        
        except:
            return self._create_fallback_response(text)
    
    def _create_fallback_response(self, text: str) -> Dict[str, Any]:
        """Create a basic fallback response when AI processing fails"""
        word_count = len(text.split()) if text else 0
        
        return {
            "document_type": "other",
            "confidence_score": 0.5,
            "extracted_fields": {
                "names": [],
                "dates": [],
                "amounts": [],
                "addresses": [],
                "phone_numbers": [],
                "email_addresses": [],
                "key_terms": []
            },
            "summary": f"Document processed with basic extraction. Contains approximately {word_count} words.",
            "metadata": {
                "language": "unknown",
                "page_count": 1,
                "word_count": word_count
            }
        }
    
    def classify_document_type(self, text: str) -> str:
        """Quick document type classification"""
        text_lower = text.lower()
        
        # Simple keyword-based classification as fallback
        if any(word in text_lower for word in ['invoice', 'bill', 'amount due', 'total:']):
            return 'invoice'
        elif any(word in text_lower for word in ['receipt', 'paid', 'transaction', 'purchase']):
            return 'receipt'
        elif any(word in text_lower for word in ['contract', 'agreement', 'terms', 'party']):
            return 'contract'
        elif any(word in text_lower for word in ['dear', 'sincerely', 'regards']):
            return 'letter'
        elif any(word in text_lower for word in ['form', 'application', 'please fill']):
            return 'form'
        else:
            return 'other'

def get_ai_processor():
    """Factory function to get AI processor instance"""
    return AIProcessor()
