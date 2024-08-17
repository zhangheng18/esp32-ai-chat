"""
   星火认知大模型HTTP调用文档 https://www.xfyun.cn/doc/spark/HTTP%E8%B0%83%E7%94%A8%E6%96%87%E6%A1%A3.html
   Spark Lite支持[搜索]内置插件； Spark Pro, Spark Max和Spark 4.0Ultra支持[搜索]、[天气]、[日期]、[诗词]、[字词]、[股票]六个内置插件；

"""

import json

import requests

import config as cfg
import logging
from utils import timeit

header = {
    "Authorization": f"Bearer {cfg.XF_APIKey}:{cfg.XF_APISecret}",
    "Content-Type": "application/json",
}
url = "https://spark-api-open.xf-yun.com/v1/chat/completions"
payload = {
    "model": cfg.XF_AI,  # 指定请求的模型
    "messages": [
        {
            "role": "system",
            "content": "你是一个智能助手,请用最简洁的语言回答我",
        },
        {"role": "user", "content": ""},
    ],
    "stream": False,
}


@timeit
def chat(msg: str) -> str:
    payload['messages'][1]['content'] = msg
    pay = json.dumps(payload).encode('utf-8')
    response = requests.post(url, headers=header, data=pay, stream=False)
    response.encoding = 'utf-8'
    res = json.loads(response.text)
    return res["choices"][0]['message']['content']


if __name__ == "__main__":
    logging.info(chat("你可以做什么？"))
