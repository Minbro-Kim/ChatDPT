import time
from timer import Timer

class SessionService:
    def __init__(self):
        self.sessions = {}  # {userid: {last_used: timestamp, data: chat_history}}
        self.expiry_time = 24 * 60 * 60  # 24시간 (초 단위)

    def update_session(self, userid: str):
        """세션을 생성하거나 갱신"""
        current_time = time.time()
        if userid in self.sessions:
            # 세션 갱신
            self.sessions[userid]["last_used"] = current_time
        else:
            # 새로운 세션 생성
            self.sessions[userid] = {
                "last_used": current_time,
                "data": []
            }

    def get_session_history(self, userid: str):
        """세션 내역 조회"""
        if userid not in self.sessions:
            self.update_session(userid)
        return self.sessions[userid]["data"]

    def clean_expired_sessions(self):
        """만료된 세션 제거"""
        current_time = time.time()
        expired_users = [
            userid for userid, session in self.sessions.items()
            if current_time - session["last_used"] > self.expiry_time
        ]
        for userid in expired_users:
            del self.sessions[userid]

# 백그라운드 작업으로 세션 정리
timer = Timer(interval=60 * 60)  # 1시간마다 세션 정리

@timer.job
def clean_sessions_task():
    session_service = SessionService()
    session_service.clean_expired_sessions()