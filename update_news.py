import os
import requests
import json
import re
from datetime import datetime
from google import genai

CLIENT_ID = os.environ.get("NAVID")
CLIENT_SECRET = os.environ.get("NAVPASS")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_ai_summary(title, description):
    try:
        clean_desc = re.sub('<[^>]*>', '', description).replace('&quot;', '"')
        prompt = f"뉴스 제목: {title}\n내용: {clean_desc}\n\n위 내용을 2줄 이내로 핵심만 요약해. 문장만 출력해."
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        summary = response.text.strip()
        if len(summary) > 120 or "요약" in summary[:5]:
            return clean_desc[:90] + "..."
        return summary
    except:
        return re.sub('<[^>]*>', '', description)[:90] + "..."

def fetch_news(keyword, count=15, apply_filter=True):
    """apply_filter=False 면 제목/본문 키워드 대조 없이 바로 가져옴"""
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    params = {"query": keyword, "display": 100 if apply_filter else count, "sort": "date"}
    
    items = []
    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            for item in res.json().get('items', []):
                title_plain = re.sub('<[^>]*>', '', item['title'])
                desc_plain = re.sub('<[^>]*>', '', item['description'])
                
                # 💡 필터 적용 여부에 따른 분기
                if not apply_filter or (keyword.lower() in title_plain.lower() and keyword.lower() in desc_plain.lower()):
                    try:
                        dt = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
                        item['formatted_date'] = dt.strftime('%m월 %d일, %H시 %M분')
                    except: item['formatted_date'] = item['pubDate']
                        
                    item['ai_summary'] = get_ai_summary(title_plain, desc_plain)
                    items.append(item)
                    if len(items) >= count: break
    except: pass
    return items

# --- 수집 실행 ---
# 💡 1번칸: 필터 해제 (apply_filter=False)
pane1_news = fetch_news("속보", 15, apply_filter=False)

# 2, 3번칸: 필터 유지 (기본값 True)
pane2_kw = ["산업부", "KIAT", "기후부", "산업혁신기반구축"]
pane2_data = {kw: fetch_news(kw, 10) for kw in pane2_kw}

pane3_kw = ["호르무즈", "트럼프", "유가", "코스피"]
pane3_data = {kw: fetch_news(kw, 10) for kw in pane3_kw}

final_data = { "pane1": pane1_news, "pane2": pane2_data, "pane3": pane3_data, "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S") }
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)
