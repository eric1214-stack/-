import os
import random
from flask import current_app
from src.models.recognition.gemini_recognition import GeminiFoodRecognition

class FoodRecognitionSystem:
    """食品辨識系統，整合Gemini API"""
    
    def __init__(self):
        """初始化辨識系統"""
        # 從Flask應用配置中獲取Gemini API Key
        gemini_api_key = None
        try:
            gemini_api_key = current_app.config.get('GEMINI_API_KEY')
        except RuntimeError:
            # 如果不在應用上下文中，嘗試從環境變數讀取
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
        
        # 如果沒有API Key，使用模擬模式
        if not gemini_api_key or gemini_api_key == "YOUR_GEMINI_API_KEY":
            print("⚠️  警告：未設定 GEMINI_API_KEY，系統將使用模擬模式運行")
            self.gemini_recognizer = None
            self.use_mock_mode = True
        else:
            self.gemini_recognizer = GeminiFoodRecognition(api_key=gemini_api_key)
            self.use_mock_mode = False
    
    def process_images_batch(self, image_paths):
        """批量處理多張圖片，保持原始順序"""
        print(f"批量處理 {len(image_paths)} 張圖片")
        
        results = []
        for image_path in image_paths:
            results.append(self.process_image(image_path))
        
        return results
    
    def process_image(self, image_path):
        """處理單張圖片，使用Gemini API進行辨識"""
        print(f"處理圖片: {image_path}")
        
        # 模擬模式的辨識結果
        if self.use_mock_mode:
            mock_foods = [
                {
                    'food_name': '可口可樂 330ml',
                    'food_category': '飲料',
                    'expiry_date': '2025-12-15',
                    'barcode': '6901234567890'
                },
                {
                    'food_name': '上好佐幫 100g',
                    'food_category': '佐食',
                    'expiry_date': '2025-11-30',
                    'barcode': '6901234567891'
                },
                {
                    'food_name': '伊利丹牛奶 500ml',
                    'food_category': '飲料',
                    'expiry_date': '2026-01-20',
                    'barcode': '6901234567892'
                },
                {
                    'food_name': '沙其馬巴巴 200g',
                    'food_category': '佐食',
                    'expiry_date': '2025-12-01',
                    'barcode': '6901234567893'
                },
                {
                    'food_name': '紅牛牛奶 200ml',
                    'food_category': '乳製品',
                    'expiry_date': '2025-12-10',
                    'barcode': '6901234567894'
                }
            ]
            
            result = random.choice(mock_foods)
            return {
                'success': True,
                'food_name': result['food_name'],
                'food_category': result['food_category'],
                'expiry_date': result['expiry_date'],
                'barcode': result['barcode'],
                'image_path': image_path,
                'ai_confidence': 0.85
            }
        
        try:
            gemini_result = self.gemini_recognizer.recognize_food_item(image_path)
            
            if gemini_result["success"]:
                # 檢查是否所有關鍵資訊都為空，如果是，則視為辨識失敗
                if not (gemini_result.get("food_name") or 
                        gemini_result.get("expiry_date") or 
                        gemini_result.get("barcode") or 
                        gemini_result.get("category")):
                    return {
                        'success': False,
                        'error': '辨識失敗：Gemini API 未能辨識出任何有效資訊',
                        'image_path': image_path
                    }

                return {
                    'success': True,
                    'food_name': gemini_result.get('food_name', '未知食品'),
                    'food_category': gemini_result.get('category', '其他'),
                    'expiry_date': gemini_result.get('expiry_date'),
                    'barcode': gemini_result.get('barcode'),
                    'image_path': image_path
                }
            else:
                return {
                    'success': False,
                    'error': gemini_result.get('error', 'Gemini 辨識失敗'),
                    'image_path': image_path
                }
            
        except Exception as e:
            print(f"處理圖片時發生錯誤: {str(e)}")
            return {
                'success': False,
                'error': f'辨識失敗：系統錯誤，請稍後再試 ({str(e)})',
                'image_path': image_path
            }
