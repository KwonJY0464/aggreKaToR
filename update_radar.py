import os
import requests
import json
from datetime import datetime, timedelta, timezone

ASSEMBLY_KEY = os.environ.get("ASSEMBLY_API_KEY")
KST = timezone(timedelta(hours=9))

def fetch_data(url_id, extra_params=None):
    url = f"https://open.assembly.go.kr/portal/openapi/{url_id}"
    params = {"KEY": ASSEMBLY_KEY, "Type": "json", "pIndex": 1, "pSize": 1000}
    if extra_params:
        params.update(extra_params)
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json()
            if url_id in data:
                return data[url_id][1]['row']
    except Exception as e:
        print(f"API 호출 에러 ({url_id}): {e}")
    return []

if __name__ == "__main__":
    print("국회 타겟 레이더 DB 구축 시작...")
    
    # 1. 의원 상세 프로필 (nwvrqwxyaytdsfvhu)
    profiles_detail = fetch_data("nwvrqwxyaytdsfvhu", {"pSize": 300})
    
    # 💡 2. 의원 사진 전용 통합 API (ALLNAMEMBER) 호출 및 병합
    profiles_photo = fetch_data("ALLNAMEMBER", {"pSize": 300})
    photo_dict = {p.get("HG_NM"): p.get("NAAS_PIC", "") for p in profiles_photo}
    
    for p in profiles_detail:
        # 이름(HG_NM)을 매칭하여 NAAS_PIC 사진 주소를 프로필 DB에 꽂아넣음
        p["NAAS_PIC"] = photo_dict.get(p.get("HG_NM"), "")
    
    # 3. 최근 활동 내역 싹쓸이 (법안, 회의록)
    bills = fetch_data("ALLBILL", {"pSize": 1000})
    minutes = fetch_data("ncwgseseafwbuheph", {"pSize": 1000})
    
    # 💡 4. [신규] 본회의 표결 싹쓸이 (최근 30개 의안)
    print("본회의 표결 데이터 수집 중 (최근 30건, 약 30회 API 호출)...")
    recent_plenary_bills = fetch_data("ncocpgfiaoituanbr", {"AGE": "22", "pSize": 30})
    
    votes_data = []
    if recent_plenary_bills:
        for bill in recent_plenary_bills:
            bill_id = bill.get("BILL_ID")
            if not bill_id: continue
            
            # 해당 의안(BILL_ID)에 대한 300명 전원의 표결 결과 호출
            bill_votes = fetch_data("nzmimeepazxkubdpn", {"BILL_ID": bill_id, "pSize": 300})
            for v in bill_votes:
                votes_data.append({
                    "HG_NM": v.get("HG_NM"),
                    "BILL_NM": v.get("BILL_NAME", bill.get("BILL_NAME", "의안명 없음")),
                    "RESULT_VOTE_NM": v.get("RESULT_VOTE_MOD", "확인불가"),
                    "VOTE_DATE": v.get("VOTE_DATE", "날짜없음")
                })
    
    # 5. 하나의 JSON DB로 병합
    db = {
        "profiles": profiles_detail,
        "bills": bills,
        "minutes": minutes,
        "votes": votes_data,
        "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open("radar_db.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)
        
    print(f"✅ 레이더 DB 갱신 완료 (표결 데이터 {len(votes_data)}건 수집됨)")
