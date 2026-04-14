import json
import requests
import os
import urllib.parse

# 1. 인증키 설정 (GitHub Secrets에 저장된 'Decoding' 키 활용)
RAW_KEY = os.environ.get("PUBLIC_API_KEY")
SERVICE_KEY = RAW_KEY # 헤더 방식은 Decoding 키를 그대로 사용합니다.

# 2. [핵심] 연구원님이 찾으신 진짜 데이터 주소(UUID) 적용
API_URL = "https://api.odcloud.kr/api/15130496/v1/uddi:aa0ce4e1-8b7f-4cc8-bf57-c5384ce7d568"

# 3. Http 헤더 및 파라미터 설정
headers = {
    "accept": "*/*",
    "Authorization": f"Infuser {SERVICE_KEY}" # 공식 문서 권장 보안 방식
}

params = {
    'page': 1,
    'perPage': 100 # 한 번에 최대 100개까지 수집
}

print("🏛️ 국가 공식 API 서버(KEIT 통합공고)에 접속 중...")

try:
    # 보안 헤더를 포함하여 요청을 보냅니다.
    response = requests.get(API_URL, params=params, headers=headers, timeout=20)
    
    print(f"📡 응답 상태 코드: {response.status_code}") # 200이 나오면 성공
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('data', [])
        print(f"📊 총 {len(items)}개의 공고 데이터를 수신했습니다.")
        
        new_events = []
        for item in items:
            # API에서 제공하는 정확한 항목명(공고명)으로 수색합니다.
            title = item.get('공고명', '')
            
            # [핵심] '기반구축' 키워드 필터링
            if "기반구축" in title:
                print(f"✨ 신규 공고 발견: {title}")
                
                # 날짜 형식 정리 (YYYY-MM-DD)
                start_dt = item.get('접수시작일자', '')[:10]
                end_dt = item.get('접수종료일자', '')[:10]
                detail_url = item.get('상세페이지URL', 'https://kiat.or.kr')

                new_events.append({
                    "title": f"[공식] {title}",
                    "start": start_dt,
                    "end": end_dt,
                    "color": "#1a73e8",
                    "url": detail_url
                })
        
        # 4. 결과 저장 (events.json 파일 생성/업데이트)
        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(new_events, f, ensure_ascii=False, indent=2)
        
        if new_events:
            print(f"🎉 성공! {len(new_events)}개의 '기반구축' 사업을 캘린더에 등록했습니다.")
        else:
            print("🤷‍♂️ 현재 공고 리스트 중 '기반구축' 키워드에 해당하는 사업이 없습니다.")

    elif response.status_code == 401:
        print("❌ 인증 실패: GitHub Secrets에 넣은 인증키가 'Decoding' 버전이 맞는지 확인해 주세요.")
    else:
        print(f"❌ 서버 응답 에러: {response.status_code}")

except Exception as e:
    print(f"❌ 실행 중 오류 발생: {e}")
