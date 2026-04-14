import json
import requests
import os
import time
import re
from bs4 import BeautifulSoup
import google.generativeai as genai

# AI 설정
gemini_api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# 연구원님이 찾아주신 신분증(Header) 복제
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Referer': 'https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e',
    'Origin': 'https://kiat.or.kr',
    'Content-Type': 'application/x-www-form-urlencoded'
}

# 데이터를 직접 요청하는 '진짜' 주소
TARGET_URL = "https://kiat.or.kr/front/board/boardContentsListPage.do"

# 서버에 보낼 '데이터 요청서' (이게 핵심입니다)
PAYLOAD = {
    'board_id': '90',
    'MenuId': 'b159c9dac684471b87256f1e25404f5e',
    'pageIndex': '1',
    'searchCondition': 'sc.subject', # 제목으로 검색
    'searchKeyword': '기반구축'      # 아예 검색어를 넣어서 서버가 골라주게 함
}

def run_scrapper():
    session = requests.Session()
    
    print("🎯 [데이터 정밀 수색] 서버에 '기반구축' 공고를 직접 요청합니다...")
    # POST 방식을 사용하여 검색 결과만 쏙 뽑아옵니다.
    response = session.post(TARGET_URL, headers=HEADERS, data=PAYLOAD, timeout=20)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 5만 자 안에 '기반구축'이라는 글자가 있는지 깡통 수색
    if "기반구축" in response.text:
        print("✅ 서버 응답 데이터에서 '기반구축' 키워드를 포착했습니다!")
    else:
        print("🤷‍♂️ 서버가 보낸 데이터에도 '기반구축' 사업은 보이지 않습니다.")
        return

    # 글 제목이 들어있는 <a> 태그들 추출
    links = soup.select('.td_title a')
    print(f"📋 필터링된 기반구축 공고: {len(links)}건 발견")

    events = []
    if os.path.exists('events.json'):
        with open('events.json', 'r', encoding='utf-8') as f:
            events = json.load(f)

    for link in links:
        title = link.text.strip()
        print(f"✨ 분석 중: {title}")
        
        # 상세페이지 링크 생성 (자바스크립트 ID 추출)
        cid_match = re.search(r"contentsView\('([^']+)'\)", link.get('href', ''))
        if cid_match:
            cid = cid_match.group(1)
            detail_url = f"https://kiat.or.kr/front/board/boardContentsView.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e&contents_id={cid}"
            
            # AI 분석 및 저장 로직 (이하 동일)
            try:
                d_res = session.get(detail_url, headers=HEADERS)
                d_soup = BeautifulSoup(d_res.text, 'html.parser')
                txt = d_soup.text.strip()[:1500]

                prompt = f"다음 공고에서 '사업명', '시작일', '종료일'을 추출해. 날짜: YYYY-MM-DD. [{{\"title\": \"[KIAT] {title}\", \"start\": \"YYYY-MM-DD\", \"end\": \"YYYY-MM-DD\", \"color\": \"#d32f2f\", \"url\": \"{detail_url}\"}}] \n본문: {txt}"
                ai_res = model.generate_content(prompt)
                
                item = json.loads(ai_res.text.replace('```json', '').replace('```', '').strip())
                events.extend(item)
                time.sleep(2)
            except: continue

    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print("🏁 업데이트 완료.")

if __name__ == "__main__":
    run_scrapper()
