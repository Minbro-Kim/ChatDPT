import requests
from bs4 import BeautifulSoup
from schemas import Item, ItemDetail, ImageTitle,Button
from typing import List
from datetime import datetime, timezone, timedelta

def get_today_query():
    # 한국 표준시 (KST) 시간대 설정
    kst = timezone(timedelta(hours=9))

    # 오늘의 날짜를 KST 기준으로 가져옴
    now = datetime.now(kst)
    midnight_kst = datetime(year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0, tzinfo=kst)

    # 타임스탬프 계산
    timestamp_kst_midnight = int(midnight_kst.timestamp())
    # 요일 계산
    timestamp_kst_date = midnight_kst.weekday()

    return f"&sday={timestamp_kst_midnight}&sdate={timestamp_kst_date}"

def fetch_meal_info() -> List[Item]:
    # url로 soup 정보 얻기
    base_url = "https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"
    url = base_url + get_today_query()
    # url = "https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1&sday=1733756400&sdate=0"
    response = requests.get(url)
    response.encoding = 'euc-kr'  # 인코딩 설정 추가
    soup = BeautifulSoup(response.text, 'html.parser')

    # 오늘의 식단 table 추출
    sdetail_div = soup.select_one("div#sdetail")
    meal_items = sdetail_div.select("p > table")[1:]
    goyang_items = sdetail_div.select("table > tr > td div > table")
    if not meal_items: return {"error": "No Board Found"}
    chunk_size = 2
    meal_chunked_items = [meal_items[i:i + chunk_size] for i in range(0, len(meal_items), chunk_size)] + [goyang_items]
    
    # 식단 정보를 저장할 리스트
    item_list: List[Item] = []

    for [meal_title, meal_info] in meal_chunked_items:
        try:
            # 식당 이름
            title = meal_title.select_one("td.menu_st").text.strip()
            if not title: continue

            if title == "상록원3층식당":
                item_list.append(fetch_sangrok_three_info(meal_info))

            if title == "상록원2층식당":
                item_list.append(fetch_sangrok_two_info(meal_info))
                
            if title == "상록원1층식당(솥앤누들)":
                item_list.append(fetch_sangrok_one_info(meal_info))
                
            if title == "가든쿡":
                item_list.append(fetch_garden_cook_info(meal_info))
                
            if title == "누리터 식당(일산캠퍼스)":
                item_list.append(fetch_ilsan_campus_info(meal_info))
            
        except AttributeError:
            continue  # 정보가 없는 항목은 스킵

    return item_list if item_list else {"error": "No Meals found"}

def fetch_sangrok_three_info(meal_info) -> Item:
    meal_index = meal_info.select("td.mft")
    meal_content = meal_info.select("td.ft2")
    
    # 휴무일
    if not meal_content:
        return Item(
            imageTitle = ImageTitle(
                title="상록원 3층 식당",
                description="교직원 식당"
            ),
            itemList = [
                ItemDetail(title="❗", description='휴무')
            ],
            buttons=[
                Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
                Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
            ]
        )

    # 메뉴 추출
    lunch_home = meal_content[0].text.strip()
    lunch_bowl = meal_content[1].text.strip()
    dinner_home = meal_content[2].text.strip()
    dinner_bowl = meal_content[3].text.strip()

    # index 추출
    home_index, bowl_index = meal_index[1].text.strip(), meal_index[2].text.strip()
    lunch_index, dinner_index = meal_index[3].text.strip(), meal_index[4].text.strip()

    return Item(
        imageTitle = ImageTitle(
            title="상록원 3층 식당",
            description="교직원 식당"
        ),
        itemList = [
            ItemDetail(title=f"{lunch_index} {home_index}", description=lunch_home),
            ItemDetail(title=f"{lunch_index} {bowl_index}", description=lunch_bowl),
            ItemDetail(title=f"{dinner_index} {home_index}", description=dinner_home),
            ItemDetail(title=f"{dinner_index} {bowl_index}", description=dinner_bowl)
        ],
        buttons=[
            Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
            Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
        ]
    )


def fetch_sangrok_two_info(meal_info) -> Item:
    meal_index = meal_info.select("td.mft") + meal_info.select("span.mft")
    meal_content = meal_info.select("td.ft2")

    # 휴무일
    if not meal_content:
        return Item(
            imageTitle = ImageTitle(
                title="상록원 2층 식당",
                description="상록원 학생식당"
            ),
            itemList = [
                ItemDetail(title="❗", description='휴무')
            ],
            buttons=[
                Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
                Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
            ]
        )

    # 메뉴 추출
    lunch_korean, lunch_bowl, lunch_western, lunch_dduk = (meal_content[i].text.strip() for i in range(0, 4))
    dinner_korean, dinner_bowl, dinner_western, dinner_dduk = (meal_content[i].text.strip() for i in range(4, 8))
    
    # index 추출
    korean_index, bowl_index, western_index, dduk_index = (meal_index[i].text.strip() for i in range(1, 5))
    lunch_index, dinner_index = meal_index[5].text.strip(), meal_index[6].text.strip()

    return Item(
        imageTitle = ImageTitle(
            title="상록원 2층 식당",
            description="상록원 학생식당"
        ),
        itemList = [
            ItemDetail(title=f"{lunch_index} {korean_index}", description=lunch_korean),
            ItemDetail(title=f"{lunch_index} {bowl_index}", description=lunch_bowl),
            ItemDetail(title=f"{lunch_index} {western_index}", description=lunch_western),
            ItemDetail(title=f"{lunch_index} {dduk_index}", description=lunch_dduk),
            ItemDetail(title=f"{dinner_index} {korean_index}", description=dinner_korean),
            ItemDetail(title=f"{dinner_index} {bowl_index}", description=dinner_bowl),
            ItemDetail(title=f"{dinner_index} {western_index}", description=dinner_western),
            ItemDetail(title=f"{dinner_index} {dduk_index}", description=dinner_dduk)
        ],
        buttons=[
            Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
            Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
        ]
    )

