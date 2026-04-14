import json
import requests
import os
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. API 및 세션 설정
gemini_api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# 세션을 사용해 연결을 유지하고 보안(Referer)을 우회합니다.
session = requests.Session()
BASE_URL = "https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Referer': 'https://kiat.or.kr/' # "키아트 메인에서 들어왔어"라고 속이는 보안 우회
}

# 2. 기존 데이터 로드
EVENTS_FILE = 'events.json'
try:
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        events = json.load(f)
    existing_titles = [event.get('title', '') for event in events]
except:
    events = []
    existing_titles = []

print("🚀 [진단 시작] 봇의 눈으로 KIAT 게시판을 정밀 수색합니다.")

# 3. 크롤링 실행 (1페이지 집중 수색)
response = session.get(BASE_URL, headers=HEADERS)
soup = BeautifulSoup(response.text, 'html.parser')

# [핵심 수술] 클래스명 다 무시하고 contentsView 링크가 있는 모든 <a> 태그를 직접 찾습니다.
all_links = soup.find_all('a', href=re.compile(r"contentsView"))

print(f"📊 발견된 게시글 후보: {len(all_links)}개")

if len(all_links) == 0:
    print("⚠️ 여전히 글을 못 찾고 있습니다. 페이지 소스 일부를 확인합니다.")
    print(response.text[:500]) # 봇이 보고 있는 화면 맨 윗부분 출력

for link in all_links:
    raw_title = link.text.strip()
    
    # 해당 링크가 포함된 줄(tr)에서 날짜 찾기
    parent_tr = link.find_parent('tr')
    date_text = "0000-00-00"
    if parent_tr:
        # 날짜가 들어있는 칸(td_reg_date)을 텍스트 기반으로 수색
        date_td = parent_tr.find('td', string=re.compile(r'\d{4}-\d{2}-\d{2}'))
        if not date_td: # 클래스명으로 다시 시도
            date_td = parent_tr.find('td', class_=lambda x: x and 'td_reg_date' in x)
        
        if date_td:
            date_text = re.sub(r'[^0-9\-]', '', date_td.text.strip())

    print(f"🔍 검토 중: [{date_text}] {raw_title[:30]}")

    # 조건 체크: 2025-03-01 이후 & 제목에 "기반구축" 포함
    if date_text < "2025-03-01": continue
    if "기반구축" not in raw_title: continue
    if any(raw_title in et for et in existing_titles): continue

    print(f"✨ [대상 확정] {raw_title} 분석 들어갑니다!")

    # 상세페이지 ID 추출 및 분석 (이전 로직과 동일)
    content_id = re.search(r"contentsView\('([^']+)'\)", link['href']).group(1)
    detail_url = f"https://kiat.or.kr/front/board/boardContentsView.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e&contents_id={content_id}"
    
    try:
        detail_resp = session.get(detail_url, headers=HEADERS)
        detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
        content_text = detail_soup.text.strip()[:2000]

        prompt = f"다음 공고에서 '사업명', '시작일', '종료일'을 추출해 JSON으로 줘. 날짜 포맷 YYYY-MM-DD. [{{\"title\": \"[KIAT] 사업명\", \"start\": \"YYYY-MM-DD\", \"end\": \"YYYY-MM-DD\", \"color\": \"#0f9d58\", \"url\": \"{detail_url}\"}}] \n본문: {content_text}"
        
        ai_res = model.generate_content(prompt)
        new_item = json.loads(ai_res.text.replace('```json', '').replace('```', '').strip())
        events.extend(new_item)
        print(f"✅ 추가 완료: {raw_title}")
        time.sleep(1)
    except Exception as e:
        print(f"❌ 에러: {e}")

# 결과 저장
with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(events, f, ensure_ascii=False, indent=2)
print("🏁 작업이 종료되었습니다.")
