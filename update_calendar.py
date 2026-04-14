import json
import requests
import os
from datetime import datetime

# 1. 설정 및 인증키 로드
# 깃허브 Secrets에 저장한 PUBLIC_API_KEY를 가져옵니다.
SERVICE_KEY = os.environ.get("PUBLIC_API_KEY")
# 캡처하신 Swagger 정보(15130496/v1)를 바탕으로 한 전용 API 주소입니다.
API_URL = "https://api.odcloud.kr/api/15130496/v1/uddi:03dfa17e-399a-4c81-8b29-3738198f7e2f"

params = {
    'page': 1,
    'perPage': 100,
    'serviceKey': SERVICE_KEY
}

# 2. 기존 데이터 로드 (없으면 빈 리스트)
EVENTS_FILE = 'events.json'
try:
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        events = json.load(f)
except:
    events = []

print("🏛️ 국가 공식 API 서버 접속 중...")

# 3. 데이터 수신 및 필터링
try:
    # 인증키를 포함하여 공식 서버에 요청
    response = requests.get(API_URL, params=params, timeout=15)
    result = response.json()
    
    if 'data' in result:
        items = result['data']
        print(f"📊 총 {len(items)}개의 공고를 확인했습니다.")
        
        new_events = []
        for item in items:
            # API 제공 항목명: '공고명', '접수시작일자', '접수종료일자' 등
            title = item.get('공고명', '')
            start = item.get('접수시작일자', '')
            end = item.get('접수종료일자', '')
            url = item.get('상세페이지URL', 'https://kiat.or.kr')

            # [핵심] 오직 '기반구축' 단어가 들어간 것만 수집
            if "기반구축" in title:
                print(f"✨ 신규 기반구축 사업 발견: {title}")
                new_events.append({
                    "title": f"[공식] {title}",
                    "start": start[:10], # YYYY-MM-DD 포맷 맞춤
                    "end": end[:10],
                    "color": "#1a73e8", # 신뢰의 구글 블루 컬러
                    "url": url
                })
        
        # 4. 결과 저장 (기존 데이터 덮어쓰기 또는 합치기)
        if new_events:
            with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_events, f, ensure_ascii=False, indent=2)
            print(f"🎉 업데이트 완료! {len(new_events)}개의 기반구축 사업이 추가되었습니다.")
        else:
            print("🤷‍♂️ 현재 공고 리스트에 '기반구축' 키워드를 가진 신규 사업이 없습니다.")

except Exception as e:
    print(f"❌ API 연결 실패: {e}")
