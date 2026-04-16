import os
import requests
import json
from datetime import datetime
from google import genai
from google.genai import types

# 1. API 키 세팅 (깃허브 시크릿에서 가져옴)
ASSEMBLY_API_KEY = os.environ.get("ASSEMBLY_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. 국회일정 통합 API 호출 (오늘 이후 데이터)
URL = f"https://open.assembly.go.kr/portal/openapi/nwzbkafmavshvabbi?KEY={ASSEMBLY_API_KEY}&Type=json&pIndex=1&pSize=50"

def fetch_assembly_schedule():
    try:
        response = requests.get(URL)
        data = response.json()
        
        # 💡 방어 로직: 정상적인 데이터('nwzbkafmavshvabbi')가 안 왔을 때 진짜 이유를 출력!
        if 'nwzbkafmavshvabbi' not in data:
            print(f"⚠️ 국회 API 거절/오류 메세지: {data}")
            return []
            
        rows = data['nwzbkafmavshvabbi'][1].get('row', [])
        
        today = datetime.now().strftime("%Y-%m-%d")
        important_meetings = []
        
        for row in rows:
            meet_date = row.get('MEET_DT', '')
            committee = row.get('COMMITTEE_NM', '')
            
            # KTR 소관 상임위(산자중기위, 과방위, 환노위) 및 본회의만 필터링 + 오늘 이후 일정만
            if meet_date >= today and any(keyword in committee for keyword in ["산업통상자원", "본회의", "과학기술", "환경노동"]):
                important_meetings.append({
                    "date": meet_date,
                    "time": row.get('MEET_TIME', ''),
                    "title": row.get('MEET_NAME', ''),
                    "committee": committee,
                    "location": row.get('MEET_PLACE', '')
                })
        return important_meetings
    except Exception as e:
        print(f"국회 데이터 수집 에러: {e}")
        return []

# 3. Gemma 3 27B로 일정 요약하기
def summarize_with_gemini(schedule_data):
    if not schedule_data:
        return "예정된 주요 상임위/본회의 일정이 없습니다."
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    다음은 대한민국 국회의 주요 일정 데이터야.
    이 일정들 중에서 연구기관(시험인증, R&D, 산업정책 등) 업무와 관련성이 높은 일정을 중심으로,
    오늘 또는 내일 주목해야 할 일정을 2~3줄로 짧고 명확하게 요약해줘.
    
    [국회 일정 데이터]
    {json.dumps(schedule_data, ensure_ascii=False)}
    """
    
    try:
        # 💡 Gemma 3 27B 모델 사용
        response = client.models.generate_content(
            model='gemma-3-27b-it',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"AI 요약 에러: {e}")
        return "일정 요약을 생성하지 못했습니다."

# 4. 메인 실행 및 JSON 저장
if __name__ == "__main__":
    print("국회 일정 수집 시작...")
    schedules = fetch_assembly_schedule()
    
    # 최근 5개 일정만 추림 (화면 표시용)
    top_schedules = sorted(schedules, key=lambda x: (x['date'], x['time']))[:5]
    ai_summary = summarize_with_gemini(top_schedules)
    
    final_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "schedules": top_schedules,
        "summary": ai_summary
    }
    
    # assembly.json 파일로 저장
    with open("assembly.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print("assembly.json 저장 완료!")
