import os
import requests
import json
import re
from datetime import datetime
# 💡 2026년 표준: 신형 google-genai 패키지 사용
from google import genai

# 1. API 및 신형 클라이언트 초기화
CLIENT_ID = os.environ.get("NAVID")
CLIENT_SECRET = os.environ.get("NAVPASS")
# 구형 configure 방식 대신 Client 객체 생성
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_ai_summary(title, description):
    """Gemini 2.5 Flash를 사용하여 군더더기 없는 2줄 요약 생성"""
    try:
        clean_desc = re.sub('<[^>]*>', '', description).replace('&quot;', '"')
        # AI가 쓸데없는 서두를 떼지 못하도록 강력한 페르소나 주입
        prompt = (
            f"뉴스 제목: {title}\n내용: {clean_desc}\n\n"
            "위 내용을 2줄 이내로 핵심만 요약해. "
            "반드시 요약된 문장만 출력하고, '요약해 드리겠습니다' 같은 말은 절대 하지 마."
        )
        
        # 신규 SDK 호출 문법
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        summary = response.text.strip()
        
        # 안전장치: AI가 기어코 말을 걸었을 경우 정제
        if len(summary) > 120 or "요약" in summary[:10]:
            return clean_desc[:90] + "..."
        return summary
    except Exception as e:
        print(f"AI 요약 실패: {e}")
        return re.sub('<[^>]*>', '', description)[:90] + "... (원문 요약)"

def fetch_filtered_news(keyword, count=15):
    """연구원님 조건: 제목에 키워드 포함 AND 요약문에 1회 이상 등장"""
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    params = {"query": keyword, "display": 70, "sort": "date"} # 필터 통과를 위해 넉넉히 수집
    
    filtered_items = []
    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            for item in res.json().get('items', []):
                # HTML 태그 제거된 순수 텍스트 추출
                title_plain = re.sub('<[^>]*>', '', item['title'])
                desc_plain = re.sub('<[^>]*>', '', item['description'])
                
                # 💡 핵심 필터 로직
                is_in_title = keyword.lower() in title_plain.lower()
                is_in_desc = keyword.lower() in desc_plain.lower()
                
                if is_in_title and is_in_desc:
                    # 날짜 형식: 04월 16일, 09시 16분
                    try:
                        dt = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
                        item['formatted_date'] = dt.strftime('%m월 %d일, %H시 %M분')
                    except:
                        item['formatted_date'] = item['pubDate']
                        
                    item['ai_summary'] = get_ai_summary(title_plain, desc_plain)
                    filtered_items.append(item)
                    if len(filtered_items) >= count: break
    except: pass
    return filtered_items

# --- 데이터 수집 실행 ---
# 1번칸: 속보 (필터 없이 15개)
pane1_news = fetch_filtered_news("속보", 15)

# 2번칸: 부처/기관 (정밀 필터 적용)
pane2_kw = ["산업부", "KIAT", "기후부", "산업혁신기반구축"]
pane2_data = {kw: fetch_filtered_news(kw, 10) for kw in pane2_kw}

# 3번칸: 모니터링 (정밀 필터 적용)
pane3_kw = ["호르무즈", "트럼프", "유가", "코스피"]
pane3_data = {kw: fetch_filtered_news(kw, 10) for kw in pane3_kw}

final_data = {
    "pane1": pane1_news,
    "pane2": pane2_data,
    "pane3": pane3_data,
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"✅ {datetime.now()} - 2026년형 업데이트 성공")
