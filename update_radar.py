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
    print("🚀 [작전명: 레이더 최적화] 22대 국회 추적 가동...")
    
    # 1. 22대 현역 의원 인적사항 (nwvrqwxyaytdsfvhu)
    raw_profiles = fetch_data("nwvrqwxyaytdsfvhu", {"pSize": 300})
    
    # 2. 22대 현역 의원 사진 전용 매칭 (ALLNAMEMBER)
    print("📸 22대 의원 사진 주소(NAAS_PIC) 수집 중...")
    photo_data = fetch_data("ALLNAMEMBER", {"UNIT": "22", "pSize": 500})
    
    photo_map = {}
    for m in photo_data:
        name = m.get("HG_NM", "").strip()
        if name:
            # 어떠한 조작도 없이 국회가 준 URL 그대로 저장
            photo_map[name] = m.get("NAAS_PIC", "")

    # 3. 데이터 다이어트 및 병합
    refined_profiles = []
    for p in raw_profiles:
        name = p.get("HG_NM", "").strip()
        pic_url = photo_map.get(name, "")

        refined_profiles.append({
            "HG_NM": name,
            "POLY_NM": p.get("POLY_NM", ""),
            "ORIG_NM": p.get("ORIG_NM", ""),
            "CMITS": p.get("CMITS") or p.get("CMIT_NM", ""),
            "REELE_GBN_NM": p.get("REELE_GBN_NM", ""),
            "UNITS": p.get("UNITS", ""),
            "STAFF": p.get("STAFF", ""),
            "SECRETARY": p.get("SECRETARY", ""),
            "SECRETARY2": p.get("SECRETARY2", ""),
            "MEM_TITLE": p.get("MEM_TITLE", ""),
            "HOMEPAGE": p.get("HOMEPAGE", ""), 
            "NAAS_PIC": pic_url,
            "MONA_CD": p.get("MONA_CD", "") # 프론트엔드 최후의 방어용
        })

    # 4. 3번 칸: 본회의 투표 데이터 (22대 강제 고정)
    print("🗳️ 본회의 투표 현황 추적 중 (최근 30건)...")
    plenary_bills = fetch_data("ncocpgfiaoituanbr", {"AGE": "22", "pSize": 30})
    
    votes_list = []
    if plenary_bills:
        for bill in plenary_bills:
            b_id = bill.get("BILL_ID")
            b_name = bill.get("BILL_NAME")
            if not b_id: continue
            
            # 각 의안별 의원들의 투표 결과 싹쓸이
            v_rows = fetch_data("nzmimeepazxkubdpn", {"BILL_ID": b_id, "AGE": "22", "pSize": 300})
            for v in v_rows:
                votes_list.append({
                    "HG_NM": v.get("HG_NM", "").strip(),
                    "BILL_NM": b_name,
                    "RESULT_VOTE_NM": v.get("RESULT_VOTE_MOD", "미투표"),
                    "VOTE_DATE": v.get("VOTE_DATE", "")
                })

    # 5. 최종 DB 저장
    final_db = {
        "profiles": refined_profiles,
        "votes": votes_list,
        "bills": fetch_data("ALLBILL", {"pSize": 500}),
        "minutes": fetch_data("ncwgseseafwbuheph", {"pSize": 500}),
        "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    }

    with open("radar_db.json", "w", encoding="utf-8") as f:
        json.dump(final_db, f, ensure_ascii=False)
        
    print(f"✅ 작전 완료: DB 갱신 성공.")
