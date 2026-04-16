import os
import requests
import json
from datetime import datetime
import google.generativeai as genai

# API 키 및 모델 설정
CLIENT_ID = os.environ.get("NAVID")
CLIENT_SECRET = os.environ.get("NAVPASS")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def get_ai_summary(text):
    try:
        clean_text = text.replace('<b>','').replace('</b>','').replace('&quot;','')
        prompt = f"다음 뉴스 내용을 2줄 이내로 핵심만 요약해줘: {clean_text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return text.replace('<b>','').replace('</b>','')[:80] + "..."

def fetch_data(keyword, count=10):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    params = {"query": keyword, "display": count, "sort": "date"}
    items = []
    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            for item in res.json().get('items', []):
                item['ai_summary'] = get_ai_summary(item['description'])
                items.append(item)
    except: pass
    return items

# 데이터 수집 (1, 2, 3번칸)
data = {
    "pane1": fetch_data("속보", 10),
    "pane2": {kw: fetch_data(kw, 10) for kw in ["산업부", "KIAT", "기후부", "산업혁신기반구축"]},
    "pane3": {kw: fetch_data(kw, 10) for kw in ["호르무즈", "트럼프", "유가", "코스피"]},
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
