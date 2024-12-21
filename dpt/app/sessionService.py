import time
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

class SessionService:
    _instance = None  # 인스턴스를 저장할 클래스 변수

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SessionService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # 한 번만 초기화되도록 보장
            self.sessions = {}  # {userid: {last_used: timestamp, data: chat_history}}
            self.expiry_time = 60*10  # 10분 (초 단위)
            self.initialized = True

    def update_session(self, sessionid: str, role: str, content: str):
        """세션을 생성하거나 갱신, 역할에 따른 메시지 추가"""
        current_time = time.time()
        
        if sessionid not in self.sessions:
            # 새로운 세션 생성
            self.sessions[sessionid] = {
                "last_used": current_time,
                "data": ChatMessageHistory()
            }
        print(self.sessions[sessionid])
        
        # 세션 갱신: 시간 업데이트
        self.sessions[sessionid]["last_used"] = current_time

        # 역할에 맞는 메시지 추가 (role: user 또는 assistant)
        if content:
            # role과 content를 포함한 메시지 객체 생성
            message = {"role": role, "content": content}
            self.sessions[sessionid]["data"].messages.append(message)
            print(self.sessions[sessionid])

    def get_session_history(self, userid: str)-> BaseChatMessageHistory:
        """세션 내역 조회"""
        if userid not in self.sessions:
            self.update_session(sessionid=userid, role="user", content="")  # 기본 세션 생성
        return self.sessions[userid]["data"]

    def clean_expired_sessions(self):
        """만료된 세션 제거"""
        current_time = time.time()
        expired_users = [
            sessionid for sessionid, session in self.sessions.items()
            if current_time - session["last_used"] > self.expiry_time
        ]
        for sessionid in expired_users:
            del self.sessions[sessionid]
            print(f"세션 {sessionid}을 제거했습니다.")