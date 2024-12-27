import base64
import cv2
import numpy as np
from openai import OpenAI
import KEYS
import requests
import json

def image2base64(img:np.ndarray)->str:
    _, img_encode = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(img_encode)
    return img_base64.decode()

def imageResize(img_path:str, scale_ratio:float)->np.ndarray:
    img = cv2.imread(img_path)
    img = cv2.resize(img, (int(img.shape[1]*scale_ratio), int(img.shape[0]*scale_ratio)))
    return img

def npimageResize(npimg:np.ndarray, scale_ratio:float)->np.ndarray:
    img = cv2.resize(npimg, (int(npimg.shape[1]*scale_ratio), int(npimg.shape[0]*scale_ratio)))
    return img

def call_api(image_base64:str, instruction:str):
    headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {KEYS.OPENAI_KEY}'
        }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": instruction
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    # response should be like this:
    # {'id': 'chatcmpl-A0VHAXDKnKTHq6r7AgV27Jow2IAzH', 'object': 'chat.completion', 'created': 1724683588, 'model': 'gpt-4o-mini-2024-07-18', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '作品名稱：生活的滋味\n\n這件藝術品運用日常食品作為創作主題，探索飲食文化與情感的交織。透過一碗看似平常的飯食，作品傳達了對家庭、友情與回憶的珍視。此外，藝術家意圖喚起觀者的共鳴，使人們反思在快節奏的現代生活中，飲食不僅是一種生理需求，更是一種文化交流與情感聯繫的媒介。每一口飯食皆是生活的縮影，富含深刻的意義。', 'refusal': None}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 8534, 'completion_tokens': 139, 'total_tokens': 8673}, 'system_fingerprint': 'fp_507c9469a1'}
    res = response.json()
    if 'choices' not in res:
        print(res)
        quit()
    return res['choices'][0]['message']['content']

def describe_iamge(image_base64:str, text_num:int=50):
    instruct = f"請想像你是直接看見，並以{str(text_num)}字繁體中文描述這個物品。"
    result = call_api(image_base64, instruct)
    return result

def is_art(image_base64:str, text_num:int=50):
    instruct = f"請想像你是直接看見這個藝術品，請以繁體中文介紹這個作品的名稱，並以{str(text_num)}字介紹他的作品理念。"
    result = call_api(image_base64, instruct)
    return result

def not_art(image_base64:str, text_num:int=50):
    instruct = f"請想像你是直接看見，請以{str(text_num)}字以內的繁體中文告訴我為何這個東西不是一個藝術作品。"
    result = call_api(image_base64, instruct)
    return result

def test():
    img_path = '/Users/erictsai/Desktop/anythingart/example_img/作品｜展台｜AI練習圖片_2.png'
    img = cv2.imread(img_path)
    img = imageResize(img_path, 0.5)
    img_base64 = image2base64(img)
    describe = describe_iamge(img_base64)
    isart = is_art(img_base64)
    notart = not_art(img_base64)
    print(f"Description: {describe}")
    print(f"Is art: {isart}")
    print(f"Not art: {notart}")

# test()