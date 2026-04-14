import json
import requests
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
import google.generativeai as genai
import urllib.parse

# 1. API 및 기본 설정
gemini_api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# KIAT 사업공고 게시판 기본 URL
BASE_URL = "https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e"
DOMAIN = "https://kiat.or.kr"

# 국가(KIAT) 방화벽에서 봇으로 오인하지 않도록 사람 브라우저처럼 위장
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

# 2. 기존 달력 데이터 불러오기 (중복 방지용)
EVENTS_FILE = 'events.json'
try:
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        events = json.load(f)
    # 이미 달력에 있는 사업명들만 리스트로 쫙 뽑아둠
    existing_titles = [event.get('title', '') for event in events]
    print(f"📂 기존 일정 {len(existing_titles)}개를 불러왔습니다.")
except FileNotFoundError:
    events = []
    existing_titles = []
    print("📂 기존 일정 파일이 없습니다. 새로 생성합니다.")

# 3. 크롤링 및 필터링 로직
new_events_found = 0
page_index = 1
stop_crawling = False

print("🌐 KIAT 기반구축사업 탐색을 시작합니다... (기준일: 2025년 3월 1일 이후)")

while not stop_crawling:
    # 페이지 번호를 바꿔가며 접속 (KIAT 페이징 방식에 맞춤)
    url = f"{BASE_URL}&pageIndex={page_index}"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 게시판 목록의 각 행(글)을 찾음 (AI 도구로 실제 HTML 태그에 맞게 수정이 필요할 수 있음)
    # 보통 KIAT 게시판은 목록이 tbody 안의 tr 태그로 구성됨
    rows = soup.select('.board_list tbody tr') 
    
    if not rows:
        break # 글이 더 이상 없으면 종료

    for row in rows:
        # KIAT 공지사항 등 상단 고정글은 제외
        if row.select_one('.notice_icon'): 
            continue

        title_elem = row.select_one('.title a')
        date_elem = row.select_one('.date') # 등록일 태그 (실제 태그에 맞게 조정 필요)

        if not title_elem or not date_elem:
            continue

        raw_title = title_elem.text.strip()
        post_date_str = date_elem.text.strip().replace('.', '-') # 2025.03.15 -> 2025-03-15 형태 가정
        link = title_elem.get('href')

        # [핵심 로직 1] 시간 방어선 (2025년 3월 이전 글이면 전체 탐색 중단)
        if post_date_str < "2025-03-01":
            print(f"🛑 2025년 3월 이전 글 도달 ({post_date_str}). 탐색을 종료합니다.")
            stop_crawling = True
            break
            
        # [핵심 로직 2] 타겟 필터링 (기반구축 키워드)
        if "기반구축" not in raw_title:
            continue

        # [핵심 로직 3] 중복 방지 (이미 추가된 사업인지 확인)
        # 괄호 등 미세한 차이를 방지하기 위해 제목에 포함되어 있는지 검사
        is_duplicate = any(raw_title in existing_title for existing_title in existing_titles)
        if is_duplicate:
            print(f"⏩ 이미 등록된 공고 건너뜀: {raw_title}")
            continue

        # ---------------------------------------------------------
        # 여기서부터는 "기반구축이 포함된 새로운 공고"만 실행됨
        # ---------------------------------------------------------
        print(f"✨ 신규 공고 발견! 상세 내용 분석 중... : {raw_title}")
        
        # 상세 페이지 접속
        detail_url = urllib.parse.urljoin(DOMAIN, link)
        detail_resp = requests.get(detail_url, headers=HEADERS)
        detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
        
        # 본문 텍스트 긁어오기 (상세 페이지의 본문 태그 클래스)
        content_text = detail_soup.select_one('.board_view_con').text.strip()[:1500] # 토큰 절약을 위해 상단 1500자만 추출

        # AI에게 정보 추출 지시
        prompt = f"""
        다음은 한국산업기술진흥원(KIAT)의 정부 사업공고문 텍스트야.
        여기서 '사업명', 접수 '시작일', 접수 '종료일'을 추출해서 JSON 배열 형식으로만 대답해.
        날짜 포맷은 YYYY-MM-DD 이어야 해. 만약 텍스트 내에 정확한 날짜가 없다면 공란으로 비워둬.

        예시:
        [ {{"title": "[KIAT] 사업명", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "color": "#ff9800", "url": "{detail_url}"}} ]

        분석할 텍스트:
        {content_text}
        """

        try:
            ai_response = model.generate_content(prompt)
            clean_json = ai_response.text.replace('```json', '').replace('```', '').strip()
            new_item = json.loads(clean_json)
            
            events.extend(new_item)
            new_events_found += len(new_item)
            
            # 잦은 호출로 인한 API 차단을 막기 위한 매너 휴식(Sleep)
            time.sleep(2) 
            
        except Exception as e:
            print(f"❌ AI 분석 에러 발생 ({raw_title}): {e}")

    page_index += 1 # 다음 페이지로 넘어가기

# 4. 결과 저장
if new_events_found > 0:
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"🎉 업데이트 완료! 새로운 기반구축 사업 {new_events_found}개가 달력에 추가되었습니다.")
else:
    print("🤷‍♂️ 새로 추가할 기반구축 사업이 없습니다.")