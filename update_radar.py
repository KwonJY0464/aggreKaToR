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
    print("🚀 [작전명: 사진 복구] 22대 국회 레이더 가동...")
    
    # 1. 22대 현역 의원 인적사항 (nwvrqwxyaytdsfvhu)
    # 여기에 'HG_NM', 'BTH_DATE', 'HOMEPAGE' 등이 다 들어있습니다.
    raw_profiles = fetch_data("nwvrqwxyaytdsfvhu", {"pSize": 300})
    
    # 💡 2. 22대 현역 의원 사진 전용 매칭 (ALLNAMEMBER)
    # AGE=22 또는 UNIT=22를 사용하여 22대 의원 사진 주소만 정확히 추출
# 💡 2. 22대 현역 의원 사진 전용 매칭 (ALLNAMEMBER)
    print("📸 22대 의원 사진 주소(NAAS_PIC) 수집 중...")
    photo_data = fetch_data("ALLNAMEMBER", {"UNIT": "22", "pSize": 500})
    
    # 생년월일 포맷 불일치 에러를 막기 위해 오직 '이름(HG_NM)'만 사용
    photo_map = {}
    for m in photo_data:
        name = m.get("HG_NM", "").strip()
        if name:
            # API가 준 진짜 사진 URL을 어떠한 가공도 없이 그대로 저장!
            photo_map[name] = m.get("NAAS_PIC", "")

    # 3. 데이터 다이어트 및 병합
    refined_profiles = []
    for p in raw_profiles:
        name = p.get("HG_NM", "").strip()
        
        # 이름으로 1:1 직결 매칭
        pic_url = photo_map.get(name, "")
        
        # (혹시라도 빈칸일 경우를 대비한 최후의 보루)
        if not pic_url:
            pic_url = f"https://www.assembly.go.kr/static/portal/img/open_data/member/{p.get('MONA_CD')}.jpg"

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
            "NAAS_PIC": pic_url               # 원본 사진 주소 완벽 적용
        })

    # 4. 3번 칸: 본회의 투표 데이터 (22대 강제 고정)
    print("🗳️ 본회의 투표 현황 추적 중 (최근 30건)...")
    plenary_bills = fetch_data("ncocpgfiaoituanbr", {"AGE": "22", "pSize": 30})
    
    votes_list = []
    if plenary_bills:
        for bill in plenary_bills:
            b_id = bill.get("BILL_ID")
            b_name = bill.get("BILL_NAME")
            # 각 의안별 의원들의 투표 결과 싹쓸이
            v_rows = fetch_data("nzmimeepazxkubdpn", {"BILL_ID": b_id, "AGE": "22", "pSize": 300})
            for v in v_rows:
                votes_list.append({
                    "HG_NM": v.get("HG_NM", "").strip(),
                    "BILL_NM": b_name,
                    "RESULT": v.get("RESULT_VOTE_MOD", "미투표"),
                    "DATE": v.get("VOTE_DATE", "")
                })

    # 5. 최종 DB 저장
    final_db = {
        "profiles": refined_profiles,
        "votes": votes_list,
        "bills": fetch_data("ALLBILL", {"pSize": 500}), # 최근 발의 의안
        "minutes": fetch_data("ncwgseseafwbuheph", {"pSize": 500}), # 최근 회의록
        "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    }

    with open("radar_db.json", "w", encoding="utf-8") as f:
        json.dump(final_db, f, ensure_ascii=False)
        
    print(f"✅ 작전 완료: {len(refined_profiles)}명의 사진 및 {len(votes_list)}건의 투표 데이터 확보.")
