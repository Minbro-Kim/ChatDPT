from pydantic import BaseModel
# 요청 본문에 대한 DTO 정의
class Intent(BaseModel):
    id: str
    name: str

class User(BaseModel):
    id: str
    type: str
    properties: dict

class Block(BaseModel):
    id: str
    name: str

class UserRequest(BaseModel):
    callbackUrl: str
    timezone: str
    params: dict
    block: Block
    utterance: str
    lang: str | None
    user: User

class Bot(BaseModel):
    id: str
    name: str

class Action(BaseModel):
    name: str
    clientExtra: dict | None
    params: dict
    id: str
    detailParams: dict

class RequestDto(BaseModel):
    intent: Intent
    userRequest: UserRequest
    bot: Bot
    action: Action
    

#응답
class SimpleText(BaseModel):
    text: str

class Output(BaseModel):
    simpleText: SimpleText

class Template(BaseModel):
    outputs: list[Output]

class ResponseDto(BaseModel):
    version: str
    template: Template

class CallBackResponseDto(BaseModel):
    useCallback : bool
    version: str
    template: Template