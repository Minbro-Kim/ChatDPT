from sessionService import SessionService
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, FewShotChatMessagePromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from config import answer_examples
from ragService import database,llm
import asyncio


session_service = SessionService()

def get_retriever():
    retriever=database.as_retriever()
    return retriever

def get_history_retriever():
    retriever = get_retriever()
    
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "Which might reference context in the chat history, "
        "Formulate a standalone question which can be understood "
        "Without the chat history. Do NOT answer the question, "
        "Just reformulate it if needed and otherwise return it as is."
        "Let"
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    return history_aware_retriever


def get_dictionary_chain():
    dictionary = ["오픽 -> OPIc", "토익 -> TOEIC", "초과학기 -> 학점등록", "졸업유예 -> 선택적 수료"]
    prompt = ChatPromptTemplate.from_template(f"""
        사용자의 질문을 보고, 우리의 사전을 참고해서 사용자의 질문을 변경해주세요.
        만약 변경할 필요가 없다고 판단된다면, 사용자의 질문을 변경하지 않아도 됩니다.
        그런 경우에는 질문만 리턴해주세요
        사전: {dictionary}
        
        질문: {{question}}
    """)

    dictionary_chain = prompt | llm | StrOutputParser()
    
    return dictionary_chain

def get_rag_chain():
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{answer}"),
        ]
    )
    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=answer_examples,
    )
    system_prompt = (
    "You are an AI assistant who answers questions related to school life of Dongguk University students."
    "Use the following pieces of retrieved context to answer the question."

    "1. Please answer in the questioning language. For example, if the Question is in English, answer in English. Or if the Question is in Chinese, answer in Chinese."
    "2. If you answer in Korean, please answer in a friendly way as if you are talking to a friend without being too formal. For example, '통계학과의 졸업 요건은 다음과 같아요!', '2학기 등록금 납부 기간은 ~~~예요!'"
    "3. Please answer by mixing appropriate happiness-emoticons when answering. For example, '전액장학생의 경우, 포털시스템에서 '0원' 등록 신청을 하시면 됩니다. 😊', '동국대학교는 다양한 장학금을 통해 학생들의 꿈을 지원하고 있어요. 🌟'"
    "4. Please present the page of the document you referred to when answering in the following format."
    " # format : * \n위 답변은 2024 신입생 학업이수가이드 ??? 페이지를 참고해 작성되었습니다. \n학업이수가이드 바로가기 : https://www.dongguk.edu/resources/pdf/2024_edu_final.pdf"

    "5. **IMPORTANT INSTRUCTION**: If a user's question varies depending on various situations or environments, **you MUST ask follow-up questions** to gather necessary information before providing an answer."
    "**This is very important!** If you don't have enough information, do not guess or make assumptions. **Instead, ask clarifying questions.**"
    "For example, if a user asks a question about '등록금', it may differ based on whether the user is an undergraduate or a graduate student. In this case, if this information is missing, you should ask the user: 'Are you an undergraduate or a graduate student?'"
    "Another example: if a user asks a question related to '공통교양', it can vary based on the year of admission. If the year of admission is not specified, you should ask: 'When did you enter the university?'"
    "Consider additional factors such as whether the user is a regular student or a transfer student, as this can also impact your response."
    "**Always ensure you have all the necessary information before answering.** If any critical information is missing, ask follow-up questions first."

    "6. You should never answer with inaccurate or incorrect content. If you can't answer the question accurately, do not provide any reference pages. Let's think step by step!"
    "7. If you have any additional questions regarding this, please also let me know the phone number of the department I can connect with."
    
    "답변할 때 제목은 출력하지 말고 사용자가 묻는 것에만 깔끔하게 답변해."

    "Remember this! If you get the same question as a few-shot, answer the same question as fewshot anwser"
    "Remember this! Please answer in the questioning language. For example, if the Question is in English, answer in English. Or if the Question is in Chinese, answer in Chinese."

    "Let's think step by step!"
    "{context}"
)

    
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            few_shot_prompt,
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = get_history_retriever()
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        session_service.get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    ).pick('answer')
    
    return conversational_rag_chain

async def get_ai_response(user_message,sessionid:str):
    dictionary_chain = get_dictionary_chain()
    
    rag_chain = get_rag_chain()
    tax_chain = {"input": dictionary_chain} | rag_chain
    #print("여기까지는 무사히 되었다...")

    ai_response =  await asyncio.to_thread(tax_chain.invoke,
        {
            "question": user_message
        },
        config={
            "configurable": {
                "session_id": sessionid
            }
        },
    )
    #print(ai_response)
    return ai_response  # 반환