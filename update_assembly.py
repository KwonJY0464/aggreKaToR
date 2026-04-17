import os
import requests
import json
from datetime import datetime
from google import genai
from google.genai import types

# 1. 설정
ASSEMBLY_API_KEY = os.environ.get("ASSEMBLY_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SERVICE_ID = "ALLSCHEDULE"
URL = f"https://open.assembly.go.kr/portal/openapi/{SERVICE_ID}?KEY={ASSEMBLY_API_KEY}&Type=json&pIndex=1&pSize=100"

def fetch_assembly_schedule():
    try:
        response = requests.get(URL)
        data = response.json()
        if SERVICE_ID not in data: return []
        rows = data[SERVICE_ID][1].get('row', [])
        
        today = datetime.now().strftime("%Y-%m-%d")
        processed_data = []
        
        for row in rows:
            dt = row.get('SCH_DT', '')
            cmit = row.get('CMIT_NM') or ""
            content = row.get('SCH_CN') or ""
            
            # 필터링 및 카테고리 분류 (산자중기위=blue, 기후환노위=yellow)
            cat = "etc"
            if any(kw in cmit for kw in ["산업통상", "중소벤처"]) or any(kw in content for kw in ["산업부", "산업통상자원부"]):
                cat = "sanja"
            elif any(kw in cmit for kw in ["기후환경", "노동"]) or any(kw in content for kw in ["기후부", "환경부", "기후환경부"]):
                cat = "gihyu"
            elif "본회의" in cmit or "본회의" in content:
                cat = "session" # 국회 본회의 등 주요 회의 포함
            
            # 오늘 이후의 관련 일정만 수집
            if dt >= today and cat != "etc":
                processed_data.append({
                    "date": dt,
                    "time": row.get('SCH_TM', ''),
                    "title": content,
                    "committee": cmit,
                    "location": row.get('EV_PLC', ''),
                    "type": cat
                })
        return processed_data
    except: return []

def summarize_with_gemini(schedule_data):
    if not schedule_data: return "당분간 예정된 주요 상임위 및 본회의 일정이 없습니다."
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"다음 국회 일정을 분석해서 오늘/내일 주목해야 할 핵심 포인트를 3줄 요약해줘. 특히 산자부 및 기후환경부 관련 이슈를 중점적으로 봐줘:\n{json.dumps(schedule_data, ensure_ascii=False)}"
        response = client.models.generate_content(model='gemma-3-27b-it', contents=prompt)
        return response.text.strip()
    except: return "일정 요약 생성 중 오류가 발생했습니다."

if __name__ == "__main__":
    schedules = fetch_assembly_schedule()
    summary = summarize_with_gemini(schedules)
    with open("assembly.json", "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "schedules": schedules,
            "summary": summary
        }, f, ensure_ascii=False, indent=2)
