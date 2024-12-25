from pydantic import BaseModel
from pydantic import BaseModel
from typing import List, Optional
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
    
class QuickReplies(BaseModel):
    messageText: Optional[str] ="중앙도서관에서 도서 검색을 하고 싶어!"
    action: Optional[str] = "message"
    label: Optional[str] =  "🔍 다시 검색하기"
    
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

class Template2(BaseModel):
    outputs: list[Output]
    quickReplies: list[QuickReplies]
    
class BookResponseDto(BaseModel):
    version: str
    template: Template2
    


class CallBackResponseDto(BaseModel):
    useCallback : bool
    version: str
    template: Template
    
class BookUserRequest(BaseModel):
    timezone: str
    params: dict
    block: Block
    utterance: str
    lang: str | None
    user: User

class BookRequestDto(BaseModel):
    intent: Intent
    userRequest: BookUserRequest
    bot: Bot
    action: Action
    
class MealRequestDto(BaseModel):
    intent: Intent
    bot: Bot
    action: Action

class Button(BaseModel):
    label: str
    action: str
    webLinkUrl: str

class ItemDetail(BaseModel):
    title: str
    description: str

class ImageTitle(BaseModel):
    title: str
    description: str

class Item(BaseModel):
    imageTitle: ImageTitle
    itemList: List[ItemDetail]
    itemListAlignment: Optional[str] = "right"  # 기본값 설정 가능
    buttons: List[Button]
