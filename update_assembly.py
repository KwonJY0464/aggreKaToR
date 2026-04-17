import os
import requests
import json
from datetime import datetime

# 1. 설정
ASSEMBLY_API_KEY = os.environ.get("ASSEMBLY_API_KEY")
SERVICE_ID = "ALLSCHEDULE"
# 검색 범위를 1000건으로 확대하여 누락 방지
URL = f"https://open.assembly.go.kr/portal/openapi/{SERVICE_ID}?KEY={ASSEMBLY_API_KEY}&Type=json&pIndex=1&pSize=1000"

def fetch_all_assembly_data():
    try:
        response = requests.get(URL)
        data = response.json()
        
        if SERVICE_ID not in data:
            print(f"⚠️ API 응답에 데이터가 없습니다: {data}")
            return []
            
        rows = data[SERVICE_ID][1].get('row', [])
        print(f"✅ 총 {len(rows)}건의 원본 데이터를 수신했습니다.")
        
        # 4월 1일부터 모든 내용 수집
        target_start_date = "2026-04-01"
        processed_data = []
        
        for row in rows:
            dt = row.get('SCH_DT', '')
            cmit = row.get('CMIT_NM') or ""
            content = row.get('SCH_CN') or ""
            
            # 날짜 조건만 확인 (4월 1일 이후면 무조건 통과)
            if dt >= target_start_date:
                # 색상 구분을 위한 태그만 지정 (거르는 로직 없음)
                cat = "etc"
                if any(kw in cmit for kw in ["산업통상", "중소벤처"]) or any(kw in content for kw in ["산업부", "산업통상자원부"]):
                    cat = "sanja" # 파란 점
                elif any(kw in cmit for kw in ["기후환경", "노동", "환경노동"]) or any(kw in content for kw in ["기후부", "환경부", "기후환경부"]):
                    cat = "gihyu" # 노란 점
                elif "본회의" in cmit or "본회의" in content:
                    cat = "session"
                
                processed_data.append({
                    "date": dt,
                    "time": row.get('SCH_TM', ''),
                    "title": content,
                    "committee": cmit,
                    "location": row.get('EV_PLC', ''),
                    "type": cat
                })
        
        print(f"🎯 {target_start_date} 이후 데이터 {len(processed_data)}건 처리 완료.")
        return processed_data
    except Exception as e:
        print(f"❌ 수집 중 에러 발생: {e}")
        return []

if __name__ == "__main__":
    # 데이터 수집 실행
    schedules = fetch_all_assembly_data()
    
    # 💡 구글 젬마 요약 일시 중단 (시험용 고정 텍스트)
    test_summary = "현재 데이터 전수 조사를 위해 AI 요약 기능이 일시 중지되었습니다. 수집된 리스트의 내용을 직접 확인하십시오."
    
    # JSON 저장
    with open("assembly.json", "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "schedules": schedules,
            "summary": test_summary
        }, f, ensure_ascii=False, indent=2)
        
    print("💾 assembly.json 저장 완료.")
