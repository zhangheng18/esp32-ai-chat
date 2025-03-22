"""
语音听写（流式版）WebAPI 文档 yhttps://www.xfyun.cn/doc/asr/voicedictation/API.html
"""

import hashlib
import hmac
import json
import logging
import time
from base64 import b64encode

import ws.client

from config import XF_APPID, XF_APIKey, XF_APISecret, audio_input
from utils import urlencode, format_date_time, timeit

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

COMMON_ARGS = {"app_id": XF_APPID}
BusinessArgs = {
    "domain": "iat",
    "language": "zh_cn",
    "accent": "mandarin",
    "vinfo": 0,
    "vad_eos": 2000,
    "nbest": 1,
    "wbest": 1,
}


class Ws_Param:
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret

        self.CommonArgs = COMMON_ARGS
        self.BusinessArgs = BusinessArgs

    def create_url(self):
        url = 'ws://ws-api.xfyun.cn/v2/iat'
        date = format_date_time(time.time())

        signature_origin = "host: ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
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


@micropython.native
def calculate_rms(buffer: bytearray, length: int) -> int:
    sum = 0
    for i in range(0, length, 2):
        sample = int((buffer[i + 1] << 8) | buffer[i])
        if sample >= 32768:
            sample -= 65536
        sum += sample * sample
    return int((sum / (length // 2)) ** 0.5)


class WebSocketClient:
    def __init__(self, url, wsParam, audio_input):
        self.url = url
        self.wsParam = wsParam
        self.ws = None
        self.audio_input = audio_input

    def connect(self):
        self.ws = ws.client.connect(self.url)
        self.ws.settimeout(3)
        logging.info("connect to:%s" % (self.url))

    @timeit
    def on_message(self, message):
        result = ""
        try:
            msg = json.loads(message)
            code = msg["code"]
            sid = msg["sid"]
            errMsg = msg["message"]
            if code != 0:
                logging.error(
                    "on_message sid:%s call error:%s code is:%s" % (sid, errMsg, code)
                )
            else:
                data = msg["data"]["result"]["ws"]
                for i in data:
                    for w in i["cw"]:
                        result += w["w"]
                logging.info(
                    "on_messagesid:%s call error:%s code is:%s ,%s"
                    % (sid, errMsg, code, msg)
                )
        except Exception as e:
            logging.error("on_message parse err:%s" % (e))
        return result

    def receive_messages(self):
        msg = ""
        while True:
            try:
                message = self.ws.recv()
                t = self.on_message(message)
                if not t:
                    break
                msg += t
            except Exception as e:
                logging.error("ERROR:%s" % (e))
                break
        logging.info(f"receive_messages stop, {msg}")
        return msg

    def read(self, chunk: bytearray):
        data_len = self.audio_input.readinto(chunk)
        rms = calculate_rms(chunk, data_len)
        return rms, chunk[:data_len]

    def audio_generator(
        self, chunk: bytearray, low_noise: int = 10, max_noise: int = 800
    ):
        while True:
            rms, audio = self.read(chunk)
            if low_noise <= rms <= max_noise:
                yield audio, rms
            else:
                yield None, rms

    def run(self):
        msg = ""
        try:
            self.connect()
            logging.info("run start ....")
            chunk = bytearray(3200)
            status = STATUS_FIRST_FRAME

            # 静默检测参数
            silence_count = 0
            max_silence_count = 10  # 约1秒
            min_speech_count = 3  # 至少检测到3帧有效语音才开始处理
            speech_count = 0
            is_recording = False

            # 自适应噪音阈值
            noise_floor = None
            noise_adapt_rate = 0.95
            speech_threshold_factor = 2.0  # 信噪比阈值因子

            for audio, rms in self.audio_generator(chunk, low_noise=0, max_noise=10000):
                # 初始化或更新噪音基准
                if noise_floor is None:
                    noise_floor = rms
                elif rms < noise_floor * 1.5:  # 只用较低的RMS值更新噪音基准
                    noise_floor = noise_floor * noise_adapt_rate + rms * (
                        1 - noise_adapt_rate
                    )

                # 判断是否为语音
                is_speech = (
                    rms > noise_floor * speech_threshold_factor and rms > 8
                )
                logging.debug(
                    f'RMS: {rms}, 噪音基准: {noise_floor:.1f}, 是语音: {is_speech}'
                )

                if is_speech:
                    speech_count += 1
                    silence_count = 0

                    # 确认开始录音
                    if speech_count >= min_speech_count:
                        is_recording = True
                else:
                    silence_count += 1
                    speech_count = 0

                    # 如果已经开始录音，且静默足够长，则结束
                    if is_recording and silence_count >= max_silence_count:
                        logging.info(f'检测到持续静默{silence_count}帧，停止录音')
                        break

                # 如果未检测到语音或未开始录音，跳过处理
                if not is_speech or not is_recording:
                    continue

                # 处理有效音频帧
                if status == STATUS_FIRST_FRAME:
                    # 第一帧处理代码
                    # 发送第一帧音频，带business 参数
                    # appid 必须带上，只需第一帧发送
                    d = {
                        "common": self.wsParam.CommonArgs,
                        "business": self.wsParam.BusinessArgs,
                        "data": {
                            "status": status,
                            "format": "audio/L16;rate=16000",
                            "audio": str(b64encode(audio), 'utf-8'),
                            "encoding": "raw",
                        },
                    }
                    status = STATUS_CONTINUE_FRAME
                else:
                    # 中间帧处理
                    d = {
                        "data": {
                            "status": STATUS_CONTINUE_FRAME,
                            "format": "audio/L16;rate=16000",
                            "audio": str(b64encode(audio), 'utf-8'),
                            "encoding": "raw",
                        }
                    }
                logging.info(
                    f'send :{len(d["data"]["audio"])} rms:{rms} status:{d["data"]["status"]}'
                )
                d = json.dumps(d)
                self.ws.send(d)
            if status == STATUS_CONTINUE_FRAME:
                # 最后一帧处理
                rms, audio = self.read(chunk)
                if not audio:
                    audio = bytearray(0x00)
                status = STATUS_LAST_FRAME
                d = {
                    "data": {
                        "status": status,
                        "format": "audio/L16;rate=16000",
                        "audio": str(b64encode(audio), 'utf-8'),
                        "encoding": "raw",
                    }
                }
                logging.info(f'send :{len(d)} rms:{rms} status:{status}')
                d = json.dumps(d)
                self.ws.send(d)
                # 接收消息
                msg = self.receive_messages()
        except Exception as e:
            logging.error("run error:%s" % (e))
        finally:
            if self.ws:
                self.ws.close()
            return msg


if __name__ == "__main__":
    param = Ws_Param(XF_APPID, XF_APIKey, XF_APISecret)
    ws_url = param.create_url()
    client = WebSocketClient(ws_url, param, audio_input)
    print(client.run())
