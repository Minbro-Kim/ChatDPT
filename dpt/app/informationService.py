import requests
from bs4 import BeautifulSoup
import re
from PIL import Image
import base64
from io import BytesIO
from urllib.parse import urljoin
from openai import OpenAI
from ragService import database
from langchain_text_splitters import RecursiveCharacterTextSplitter

client = OpenAI()

TYPE_MAPPING = {
    "GENERALNOTICES": "일반공지",
    "HAKSANOTICE": "학사공지",
    "JANGHAKNOTICE": "장학공지",
    "BUDDHISTEVENT": "행사공지"
}
# 게시물 목록을 크롤링하는 함수
def crawl_board_list(url: str,n:int=1,notice_type:str = "GENERALNOTICES"):
    try:
        
        listurl = f"{url}/list?pageIndex={n}&"
        # 웹 페이지 요청 (목록 크롤링)
        response = requests.get(listurl)
        if response.status_code != 200:
            return {"error": "웹 페이지를 가져오는 데 실패했습니다."}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 'board_list' 클래스 내의 <ul> 태그 내에 있는 모든 <li> 태그를 찾음
        board_list = soup.find('div', class_='board_list')
        if not board_list:
            return {"error": "게시판 목록을 찾을 수 없습니다."}

        posts = board_list.find_all('li')  # <li> 태그들 찾기
        
        result = []  # 크롤링된 결과를 담을 리스트
        
        # 게시물 목록 저장
        for post in posts:
            num_span = post.find('span', class_='num')  
            
            if num_span:
                num = num_span.get_text(strip=True)
                title = post.find('p', class_='tit')  # 제목이 있는 p 태그 찾기
                date = post.find('div', class_='info').find('span')  # 날짜, 작성자 등의 정보가 있는 span 태그 찾기
                onclick = post.find('a', onclick=True)  # onclick 속성이 있는 a 태그 찾기
                
                if onclick:
                    # onclick 속성에서 숫자 추출 (goDetail(26758339); 형태에서 숫자만 추출)
                    match = re.search(r'goDetail\((\d+)\);', onclick['onclick'])
                    if match:
                        post_id = match.group(1)
                        post_url = f"{url}/detail/{post_id}"  # 게시물 ID를 이용해 게시물 상세 URL 생성
                        # 이미 해당 post_id가 Chroma에 존재하는지 확인
                        # 타입을 한국어로 변환
                        korean_type = TYPE_MAPPING.get(notice_type, '기타 공지')
                        
                        
                        existing_docs = database.get(
                            where = {"$and": [
                                {"post_id": {"$eq": post_id}},
                                {"notice_type": {"$eq":korean_type}}
                            ]}
                        )
                        

                        # 이미 존재하는 게시물은 목록에 추가하지 않음
                        if not existing_docs['ids']:
                            post_data = {"title": title.get_text(strip=True) if title else "제목 없음",
                                         "date": date.get_text(strip=True) if date else "정보 없음",
                                         "num": num,
                                         "post_id": post_id,
                                         "post_url": post_url}
                            result.append(post_data)

        #print(f"결과가 나오면 안된다이{result}")
        return result
    
    
    
    except Exception as e:
        return {"error": str(e)}

# 게시물 상세 정보를 크롤링하는 함수
def crawl_post_details(item):
    try:
        # 게시물 상세 페이지 요청
        post_url =item['post_url']
        post_response = requests.get(post_url)
        if post_response.status_code != 200:
            return {"error": f"{post_url} 페이지를 가져오는 데 실패했습니다."}
        
        post_soup = BeautifulSoup(post_response.text, 'html.parser')
        div_section = post_soup.find('div', class_='view_cont')

        post_data = {}
        post_data['title'] = item['title']
        post_data['date'] = item['date']
        post_data['post_id'] = item['post_id']
        post_data['post_url'] = post_url
        if div_section:
            
            content_text = div_section.get_text(separator='\n', strip=True)
            post_data["content"] = content_text
            
            # 이미지 태그 찾기
            img_tag = div_section.find('img')
            if img_tag and 'src' in img_tag.attrs:
                image_url = img_tag.attrs['src']
                image_url = urljoin(post_url, image_url)
                post_data["image_url"] = image_url
                
                # 이미지에서 텍스트 "추출"
                image_text = analyze_image_from_url(image_url=image_url)
                post_data["content"] += image_text
                

        return post_data

    except Exception as e:
        return {"error": str(e)}
    
