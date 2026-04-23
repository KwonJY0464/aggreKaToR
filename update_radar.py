import os
import requests
import json
from datetime import datetime, timedelta, timezone

ASSEMBLY_KEY = os.environ.get("ASSEMBLY_API_KEY")
KST = timezone(timedelta(hours=9))

def fetch_data(url_id, extra_params=None):
    url = f"https://open.assembly.go.kr/portal/openapi/{url_id}"
    # 의원별 발의법률안은 5개만 긁어오도록 기본 pSize를 5로 세팅
    params = {"KEY": ASSEMBLY_KEY, "Type": "json", "pIndex": 1, "pSize": 5}
    if extra_params:
        params.update(extra_params)
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json()
            if url_id in data:
                return data[url_id][1]['row']
    except Exception as e:
        pass
    return []

if __name__ == "__main__":
    print("🚀 [작전명: 개인화 레이더 가동] 활동 내역 수집 개시...")

    # 1. 수동으로 만들어둔 기준 명부(profiles_db.json) 로드
    try:
        with open("profiles_db.json", "r", encoding="utf-8") as f:
            profiles = json.load(f)
    except Exception as e:
        print("❌ profiles_db.json 파일을 찾을 수 없습니다. 프로필을 먼저 갱신하십시오.")
        exit(1)

    radar_db = {
        "committee": [],
        "plenary": [],
        "bills": [],
        "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    }

    total = len(profiles)
    print(f"총 {total}명의 의원 활동 데이터 추적을 시작합니다. (시간이 다소 소요될 수 있습니다)")

    for idx, p in enumerate(profiles):
        name = p.get("HG_NM", "").strip()
        naas_cd = p.get("NAAS_CD", "").strip()
        if not name or not naas_cd: continue

        # [1] 위원회 일정 (NAMEMBERCMITSCHEDULE)
        c_schedules = fetch_data("NAMEMBERCMITSCHEDULE", {"NAAS_CD": naas_cd, "pSize": 10})
        for s in c_schedules:
            radar_db["committee"].append({
                "HG_NM": name,
                "SCH_CN": s.get("SCH_CN", ""),
                "SCH_DT": s.get("SCH_DT", ""),
                "SCH_TM": s.get("SCH_TM", ""),
                "CMIT_NM": s.get("CMIT_NM", "")
            })

        # [2] 본회의 일정 (NAMEMBERLEGISCHEDULE)
        p_schedules = fetch_data("NAMEMBERLEGISCHEDULE", {"NAAS_CD": naas_cd, "pSize": 10})
        for s in p_schedules:
            radar_db["plenary"].append({
                "HG_NM": name,
                "SCH_CN": s.get("SCH_CN", ""),
                "SCH_DT": s.get("SCH_DT", ""),
                "SCH_TM": s.get("SCH_TM", ""),
                "CMIT_NM": s.get("CMIT_NM", "본회의") 
            })

        # [3] 발의법률안 (nzmimeepazxkubdpn) - AGE=22, 제안자=이름, 5개 한정
        bills = fetch_data("nzmimeepazxkubdpn", {"AGE": "22", "PROPOSER": name})
        for b in bills:
            # 💡 사령관님 명령 완수: "비어있으면 있는 걸 찾아라" (역순 추적 폭포수 로직)
            status = ""
            dt = ""
            
            if b.get("PROC_RESULT"):                  # 1. 본회의 통과/폐기
                status = b.get("PROC_RESULT")
                dt = b.get("PROC_DT", "")
            elif b.get("LAW_PROC_DT"):                # 2. 법사위 처리
                status = "법사위처리"
                dt = b.get("LAW_PROC_DT", "")
            elif b.get("LAW_PRESENT_DT"):             # 3. 법사위 상정
                status = "법사위상정"
                dt = b.get("LAW_PRESENT_DT", "")
            elif b.get("LAW_SUBMIT_DT"):              # 4. 법사위 회부
                status = "법사위회부"
                dt = b.get("LAW_SUBMIT_DT", "")
            elif b.get("CMT_PROC_DT"):                # 5. 소관위 처리
                status = "소관위처리"
                dt = b.get("CMT_PROC_DT", "")
            elif b.get("CMT_PRESENT_DT"):             # 6. 소관위 상정
                status = "소관위상정"
                dt = b.get("CMT_PRESENT_DT", "")
            elif b.get("COMMITTEE_DT"):               # 7. 소관위 회부 (사진에서 잡힌 데이터)
                status = "소관위회부"
                dt = b.get("COMMITTEE_DT", "")
            else:                                     # 8. 이제 막 발의됨
                status = "발의"
                dt = b.get("PROPOSE_DT", "")

            radar_db["bills"].append({
                "HG_NM": name,
                "BILL_NAME": b.get("BILL_NAME", ""),
                "COMMITTEE": b.get("COMMITTEE", ""),
                "STATUS": status,
                "DT": dt,
                "LINK_URL": b.get("DETAIL_LINK", "#")
            })

    # 최종 병합 저장
    with open("radar_db.json", "w", encoding="utf-8") as f:
        json.dump(radar_db, f, ensure_ascii=False)

    print(f"✅ 완료:  DB (radar_db.json) 구축 성공!")
