import json
import requests
import os
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. API 및 기본 설정
gemini_api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

BASE_URL = "https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

# 2. 기존 데이터 로드
EVENTS_FILE = 'events.json'
try:
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        events = json.load(f)
    existing_titles = [event.get('title', '') for event in events]
except FileNotFoundError:
    events = []
    existing_titles = []

# 3. 크롤링 시작
new_events_found = 0
page_index = 1
stop_crawling = False

print("🌐 KIAT 사업공고 탐색을 시작합니다... (기준일: 2025년 3월 1일 이후)")

while not stop_crawling:
    url = f"{BASE_URL}&pageIndex={page_index}"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 게시판 목록 행 가져오기
    rows = soup.select('table tbody tr')
    
    if not rows:
        break

    for row in rows:
        # 연구원님이 찾아낸 정확한 KIAT 태그 적용
        title_elem = row.select_one('.td_title a')
        date_elem = row.select_one('.td_reg_date')

        if not title_elem or not date_elem:
            continue

        raw_title = title_elem.text.strip()
        raw_date = date_elem.text.strip()
        post_date_str = re.sub(r'[^0-9\-]', '', raw_date.replace('.', '-'))

        # 시간 방어선 (2025-03-01 이전이면 스탑)
        if post_date_str < "2025-03-01":
            print(f"🛑 2025년 3월 이전 글 도달 ({post_date_str}). 탐색 종료.")
            stop_crawling = True
            break
            
        # [핵심] 키워드 필터링: 오직 "기반구축"만 통과!
        if "기반구축" not in raw_title:
            continue

        if any(raw_title in existing_title for existing_title in existing_titles):
            continue

        print(f"✨ 신규 기반구축사업 발견! : {raw_title}")
        
        # 자바스크립트 링크 해독
        href_val = title_elem.get('href', '')
        content_id_match = re.search(r"contentsView\('([^']+)'\)", href_val)
        
        if content_id_match:
            content_id = content_id_match.group(1)
            detail_url = f"https://kiat.or.kr/front/board/boardContentsView.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e&contents_id={content_id}"
            
            # 상세 페이지 접속
            detail_resp = requests.get(detail_url, headers=HEADERS)
            detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
            
            # 본문 내용 추출
            try:
                content_text = detail_soup.select_one('.board_view_con').text.strip()[:1500]
            except AttributeError:
                content_text = detail_soup.text.strip()[:1500]

            # AI 분석
            prompt = f"""
            다음은 KIAT 사업공고문이야. '사업명', 접수 '시작일', '종료일'을 추출해서 JSON 배열로 대답해.
            날짜 포맷: YYYY-MM-DD.
            예시: [ {{"title": "[KIAT] 사업명", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "color": "#0f9d58", "url": "{detail_url}"}} ]
            텍스트: {content_text}
            """

            try:
                ai_response = model.generate_content(prompt)
                clean_json = ai_response.text.replace('```json', '').replace('```', '').strip()
                new_item = json.loads(clean_json)
                
                events.extend(new_item)
                new_events_found += len(new_item)
                time.sleep(2) # 매너 휴식
                
            except Exception as e:
                print(f"❌ 분석 에러: {e}")

    page_index += 1

if new_events_found > 0:
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"🎉 업데이트 완료! {new_events_found}개의 기반구축사업이 캘린더에 추가되었습니다.")
else:
    print("🤷‍♂️ 새로 추가할 기반구축사업이 없습니다.")
    
# 기존 코드
if "기반구축" not in raw_title:
    continue

# 수정 코드 (테스트용: '기반'이라는 단어만 들어가면 수집)
if "기반" not in raw_title:
    continue