# 이미지 URL을 통해 텍스트 추출 함수
def analyze_image_from_url(image_url: str):
    # 이미지 URL을 통해 이미지 다운로드
    # 이미지 URL을 통해 이미지 다운로드
    image_response = requests.get(image_url)
    
    # 이미지가 성공적으로 다운로드 되었는지 확인
    if image_response.status_code != 200:
        return {"error": "이미지를 다운로드하는 데 실패했습니다."}
    
    # 이미지 열기
    img = Image.open(BytesIO(image_response.content))
    # RGBA 이미지를 RGB로 변환
    if img.mode == 'RGBA':
        img = img.convert('RGB')


    # 이미지를 base64로 인코딩
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)  # 포인터를 처음으로 이동시킴
    current_base64_image = base64.b64encode(img_bytes.read()).decode("utf-8")

    # GPT-4에 이미지 텍스트 변환 요청
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Turn an image into text with as much content as possible. Don't use special characters, write in lines. and Answer in Korean."},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{current_base64_image}"}}]}
        ]
    )

    # GPT-4 응답에서 텍스트 추출
    advice = response.choices[0].message.content
    return advice

def start_crawling(n:int=1):
    notice_type = ["GENERALNOTICES","HAKSANOTICE","JANGHAKNOTICE","BUDDHISTEVENT"]
    #notice_type = ["GENERALNOTICES"]
    
    
    for notice in notice_type:  # notice_type을 순회하며 크롤링
        url = f'https://www.dongguk.edu/article/{notice}'  # 공지사항 종류에 맞는 URL 생성
        post_list = []  # 모든 게시물 정보를 담을 리스트
        for page_num in range(1, n + 1):  # n만큼 반복 (1부터 n까지)
            #print(f"{notice} 크롤링 중... 페이지 {page_num}")
            
            # 각 페이지 크롤링
            board_list = crawl_board_list(url=url, n=page_num,notice_type=notice)
            
            # 각 게시물의 상세 정보를 크롤링
            for item in board_list:
                post_data = crawl_post_details(item)
                post_list.append(post_data)
    
        for post_data in post_list:
            if 'error' not in post_data:
                save_to_chroma(post_data,notice_type=notice)
                

# 게시물 내용을 청크로 쪼개서 Chroma에 저장하는 함수
def save_to_chroma(post_data,notice_type:str="GENERALNOTICES"):
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=100)
        # 게시물 내용을 텍스트로 추출
        content = post_data.get('content', '')
        post_url = post_data.get('post_url', '')
        post_date = post_data.get('date', '')  # 공지사항 작성일자 가져오기
        # 타입을 한국어로 변환
        korean_type = TYPE_MAPPING.get(notice_type, '기타 공지')  # 매핑되지 않으면 '기타'로 처리

        # URL과 내용을 결합
        combined_text = f"URL: {post_url}\n\n{content}"
        
        # 텍스트 분할
        documents = text_splitter.split_text(combined_text)
        
        # 분할된 텍스트와 메타데이터를 Chroma에 저장
        database.add_texts(
            texts=documents,
            metadatas=[
                {
                    "post_id": post_data.get("post_id"),
                    "url": post_url,
                    "date": post_date,  # 공지사항 작성일자 추가
                    "chunk_index": i,
                    "notice_type": korean_type,
                }
                for i in range(len(documents))
            ],
            ids=[f"{post_data.get('post_id')}-{i}" for i in range(len(documents))]
        )
        
        #print(f"게시물 {post_data['post_id']}의 데이터를 Chroma에 저장했습니다.")
        #print("끝!")
    except Exception as e:
        print(f"Chroma 저장 중 오류 발생: {str(e)}")


    