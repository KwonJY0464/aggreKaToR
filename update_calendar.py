import json
import requests
import os
import time
import re
from bs4 import BeautifulSoup
import google.generativeai as genai # 2026년 기준 신규 SDK 권장

# 1. AI 설정
gemini_api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.0-flash') # 최신 모델 사용

# 연구원님이 캡처해주신 그 헤더 완벽 복제
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Referer': 'https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90'
}

BASE_URL = "https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e"

def run_scrapper():
    session = requests.Session()
    print("🚀 [최후의 수단] 텍스트 전체를 뒤져서 '기반구축'을 찾습니다.")
    
    # 1. 일단 게시판을 통째로 읽어옵니다.
    response = session.get(BASE_URL, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 2. [핵심 수술] 모든 <a> 태그를 다 가져와서 제목에 '기반구축'이 있는지 검사
    all_a_tags = soup.find_all('a')
    filtered_links = []
    
    for a in all_a_tags:
        title_text = a.text.strip()
        # 제목에 '기반구축'이 있고, href에 contentsView가 포함된 것만 골라냄
        if "기반구축" in title_text and "contentsView" in a.get('href', ''):
            filtered_links.append(a)

    print(f"📋 발견된 기반구축 공고: {len(filtered_links)}건")

    if not filtered_links:
        print("⚠️ 텍스트는 가져왔으나 '기반구축' 링크를 특정하지 못했습니다.")
        return

    # 3. 데이터 로드 및 분석
    events = []
    if os.path.exists('events.json'):
        with open('events.json', 'r', encoding='utf-8') as f:
            events = json.load(f)

    for link in filtered_links:
        title = link.text.strip()
        print(f"✨ 분석 시작: {title}")
        
        cid = re.search(r"contentsView\('([^']+)'\)", link['href']).group(1)
        detail_url = f"https://kiat.or.kr/front/board/boardContentsView.do?board_id=90&MenuId=b159c9dac684471b87256f1e25404f5e&contents_id={cid}"
        
        try:
            d_res = session.get(detail_url, headers=HEADERS)
            d_soup = BeautifulSoup(d_res.text, 'html.parser')
            # 상세내용에서 분석 (가장 확실한 방법)
            content = d_soup.text[:1500] 

            prompt = f"다음 공고에서 '사업명', '시작일', '종료일' 추출해 JSON으로 줘. 날짜 포맷 YYYY-MM-DD. [{{\"title\": \"[KIAT] {title}\", \"start\": \"YYYY-MM-DD\", \"end\": \"YYYY-MM-DD\", \"color\": \"#d32f2f\", \"url\": \"{detail_url}\"}}] \n본문: {content}"
            ai_res = model.generate_content(prompt)
            
            # JSON만 정밀하게 추출
            clean_json = re.search(r'\[.*\]', ai_res.text, re.DOTALL).group()
            item = json.loads(clean_json)
            events.extend(item)
            time.sleep(2) # 서버 부하 방지 (에티켓)
        except Exception as e:
            print(f"❌ 분석 실패: {e}")

    # 결과 저장
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print("🏁 캘린더 업데이트가 성공적으로 끝났습니다.")

if __name__ == "__main__":
    run_scrapper()
