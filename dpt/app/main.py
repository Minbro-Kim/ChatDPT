from fastapi import FastAPI,UploadFile
from schemas import RequestDto,ResponseDto,Template, Output, SimpleText,CallBackResponseDto,Template2,BookResponseDto,BookRequestDto,QuickReplies
from langchain_community.document_loaders import PyMuPDFLoader
from ragService import process_documents, query_qa_system
from fastapi.responses import JSONResponse
from sessionService import SessionService
from chatService import get_ai_response
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
import httpx
import asyncio
import time
import logging
from informationService import start_crawling
from libService import fetch_book_info

session_service = SessionService()
# APScheduler 설정
scheduler = BackgroundScheduler()
scheduler.add_job(session_service.clean_expired_sessions, IntervalTrigger(seconds=60*10))  # 10분마다간실행
scheduler.add_job(start_crawling,IntervalTrigger(seconds=60*60*24))
# 평일 자정에 작업 실행 (월요일~금요일)
#.add_job(start_crawling, CronTrigger(day_of_week='mon-fri', hour=0, minute=0))
#scheduler.add_job(lambda: asyncio.create_task(start_crawling()), IntervalTrigger(seconds=30))  # 10초마다 실행
@asynccontextmanager
async def lifespan(app):
    # 애플리케이션 시작 시 실행될 코드
    scheduler.start()
    #start_crawling(n=10)
    #logging.info("작업 실행 중!!!...")
    yield
    # 애플리케이션 종료 시 실행될 코드
    scheduler.shutdown()
    
app = FastAPI(lifespan=lifespan)

def create_response_body(**kwargs) -> ResponseDto:
    """
    동적으로 ResponseDto를 생성하는 함수
    """
    text = kwargs.get("text", "잘 모르겠어요..ㅠ")
    return ResponseDto(
        version="2.0",
        template=Template(
            outputs=[Output(simpleText=SimpleText(text=text))]
        )
    )

def create_lib_response_body(text=str):
    """
    동적으로 ResponseDto를 생성하는 함수
    """
    return BookResponseDto(
        version="2.0",
        template=Template2(
            outputs=[Output(simpleText=SimpleText(text=text))],
            quickReplies= [QuickReplies()]
        )
    )

def create_callback_response_body() -> CallBackResponseDto:
    """
    동적으로 ResponseDto를 생성하는 함수
    """
    text = "조금만 기다려주세요~~"
    return CallBackResponseDto(
        version="2.0",
        useCallback= True,
        template=Template(
            outputs=[Output(simpleText=SimpleText(text=text))]
        )
    )
    
# 콜백 URL로 응답 보내기
async def send_callback_post(answer_task,callback_url: str):
    #print(f"콜백 전송하기")
    async with httpx.AsyncClient() as client:
        answer = await answer_task
        response_body = create_response_body(text=answer)
        #print(f"콜백 전송 완료: {response_body}")
        response = await client.post(callback_url, json=response_body.dict())
        #print(f"콜백 전송 완료: {response.status_code}")
   
@app.post("/api/query/")
async def query_qa(body: RequestDto):
    try:
        start_time = time.time()
        utterance = body.userRequest.utterance
        callback_url = body.userRequest.callbackUrl

        # 답변을 비동기적으로 받아오는 작업
        answer_task = asyncio.create_task(query_qa_system(utterance))

        # 4초 내에 답변을 받았는지 체크
        elapsed_time = 0

        while elapsed_time < 3: 
            elapsed_time = time.time() - start_time
            if answer_task.done():
                # 4초 이내에 답변이 오면 바로 응답을 반환
                answer = await answer_task
                response_body = create_response_body(text=answer)
                return response_body
            await asyncio.sleep(0.1)  # 0.1초 대기 후 다시 체크

        # 4초가 지나면 콜백 응답을 먼저 보내기
        callback_response_body = create_callback_response_body()
        # 콜백 응답을 비동기적으로 전송
        asyncio.create_task(send_callback_post(answer_task, callback_url=callback_url))

        return callback_response_body
        

    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        response_body = create_response_body(text=error_message)
        return JSONResponse(content=response_body.dict(), status_code=500)
    
