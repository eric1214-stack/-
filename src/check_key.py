import os
# 讀取環境變數中的金鑰
api_key = os.environ.get('GEMINI_API_KEY')

if api_key:
    print("成功讀取到環境變數！")
    # 為了安全，我們只顯示金鑰的頭尾幾個字元
    print(f"金鑰開頭: {api_key[:4]}")
    print(f"金鑰結尾: {api_key[-4:]}")
else:
    print("錯誤：沒有讀取到名為 'GEMINI_API_KEY' 的環境變數。")
    print("程式將會使用預設值，導致 API 呼叫失敗。")