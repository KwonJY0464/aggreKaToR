import os
import requests
import json
import re
from datetime import datetime, timedelta, timezone

# 1. 환경 변수 및 설정
ASSEMBLY_KEY = os.environ.get("ASSEMBLY_API_KEY")
KST = timezone(timedelta(hours=9))

# 💡 KTR 미래전략실 핵심 타겟 설정
TARGET_COMMITTEES = ['산업통상자원중소벤처기업위원회', '환경노동위원회', '과학기술정보방송통신위원회', '보건복지위원회']
TARGET_KEYWORDS = ['이차전지', '배터리', '탄소중립', 'R&D', '연구개발', '인증', '시험', '규제', '모빌리티', '신산업']

def fetch_all_bill():
    """의안접수정보(ALLBILL) 수집 및 필터링"""
    url = "https://open.assembly.go.kr/portal/openapi/ALLBILL"
    params = {
        "KEY": ASSEMBLY_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100 # 검색 범위를 넓혀 100건 확인
    }
    
    extracted = []
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json()
            if 'ALLBILL' in data:
                rows = data['ALLBILL'][1]['row']
                for row in rows:
                    title = row.get('BILL_NM', '')
                    comm = row.get('JRCMIT_NM', '') or "미정"
                    
                    # 키워드 매칭 또는 타겟 상임위 필터링
                    if any(kw in title for kw in TARGET_KEYWORDS) or comm in TARGET_COMMITTEES:
                        extracted.append({
                            "type": "bill",
                            "title": title,
                            "committee": comm,
                            "date": row.get('PROPOSER_DT', ''),
                            "link": row.get('LINK_URL', ''),
                            "meta": f"제안자: {row.get('RST_PROPOSER', '확인불가')}",
                            "ai_summary": f"[{comm}] 신규 의안이 접수되었습니다. 상세 내용을 확인하십시오." # AI 대신 고정 메시지
                        })
    except Exception as e:
        print(f"의안 수집 에러: {e}")
    return extracted

def fetch_meeting_minutes():
    """위원회 회의록 정보(ncwgseseafwbuheph) 수집 및 필터링"""
    url = "https://open.assembly.go.kr/portal/openapi/ncwgseseafwbuheph"
    params = {
        "KEY": ASSEMBLY_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 50
    }
    
    extracted = []
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json()
            if 'ncwgseseafwbuheph' in data:
                rows = data['ncwgseseafwbuheph'][1]['row']
                for row in rows:
                    comm = row.get('COMM_NAME', '')
                    agenda = row.get('SUB_NAME', '')
                    
                    if comm in TARGET_COMMITTEES or any(kw in agenda for kw in TARGET_KEYWORDS):
                        extracted.append({
                            "type": "minute",
                            "title": f"[{comm}] {agenda[:40]}...",
                            "committee": comm,
                            "date": row.get('MEET_DATE', ''),
                            "link": row.get('CONF_LINK_URL', '') or row.get('PDF_LINK_URL', ''),
                            "meta": f"회의구분: {row.get('MEET_NAME', '')}",
                            "ai_summary": f"{comm} 회의록 데이터입니다. PDF/링크를 통해 원문을 확인하십시오."
                        })
    except Exception as e:
        print(f"회의록 수집 에러: {e}")
    return extracted

if __name__ == "__main__":
    print("국회 데이터 정찰 개시 (AI 제외 버전)...")
    
    # 데이터 수집
    bills = fetch_all_bill()
    minutes = fetch_meeting_minutes()
    combined = bills + minutes
    
    # 프론트엔드 호환성을 위해 날짜 키 복사
    for item in combined:
        item['formatted_date'] = item['date']

    # JSON 저장 (기존 프론트엔드 구조 유지)
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    output = {
        "pane2": {"전체": combined},
        "last_updated": now_kst
    }

    with open("assembly_ktr.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ {now_kst} KST - 국회 데이터 총 {len(combined)}건 수집 완료 (AI 분석 제외)")