# 세션 쿼리

@app.post("/api/query/session")
async def chat_with_ai(body: RequestDto):
    try:
        start_time = time.time()
        userid = body.userRequest.user.id
        user_message = body.userRequest.utterance
        callback_url = body.userRequest.callbackUrl
        # 세션 생성 또는 갱신
        session_service.update_session(sessionid=userid,role="user",content=user_message)
        # 답변을 비동기적으로 받아오는 작업
        answer_task = asyncio.create_task(get_ai_response(user_message,sessionid=userid))
        # 4초 내에 답변을 받았는지 체크
        elapsed_time = 0

        while elapsed_time < 3: 
            elapsed_time = time.time() - start_time
            if answer_task.done():
                # 4초 이내에 답변이 오면 바로 응답을 반환
                answer = await answer_task
                response_body = create_response_body(text=answer)
                return response_body
            await asyncio.sleep(0.1)  # 0.1초 대기 후 다시 체크

        # 4초가 지나면 콜백 응답을 먼저 보내기
        callback_response_body = create_callback_response_body()
        # 콜백 응답을 비동기적으로 전송
        asyncio.create_task(send_callback_post(answer_task, callback_url=callback_url))
        return callback_response_body
        
        
    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        response_body = create_response_body(text=error_message)
        return JSONResponse(content=response_body.dict(), status_code=500)
 
    
    
@app.post("/api/search-books")
async def search_books(body: BookRequestDto):
    if '책이름' not in body.action.params or not body.action.params['책이름']:
        return create_lib_response_body(text="도서정보가 잘못됐어요😣")
    bookname = body.action.params['책이름']
    result = fetch_book_info(bookname)  # `bookname` 사용
    if "error" in result:
        return create_lib_response_body(text="해당 정보의 도서가 없어요😣")
    return create_lib2_response_body(books=result,query=bookname)
 
@app.get("/")
def read_root():
    return {"message": "된다요요요요요"}

@app.post("/api/sayhello")
def say_hello(body: RequestDto):
    
    response_body = create_response_body(text=f"안녕!{body}")
    return response_body

#pdf 업로드
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile, file_name:str):
    try:
        # 업로드된 파일이 PDF인지 확인
        if not file.filename.endswith('.pdf'):
            return JSONResponse({"error": "Invalid file format. Only PDF files are allowed."}, status_code=400)

        # 'dpt/temp' 폴더에 저장
        temp_file_path = os.path.join("../temp", f"{file_name}.pdf")  # 파일 이름을 입력받아 경로 설정

        # 파일을 해당 경로에 저장
        with open(temp_file_path, "wb") as temp_file:
            file_contents = await file.read()  # 업로드된 PDF 파일의 내용
            temp_file.write(file_contents)  # 내용을 파일에 씁니다.

        print("파일 저장 완료:", temp_file_path)

        # PyMuPDFLoader는 파일 경로를 요구하므로 임시 파일 경로로 로드
        docs = PyMuPDFLoader(temp_file_path).load()

        print("파일 로드 완료!")
        result = process_documents(docs=docs, file_name=file_name)
        return JSONResponse({"message": result})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    



    
def create_lib2_response_body(books, query:str):
    result ={
            "version": "2.0",
            "template": {
                "outputs": [
                     {
                        "simpleText": {
                            "text": f"'{query}'에 대한 상위 3개의 검색 결과가 표시됩니다😀"
                        }
                    },
                    {
                        "carousel": {
                        "type": "itemCard",
                        "items": books
                        }
                    }
                ],
                "quickReplies": [
                    {
                        "messageText": "중앙도서관에서 도서 검색을 하고 싶어!",
                        "action": "message",
                        "label": "🔍 다시 검색하기"
                    }
                ]
            }
        }
    return result
