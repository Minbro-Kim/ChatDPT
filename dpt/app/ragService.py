from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_upstage import UpstageEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
#from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI

import asyncio
load_dotenv()
embeddings = UpstageEmbeddings(model="solar-embedding-1-large")
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Chroma 데이터베이스 초기화 (앱 시작 시 한 번만 실행)
database = Chroma(
    collection_name='chroma-dongguk',
    persist_directory="./chroma",
    embedding_function=embeddings,
)

# 프롬프트 정의
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
    You are an aiassistant who answers questions related to school life of Dongguk University students.
    Use the following pieces of retrieved context to answer the question. 
    Please answer in the questioning language. For example, if the Question is in English, answer in English, and answer in Chinese
    Please present the title of file from the file_path and page of the document you referenced in the following format when answering.
    If a user's question varies depending on various situations or environments, encourages the user to ask more specific questions, please.
    You should never answer inaccurate or incorrect content. If you can't answer the content, don't provide a page. let's think step by step
    
    # format : 이 답변은 ??? 의 ??? 페이지를 참고해 작성되었습니다.

    Retrieved Context: {context}

    Question: {question}

    Answer:
    """
)

qa_chain = RetrievalQA.from_chain_type(
    llm, retriever=database.as_retriever(),
    chain_type_kwargs={"prompt": prompt}
)

# pdf 로드
def process_documents(docs,file_name:str):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    split_documents = text_splitter.split_documents(docs)
    #print(split_documents)

    database.add_documents(split_documents)
    
    return  f"Document '{file_name}'가 잘 저장되었습니다."

async def query_qa_system(query: str):
    #await asyncio.sleep(10)
    response = await asyncio.to_thread(qa_chain.invoke, {"query": query})
    return response['result']

