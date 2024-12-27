from pathlib import Path
import openai
import os
import KEYS
import random
# client = OpenAI()
# setting up the openai api key
openai.api_key = KEYS.OPENAI_KEY

voice_list = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']

def openai_tts(speech_text, prefix=None, voice='alloy'):
    if voice == 'random':
        voice = random.choice(voice_list)
    if prefix:
        save_name = f'{prefix}_{voice}.mp3'
    else:
        save_name = f'{voice}.mp3'
    save_path = f'test_speech_results/{save_name}'
    # headers = {
    #     "Content-Type": "application/json",
    #     "Authorization": f'Bearer {KEYS.OPENAI_KEY}'
    # }
    # payload = {
    #     "model": 'tts-1', 
        
    # }
    with openai.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=voice,
        input=speech_text
    ) as response:
        response.stream_to_file(save_path)
        # print(f"Saved to {save_path}")
    return save_path
    


# openai_tts(text_text['Description'], voice='alloy')
# openai_tts(text_text['IsArt'], prefix='IsArt', voice='alloy')
# openai_tts(text_text['NotArt'], prefix='NotArt', voice='alloy')

if __name__ == "__main__":

    text_text = {
        'Description': '這是一碗看起來美味的料理，裡面有米飯、肉片和洋蔥，還有一些海苔絲作為裝飾。碗是一次性的紙碗，上面放著一把白色的湯匙，方便食用。整體的顏色呈現出金黃與褐色的調和，十分誘人，似乎是日式的肉燥飯或類似的飯類料理。', 
        'IsArt': '這件藝術品的名稱是《無形的滋味》。作品理念探討了食物與文化之間的關係，以及日常生活中看似平凡的食物如何承載著深厚的情感與記憶。透過一碗簡單的料理，藝術家表達了飲食的多樣性與共鳴，反映了人類的存在與傳承。將觀者帶入一個充滿味道的時空，促使人們重新思考與食物的連結，並珍惜每一口的滋味。', 
        'NotArt': '這張照片中的食物是一碗牛肉飯，主要是呈現一種日常飲食的場景，缺乏藝術構圖或創意表現。不具備藝術作品所需的情感深度、主題探討或美學意義。因此，這僅是生活中的一個瞬間，而非藝術創作。'
    }
    openai_tts(text_text['Description'], voice='echo')
    openai_tts(text_text['Description'], voice='fable')
    openai_tts(text_text['Description'], voice='onyx')
    openai_tts(text_text['Description'], voice='nova')
    openai_tts(text_text['Description'], voice='shimmer')