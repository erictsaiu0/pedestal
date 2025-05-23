import base64
import cv2
import numpy as np
from openai import OpenAI
import KEYS
import requests
import json
from utils import log_and_print
import logging

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
        log_and_print(f'In gpt_utils.py, call_api function, response: {res}', 'DEBUG')
        quit()
    return res['choices'][0]['message']['content']

def describe_iamge(image_base64:str, text_num:int=50):
    instruct = f"請想像你是直接看見，並以{str(text_num)}字繁體中文描述這個物品。最後加上英文翻譯。"
    result = call_api(image_base64, instruct)
    return result

def is_art(image_base64:str, text_num:int=100):
    reference = "介紹時請參考（但不一定要提及）以下關鍵字：觀念藝術、 現成物、雕塑、藝術品、勞動、存在主義、解構主義。可參考（但不一定要提及）當代藝術家如杜象、波伊斯等的作品創作理念。"
    instruct = f"你是一個這個藝術品的作者，請想像你是直接看見這個放在展台上的藝術品，首先先介紹它的藝術作品名，並以{str(text_num)}字繁體中文向10歲小孩介紹這個作品。接著說說這個作品背後的故事。最後做一個簡單的英文總結。"
    result = call_api(image_base64, instruct)
    return result

def not_art(image_base64:str, text_num:int=100):
    reference = "介紹時請參考（但不一定要提及）以下關鍵字：觀念藝術、 現成物、雕塑、藝術品、勞動、存在主義、解構主義。可參考（但不一定要提及）當代藝術家如杜象、波伊斯等的作品創作理念。"
    instruct = f"請想像你是直接看見，請以{str(text_num)}字以內的繁體中文告訴我為何這個這個放在展台上的東西不是一個藝術作品。{reference}最後加上英文翻譯。"
    result = call_api(image_base64, instruct)
    return result

if __name__ == "__main__":
    # logname = 'log_gpt_utils'
    # logging.basicConfig(
    #     filename=f'{logname}.log',
    #     filemode='a',
    #     format='%(asctime)s\t %(levelname)s\t %(message)s',
    #     datefmt='%H:%M:%S',
    #     level=logging.DEBUG
    # )

    img_path = 'example_img/作品｜展台｜AI練習圖片_4.png'
    img = cv2.imread(img_path)
    img = imageResize(img_path, 0.5)
    img_base64 = image2base64(img)
    # describe = describe_iamge(img_base64)
    isart = is_art(img_base64)
    # notart = not_art(img_base64)
    # print(f"Description: {describe}")
    print(f"Is art: {isart}")
    # print(f"Not art: {notart}")
