import requests
from bs4 import BeautifulSoup
from schemas import Item, ItemDetail, ImageTitle,Button
from typing import List

def fetch_book_info(query: str):
    base_url = "https://lib.dongguk.edu/searchTotal/result?st=KWRD&si=TOTAL&q="
    lib_url = "https://lib.dongguk.edu"
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
    item_list : List[Item] = []

    # 각 책 정보를 순회하며 추출
    for book in book_items:
        try:
            title =book.select_one('p.listTitle > a').text.strip()  # 책 제목
            if not title:  # 책 제목이 없으면 저장하지 않고 넘어감
                continue
            detail = book.select_one('p.listTitle > a').get('href')
            author = book.select_one('div.information > p:nth-of-type(2)').text.strip() if book.select_one('div.information > p:nth-of-type(2)') else ""  # 저자
            publisher = book.select_one('div.information > p:nth-of-type(3)').text.strip() if book.select_one('div.information > p:nth-of-type(3)') else ""  # 출판사
            year = book.select_one('div.information > p:nth-of-type(4)').text.strip() if book.select_one('div.information > p:nth-of-type(4)') else ""  # 출판연도
            book_type = book.select_one('div.information > p.type img')['title'] if book.select_one('div.information > p.type img') else '정보 없음'
            location_list = book.select('div.holdingInfo > div.holding > p.location')
            library_details = [
                ItemDetail(
                    title=f"🚩 {loc.select_one('a').contents[0].strip().replace('바이오약학도서관', '약학도서관')}",
                    description= loc.select_one('span').text.strip()
                )
                for loc in location_list if loc.select_one('a') and loc.select_one('span')
            ]
            
                        # DTO에 맞는 데이터 변환
            item = Item(
                imageTitle=ImageTitle(
                    title=f"📚 {title}",
                    description=f"   {author}"
                ),
                itemList=[
                    ItemDetail(title="📜 자료유형", description=book_type),
                    ItemDetail(title="🖨️ 발행사항", description=f"{publisher} ({year})"),
                ] + library_details,  # 소장정보를 itemList에 추가
                buttons=[
                    Button(label="도서 상세 정보", action="webLink", webLinkUrl=lib_url + detail),
                    Button(label="모든 검색 결과", action="webLink", webLinkUrl=url),
                ]
            )

            item_list.append(item)
        except AttributeError:
            continue  # 정보가 없는 항목은 스킵

    return item_list if item_list else {"error": "No books found"}
