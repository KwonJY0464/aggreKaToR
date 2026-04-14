import json
import requests
import os
import urllib.parse

# 1. 설정 (인증키는 GitHub Secrets에 'PUBLIC_API_KEY'로 저장하는 걸 추천합니다)
SERVICE_KEY = os.environ.get("PUBLIC_API_KEY") # 발급받은 인증키
UUID = "여기에_상세페이지에서_확인한_UUID를_넣으세요" # 예: uddi:69074742-xxx
API_URL = f"https://api.odcloud.kr/api/15130496/v1/{UUID}"

# 2. API 호출
params = {
    'page': 1,
    'perPage': 100, # 한 번에 100개씩 가져옴
    'serviceKey': SERVICE_KEY
}

print("🏛️ 국가 공식 API 서버에 접속 중...")

try:
    # 인증키가 이미 인코딩되어 있다면 unquote로 한 번 풀어줘야 에러가 안 납니다.
    response = requests.get(API_URL, params=params, timeout=10)
    data = response.json()
    
    # 3. 데이터 수색 (기반구축 키워드 필터링)
    new_events = []
    if 'data' in data:
        items = data['data']
        print(f"📊 총 {len(items)}개의 공고를 수신했습니다.")
        
        for item in items:
            # API마다 항목명이 다를 수 있습니다. (보통 '공고명', 'PBLANC_NM' 등)
            title = item.get('공고명') or item.get('pblancNm') or ""
            start_date = item.get('공고시작일') or item.get('pblancStrtDt') or ""
            end_date = item.get('공고종료일') or item.get('pblancEndDt') or ""
            url = item.get('상세페이지URL') or "https://kiat.or.kr"

            # [핵심] 연구원님이 원하시는 '기반구축' 키워드 수색
            if "기반구축" in title:
                print(f"✨ 기반구축 사업 발견! : {title}")
                new_events.append({
                    "title": f"[국가공식] {title}",
                    "start": start_date[:10], # YYYY-MM-DD 포맷
                    "end": end_date[:10],
                    "color": "#0052cc", # 공식 데이터는 신뢰의 파란색
                    "url": url
                })

    # 4. JSON 파일 저장
    if new_events:
        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(new_events, f, ensure_ascii=False, indent=2)
        print(f"🎉 성공! {len(new_events)}개의 기반구축 일정을 업데이트했습니다.")
    else:
        print("🤷‍♂️ 현재 API 리스트 내에 '기반구축' 사업이 없습니다.")

except Exception as e:
    print(f"❌ API 통신 실패: {e}")
