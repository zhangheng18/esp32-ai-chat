"""
语音合成（流式版）WebAPI 文档 https://www.xfyun.cn/doc/tts/online_tts/API.html
"""

import hashlib
import hmac
import json
import logging
import time
from base64 import b64decode, b64encode

import ws.client

from config import XF_APPID, XF_APIKey, XF_APISecret, audio_out
from utils import urlencode, format_date_time, timeit

COMMON_ARGS = {"app_id": XF_APPID}
BusinessArgs = {
    "aue": "raw",
    "auf": "audio/L16;rate=16000",
    "vcn": "xiaoyan",
    "tte": "utf8",
    "volume": 8,
    "speed": 60,
}


class Ws_Param:
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.CommonArgs = COMMON_ARGS
        self.BusinessArgs = BusinessArgs

    def create_url(self):
        url = 'ws://tts-api.xfyun.cn/v2/tts'
        date = format_date_time(time.time())

        signature_origin = "host: ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        signature_sha = hmac.new(
            self.APISecret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            hashlib.sha256,
        ).digest()
        signature = b64encode(signature_sha).decode('utf-8')

        authorization_origin = (
            'api_key="%s", algorithm="hmac-sha256", headers="host date request-line", signature="%s"'
            % (self.APIKey, signature)
        )
        authorization = b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        headers = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn",
        }
        return url + '?' + urlencode(headers)

    def mk_text(self, text):
        # 语音合成接口最后文字容易丢失，加。保持文字 完整转化
        # text += '。'
        return {
            "status": 2,
            "text": str(b64encode(text.encode('utf-8')), "UTF8"),
        }


class WebSocketClient:
    def __init__(self, url, wsParam, text, audio_out):
        self.url = url
        self.wsParam = wsParam
        self.ws = None
        self.text = text
        self.audio_out = audio_out

    def connect(self):
        self.ws = ws.client.connect(self.url)
        self.ws.settimeout(5)
        logging.info("connect:{}".format(self.url))

    def send_text(self):
        logging.info("send_text ------>:%s" % (self.text))
        d = {
            "common": self.wsParam.CommonArgs,
            "business": self.wsParam.BusinessArgs,
            "data": self.wsParam.mk_text(self.text),
        }
        self.ws.send(json.dumps(d))

    @timeit
    def on_message(self, msg):
        if not msg:
            return False

        message = json.loads(msg)
        code = message["code"]
        sid = message["sid"]
        audio = b64decode(message["data"]["audio"])
        status = message["data"]["status"]
        errMsg = message["message"]

        if code != 0:
            logging.error(
                "on_message:sid:%s call error:%s code is:%s  len:%s"
                % (sid, errMsg, code)
            )
        else:
            logging.info(
                "on_message: sid:%s call error:%s code is:%s %s"
                % (sid, errMsg, code, len(audio))
            )
            # with open('demo.pcm', 'ab') as f:
            #   f.write(audio)
            self.audio_out.write(audio)
        return True

    def receive_messages(self):
        while True:
            try:
                message = self.ws.recv()
                if not self.on_message(message):
                    break
            except Exception as e:
                logging.error("receive_messages:%s" % (e))
                break

    def run(self):
        try:
            self.connect()
            self.send_text()
            self.receive_messages()
        except Exception as e:
            logging.error("run:%s" % (e))
        finally:
            if self.ws:
                self.ws.close()


if __name__ == "__main__":
    param = Ws_Param(XF_APPID, XF_APIKey, XF_APISecret)
    ws_url = param.create_url()
    text = "我可以帮助您解答各种问题，例如：提供实时天气信息和预报。回答有关历史、科学、文化、技术等方面的问题。提供新闻和时事评论。帮助您查找附近的餐厅、商店和其他地点。提醒您即将到来的日程安排和事件。播放音乐、电影和电视节目。与您进行闲聊，提供娱乐和轻松的氛围。提供有关健康、锻炼和饮食的建议。帮助您学习新技能和提高现有技能。提供有关旅行目的地的信息和建议。请注意，我的功能可能因设备和应用程序的不同而有所不同。"
    client = WebSocketClient(ws_url, param, text=text, audio_out=audio_out)
    client.run()
    print('done')
