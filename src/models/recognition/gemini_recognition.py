import google.generativeai as genai
from PIL import Image
import io
import re
import json
from datetime import datetime

class GeminiFoodRecognition:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def recognize_food_item(self, image_path):
        try:
            img = Image.open(image_path).convert('RGB')
            
            prompt = """請從這張圖片中辨識出食品的品名、可能的生產或到期日期（格式為YYYY-MM-DD，如果有多個日期請提供最接近當前的日期）、條碼（如果存在，請提供數字）、以及食品的類別（例如：飲料、罐頭、零食、乳製品、肉類、蔬菜、水果、烘焙、調味料、冷凍食品、其他）。請以JSON格式返回結果，如果無法辨識則對應欄位留空。範例：{"food_name": "可口可樂", "expiry_date": "2025-12-31", "barcode": "4710000000000", "category": "飲料"}"""

            response = self.model.generate_content([prompt, img])
            text_response = response.text.strip()

            # 嘗試解析JSON
            try:
                # 清理回應文本，移除可能的markdown格式
                if text_response.startswith('```json'):
                    text_response = text_response[7:]
                if text_response.endswith('```'):
                    text_response = text_response[:-3]
                text_response = text_response.strip()
                
                result = json.loads(text_response)
            except json.JSONDecodeError:
                # 如果不是標準JSON，嘗試從文本中提取資訊
                result = self._parse_text_response(text_response)

            # 處理日期格式，確保為 YYYY-MM-DD
            if 'expiry_date' in result and result['expiry_date']:
                try:
                    # 嘗試多種日期格式解析
                    date_str = result['expiry_date']
                    parsed_date = None
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m-%d-%Y', '%m/%d/%Y', '%Y%m%d']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                    if parsed_date:
                        result['expiry_date'] = parsed_date.strftime('%Y-%m-%d')
                    else:
                        result['expiry_date'] = None # 無法解析則設為空
                except Exception:
                    result['expiry_date'] = None

            return {
                'success': True,
                'food_name': result.get('food_name'),
                'expiry_date': result.get('expiry_date'),
                'barcode': result.get('barcode'),
                'category': result.get('category'),
                'raw_response': text_response # 儲存原始回應以便調試
            }

        except Exception as e:
            print(f"Gemini 辨識時發生錯誤: {str(e)}")
            return {
                'success': False,
                'error': f'Gemini 辨識失敗: {str(e)}',
                'food_name': None,
                'expiry_date': None,
                'barcode': None,
                'category': None
            }

    def _parse_text_response(self, text):
        # 嘗試從非JSON格式的文本中提取資訊
        food_name = re.search(r'品名[:：\s]*([^\n,]+)', text)
        expiry_date = re.search(r'日期[:：\s]*(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}|\d{8})', text)
        barcode = re.search(r'條碼[:：\s]*(\d+)', text)
        category = re.search(r'類別[:：\s]*([^\n,]+)', text)

        return {
            'food_name': food_name.group(1).strip() if food_name else None,
            'expiry_date': expiry_date.group(1).strip() if expiry_date else None,
            'barcode': barcode.group(1).strip() if barcode else None,
            'category': category.group(1).strip() if category else None,
        }



