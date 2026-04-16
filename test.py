import os
from google import genai

# 본인의 API 키를 직접 넣으세요 (테스트용)
client = genai.Client(api_key="AIzaSyDc1BpjVqBOR4jVyFWXMbZvn_nYnQSpZXc")

print("🔍 사용 가능한 Gemini 모델 목록 검색 중...")
for m in client.models.list_models():
    # 이름에 lite나 flash가 들어간 것만 필터링해서 출력
    if 'lite' in m.name.lower() or 'flash' in m.name.lower():
        print(f"진짜 API 이름: {m.name}")