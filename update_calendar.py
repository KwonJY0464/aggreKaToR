import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Referer': 'https://kiat.or.kr/'
}
URL = "https://kiat.or.kr/front/board/boardContentsListPage.do?board_id=90"

def final_check():
    res = requests.get(URL, headers=HEADERS, timeout=20)
    res.encoding = 'utf-8'
    html = res.text
    
    print(f"📊 총 글자 수: {len(html)}자")
    
    # 1. '기반구축' 단어가 전체 코드에 몇 번 나오는지 확인
    count = html.count("기반구축")
    print(f"🔍 '기반구축' 단어 발견 횟수: {count}회")
    
    # 2. '공고'라는 단어는 나오는지 확인 (게시판인지 확인용)
    notice_count = html.count("공고")
    print(f"🔍 '공고' 단어 발견 횟수: {notice_count}회")

    # 3. 만약 0회라면, 봇이 보고 있는 텍스트의 중간 부분을 출력 (진짜 정체 확인)
    if count == 0:
        print("\n👀 봇이 읽어온 텍스트 중간 부분 (실제 내용):")
        print(html[20000:20500]) # 5만 자 중 중간 500자 출력

if __name__ == "__main__":
    final_check()
