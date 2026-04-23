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
        print(f"API 호출 에러: {e}")
    return []

if __name__ == "__main__":
    current_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] 🚀 [ALLNAMEMBER] 최신 데이터 정제 개시...")
    
    final_profiles = []
    
    for i in range(1, 8):
        members = fetch_data("ALLNAMEMBER", {"pIndex": i, "pSize": 1000})
        if not members: break
        
        for m in members:
            eraco = str(m.get("GTELT_ERACO", ""))
            
            if "22대" in eraco:
                name = m.get("NAAS_NM", "").strip() 
                pic_url = m.get("NAAS_PIC", "")
                if not isinstance(pic_url, str): pic_url = ""
                pic_url = pic_url.strip()
                
                # 💡 과거 기록 쳐내기: '/' 기준으로 쪼갠 후 맨 마지막 요소만 가져옵니다.
                raw_poly = m.get("PLPT_NM", "")
                raw_orig = m.get("ELECD_NM", "")
                
                poly_nm = raw_poly.split("/")[-1].strip() if raw_poly else ""
                orig_nm = raw_orig.split("/")[-1].strip() if raw_orig else ""
                
                if not any(p["HG_NM"] == name for p in final_profiles):
                    final_profiles.append({
                        "HG_NM": name,                                  
                        "POLY_NM": poly_nm,                             # 수정됨 (최신 정당)
                        "ORIG_NM": orig_nm,                             # 수정됨 (최신 선거구)
                        "CMITS": m.get("BLNG_CMIT_NM", "") or m.get("CMIT_NM", ""),
                        "REELE_GBN_NM": m.get("RLCT_DIV_NM", ""),       
                        "UNITS": eraco,                                 
                        "STAFF": m.get("AIDE_NM", ""),                  
                        "SECRETARY": m.get("CHF_SCRT_NM", ""),          
                        "SECRETARY2": m.get("SCRT_NM", ""),             
                        "MEM_TITLE": m.get("BRF_HST", ""),              
                        "HOMEPAGE": m.get("NAAS_HP_URL", ""),           
                        "NAAS_PIC": pic_url                             
                    })
                    
    with open("profiles_db.json", "w", encoding="utf-8") as f:
        json.dump(final_profiles, f, ensure_ascii=False)

    print(f"✅ 프로필 DB 정제 완료! (총 {len(final_profiles)}명, 최신 정당/선거구 분리 적용)")
