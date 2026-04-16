import os
import requests
import json
import re
from datetime import datetime, timedelta, timezone
from google import genai

# 1. 설정
CLIENT_ID = os.environ.get("NAVID")
CLIENT_SECRET = os.environ.get("NAVPASS")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 💡 한국 표준시(KST) 설정
KST = timezone(timedelta(hours=9))

def get_batch_summaries(news_items):
    """기사 10개를 한 번에 묶어서 제미나이에게 전달"""
    if not news_items: return []
    
    prompt_content = ""
    for idx, item in enumerate(news_items):
        # HTML 태그 및 특수문자 제거
        clean_desc = re.sub('<[^>]*>', '', item['description']).replace('&quot;', '"')
        prompt_content += f"[{idx}] 제목: {item['title']}\n내용: {clean_desc}\n\n"

    prompt = (
        f"너는 전문 뉴스 요약가이다. 다음 뉴스 목록을 보고 각 [idx] 번호에 맞춰 핵심을 2줄 이내로 요약해.\n"
        f"반드시 '[idx] 요약내용' 형식만 출력하고, 인사말이나 추가 설명은 절대 하지 마.\n\n"
        f"{prompt_content}"
    )

    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        raw_output = response.text.strip().split('\n')
        
        summaries = {}
        for line in raw_output:
            match = re.match(r'\[(\d+)\]\s*(.*)', line)
            if match:
                summaries[int(match.group(1))] = match.group(2)
        
        # 만약 AI가 번호를 누락했을 경우를 대비한 Fallback
        return [summaries.get(i, "내용 요약 중 오류가 발생했습니다.") for i in range(len(news_items))]
    except Exception as e:
        print(f"Batch 요약 에러: {e}")
        return [re.sub('<[^>]*>', '', item['description'])[:90] + "..." for item in news_items]

def fetch_news(keyword, count=15, apply_filter=True):
    """뉴스 수집 및 필터링 (KST 날짜 포함)"""
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    # 필터 적용 시 검색 범위를 넓히기 위해 100개 요청
    params = {"query": keyword, "display": 100 if apply_filter else count, "sort": "date"}
    
    items = []
    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            for item in res.json().get('items', []):
                title_plain = re.sub('<[^>]*>', '', item['title'])
                desc_plain = re.sub('<[^>]*>', '', item['description'])
                
                # 조건: 제목 포함 AND 요약문 1회 이상 등장
                if not apply_filter or (keyword.lower() in title_plain.lower() and keyword.lower() in desc_plain.lower()):
                    try:
                        dt = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
                        item['formatted_date'] = dt.strftime('%m월 %d일, %H시 %M분')
                    except: 
                        item['formatted_date'] = item['pubDate']
                    
                    item['title'] = title_plain
                    item['description'] = desc_plain # 요약용 원문 보존
                    items.append(item)
                    if len(items) >= count: break
    except: pass
    return items

# --- 데이터 수집 및 묶음 요약 실행 ---

# 1. 칸별 기사 수집 
p1 = fetch_news("속보", 15, apply_filter=False)  # 1번 칸 15개

p2_kw = ["산업부", "KIAT", "기후부", "산업혁신기반구축"]
p2_all = {kw: fetch_news(kw, 10) for kw in p2_kw}  # 2번 칸 각 10개씩

p3_kw = ["호르무즈", "트럼프", "유가", "코스피"]
p3_all = {kw: fetch_news(kw, 10) for kw in p3_kw}  # 3번 칸 각 10개씩

# 2. 요약할 전체 기사 리스트화 (총 약 95개)
total_news = p1 + sum(p2_all.values(), []) + sum(p3_all.values(), [])

# 3. 10개씩 묶어서 요약 (API 호출 10회 미만으로 끝남)
batch_size = 10
summaries = []
for i in range(0, len(total_news), batch_size):
    batch = total_news[i : i + batch_size]
    summaries.extend(get_batch_summaries(batch))

# 4. 요약된 텍스트를 각 기사에 매칭
for idx, item in enumerate(total_news):
    item['ai_summary'] = summaries[idx] if idx < len(summaries) else "요약 대기 중..."

# 5. KST 시간 반영 및 저장
now_kst = datetime.now(KST)
final_data = {
    "pane1": p1, "pane2": p2_all, "pane3": p3_all,
    "last_updated": now_kst.strftime("%Y-%m-%d %H:%M:%S")
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"✅ {now_kst} KST - 총 {len(total_news)}개 기사 묶음 요약 완료")