def fetch_sangrok_one_info(meal_info) -> Item:
    meal_index = meal_info.select("td.mft") + meal_info.select("span.mft")
    meal_content = meal_info.select("td.ft2")
    
    # 휴무일
    if not meal_content:
        return Item(
            imageTitle = ImageTitle(
                title="상록원 1층 식당",
                description="솥앤누들"
            ),
            itemList = [
                ItemDetail(title="❗", description='휴무')
            ],
            buttons=[
                Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
                Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
            ]
        )

    # 메뉴 추출
    sot_lunch_dinner, bun_lunch_dinner = (meal_content[i].text.strip() for i in range(0, 2))
    
    # index 추출
    menu_index = meal_index[1].text.strip()
    lunch_dinner_index = meal_index[2].text.strip()

    return Item(
        imageTitle = ImageTitle(
            title="상록원 1층 식당",
            description="솥앤누들"
        ),
        itemList = [
            ItemDetail(title=f"{menu_index} {lunch_dinner_index}", description=sot_lunch_dinner),
            ItemDetail(title=f"{menu_index} {lunch_dinner_index}", description=bun_lunch_dinner)
        ],
        buttons=[
            Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
            Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
        ]
    )

def fetch_garden_cook_info(meal_info) -> Item:
    meal_index = meal_info.select("td.mft") + meal_info.select("span.mft")
    meal_content = meal_info.select("td.ft2")
    
    # 휴무일
    if not meal_content:
        return Item(
            imageTitle = ImageTitle(
                title="가든쿡",
                description=""
            ),
            itemList = [
                ItemDetail(title="❗", description='휴무')
            ],
            buttons=[
                Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
                Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
            ]
        )

    # 메뉴 추출
    dish_lunch_dinner, drink_lunch_dinner = (meal_content[i].text.strip() for i in range(0, 2))
    
    # index 추출
    menu_index = meal_index[1].text.strip()
    lunch_dinner_index = meal_index[2].text.strip()

    return Item(
        imageTitle = ImageTitle(
            title="가든쿡",
            description=""
        ),
        itemList = [
            ItemDetail(title=f"{menu_index} {lunch_dinner_index}", description=dish_lunch_dinner),
            ItemDetail(title=f"{menu_index} {lunch_dinner_index}", description=drink_lunch_dinner)
        ],
        buttons=[
            Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
            Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
        ]
    )

def fetch_ilsan_campus_info(meal_info) -> Item:
    meal_index = meal_info.select("td.mft")
    meal_content = meal_info.select("td.ft2")
    
    # 휴무일
    if not meal_content:
        return Item(
            imageTitle = ImageTitle(
                title="누리터식당",
                description="일산캠퍼스 학생식당"
            ),
            itemList = [
                ItemDetail(title="❗", description='휴무')
            ],
            buttons=[
                Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
                Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
            ]
        )

    # 메뉴 추출
    dish_breakfast = meal_content[0].text.strip()
    nuri_lunch, nuri_dinner = (meal_content[i].text.strip() for i in (1, 4))
    jin_lunch_dinner = meal_content[2].text.strip()
    pan_lunch_dinner = meal_content[3].text.strip()

    # index 추출
    breakfast_index = meal_index[0].text.strip()
    nuri_index, jin_index, pan_index = (meal_index[i].text.strip() for i in range(2, 5))
    lunch_index, dinner_index = meal_index[5].text.strip(), meal_index[6].text.strip()

    return Item(
        imageTitle = ImageTitle(
            title="누리터식당",
            description="일산캠퍼스 학생식당"
        ),
        itemList = [
            ItemDetail(title=f"{breakfast_index}", description=dish_breakfast),
            ItemDetail(title=f"{lunch_index} {nuri_index}", description=nuri_lunch),
            ItemDetail(title=f"{dinner_index} {nuri_index}", description=nuri_dinner),
            ItemDetail(title=f"{jin_index}", description=jin_lunch_dinner),
            ItemDetail(title=f"{pan_index}", description=pan_lunch_dinner),
        ],
        buttons=[
            Button(label="오늘의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1"),
            Button(label="주간의 학식 보기", action="webLink", webLinkUrl="https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=2")
        ]
    )

if __name__ == "__main__":
    fetch_meal_info()