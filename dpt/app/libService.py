import requests
from bs4 import BeautifulSoup

def fetch_book_info(query: str):
    base_url = "https://lib.dongguk.edu/searchTotal/result?st=KWRD&si=TOTAL&q="
    url = base_url + query
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 소장자료 div 선택
    catalogs_div = soup.select_one('div.catalogs')

    if not catalogs_div:
        return {"error": "No catalogs found"}

    # 책 정보가 포함된 li 태그 선택
    book_items = catalogs_div.select('ul > li')

    # 책 정보를 저장할 리스트
    bookinfo_list = []

    # 각 책 정보를 순회하며 추출
    for item in book_items:
        try:
            title = item.select_one('p.listTitle > a').text.strip()  # 책 제목
            if not title:  # 책 제목이 없으면 저장하지 않고 넘어감
                continue
            author = item.select_one('div.information > p:nth-of-type(2)').text.strip() if item.select_one('div.information > p:nth-of-type(2)') else ""  # 저자
            publisher = item.select_one('div.information > p:nth-of-type(3)').text.strip() if item.select_one('div.information > p:nth-of-type(3)') else ""  # 출판사
            year = item.select_one('div.information > p:nth-of-type(4)').text.strip() if item.select_one('div.information > p:nth-of-type(4)') else ""  # 출판연도
            availability = item.select_one('div.holdingInfo > div.holding > p.location > a > span').text.strip() if item.select_one('div.holdingInfo > div.holding > p.location > a > span') else ""  # 대출 가능 여부
            # 객체 생성
            bookinfo = {
                "title": title,
                "author": author,
                "publisher": publisher,
                "year": year,
                "availability": availability
            }
            bookinfo_list.append(bookinfo)
        except AttributeError:
            continue  # 정보가 없는 항목은 스킵

    return bookinfo_list if bookinfo_list else {"error": "No books found"}
