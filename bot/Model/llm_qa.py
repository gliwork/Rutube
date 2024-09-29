import json
import pickle
import os
from openai import OpenAI

from sentence_transformers import SentenceTransformer
import requests
import numpy as np
import faiss

os.environ['TOGETHER_API_KEY'] = '21d5552e22479067e0e6010f2a0f2a07ac777cd1fe42cb3c612f5faf97e310da'


# In[9]:


# import streamlit as st
# @st.cache_data
def load_faiss_index():
    with open('./Model/chunks_data.pickle', 'rb') as handle: #Model/
        chunks = pickle.load(handle)

    model = SentenceTransformer('BAAI/bge-m3', device="cpu")
    embeddings = np.load('./Model/embs-data.npy')#Model/

    index = faiss.IndexFlatL2(embeddings.shape[1])  # build the index
    index.add(embeddings)

    return chunks, model, index, embeddings


def get_relevant_documents(question, chunks, model, index, embeddings):
    k = 3  # NUM of retrieval candidates
    e = model.encode(question)
    dist, Idx = index.search(e.reshape(1, -1), k)
    retrievals = [chunks[i] for i in Idx.flatten()]
    return retrievals


def generate_mixtral_response(question, chunks, model, index, embeddings):
    rets = get_relevant_documents(question, chunks, model, index, embeddings)
    metadatas = [list(item.metadata.keys())[0] for item in rets]

    # Improved string formatting
    sources_text = ' \n\n '.join([f'ИСТОЧНИК {i + 1}: {ret.page_content}' for i, ret in enumerate(rets)])

    promptstring = (
        f"Вы программист, который отвечает на вопросы пользователей на темы, связанные с программированием. "
        f"Используя только информацию, содержащуюся в ИСТОЧНИКАХ после слова ТЕКСТ, "
        f"ответьте на вопрос, заданный после слова ВОПРОС. "
        f"Если в тексте нет информации, необходимой для ответа, ответьте «Недостаточно информации для ответа». "
        f"Структурируйте свой ответ и отвечайте шаг за шагом, но не упоминайте ссылки на источники в ответе."
        f"Проверьте, что ответ выводится на кириллице и на русском языке. \n"
        f"ТЕКСТ:\n{sources_text}\nВОПРОС:\n{question}"
    )

    # print(promptstring)
#    endpoint = 'https://api.together.xyz/v1/chat/completions'
#    res = requests.post(endpoint, json={
#        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
#        "max_tokens": 2048,
#        "prompt": f"[INST] {promptstring}  [/INST]",
#        "temperature": 0.4,
#        "top_p": 0.7,
#        "top_k": 5,
#        "repetition_penalty": 1,
#        "stop": [
#            "[/INST]",
#            "</s>"
#        ],
#        "repetitive_penalty": 1,
#        "update_at": "2024-02-25T16:35:32.555Z"
#    }, headers={
#        "Authorization": f"Bearer {os.environ['TOGETHER_API_KEY']}",
#    })
    # print(dict(json.loads(res.content))['usage']['total_tokens'])


# Set OpenAI's API key and API base to use vLLM's API server.
    openai_api_key = "EMPTY"
    openai_api_base = "http://localhost:8000/v1"
    
    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
    )
    
    chat_response = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        messages=[
            
            {"role": "user", "content": promptstring},
            
        ],
        max_tokens = 2048,
    )
    print("Chat response:", chat_response)




    return chat_response.choices[0].message.content, metadatas, rets#dict(json.loads(res.content)) ['message']['content'],


# prompt = ''
def respond_question(prompt):
    if prompt:
        # Check which model is selected and call the corresponding function
        chunks, model, index, embeddings = load_faiss_index()
        response, metadatas, rets = generate_mixtral_response(prompt, chunks, model, index,
                                                              embeddings)  # generate_mixtral_comment(question, answer, chunks, model, index, embeddings)#generate_mixtral_response(prompt, chunks, model, index, embeddings)
        # Process and display the response
        excerpts = '\n\n'.join([f"ИСТОЧНИК {i + 1}, {list(ret.metadata.keys())[0]}: {ret.page_content}" for i, ret in
                                enumerate(rets)]) if rets else ""
        bibliography = '\n\n'.join([f"{i + 1}. {meta}" for i, meta in enumerate(metadatas)]) if metadatas else ""
        full_response = f"{response}\n\n\n\nИСТОЧНИКИ:\n{excerpts}\n\nСПИСОК ЛИТЕРАТУРЫ:\n\n{bibliography}"
    return full_response  # f"{response}#\n\nИСТОЧНИКИ:\n{excerpts}\n\nСПИСОК ЛИТЕРАТУРЫ:\n\n{bibliography}"#full_response
