import gc
import logging

from machine import Timer, Pin

import xunfei_ai
import xunfei_iat
import xunfei_tts
from config import (
    audio_input,
    audio_out,
    XF_APIKey,
    XF_APISecret,
    XF_APPID,
    BTN_PIN,
    ed,
)
from display import display_time, display_img, display_th
from net import ntp_sync

# 全局变量
tim_ntp = Timer(0)
tim_tm = Timer(1)
tim_show = True

tts_param = xunfei_tts.Ws_Param(XF_APPID, XF_APIKey, XF_APISecret)
iat_param = xunfei_iat.Ws_Param(XF_APPID, XF_APIKey, XF_APISecret)


def run_ai():
    global tim_tm, tts_param, iat_param, time_show

    tim_show = False

    ed.fill(0xFFFF)
    ed.show()

    ws_iat_url = iat_param.create_url()
    ws_tts_url = tts_param.create_url()

    try:
        ws_iat_ws = xunfei_iat.WebSocketClient(ws_iat_url, iat_param, audio_input)
        ed.text("q: ...", 0, 0)

        qa = ws_iat_ws.run()
        logging.info("run_ai qa:{}".format(qa))
        ed.text("q: {}".format(qa), 0, 0)

        ans = xunfei_ai.chat(qa) if qa else "我没听清，请再说一次"
        logging.debug("run_ai ans:{}".format(ans))
        ed.text("q: {}\na: {}".format(qa, ans), 0, 0)
        tts_ws = xunfei_tts.WebSocketClient(ws_tts_url, tts_param, ans, audio_out)
        tts_ws.run()
    except Exception as e:
        logging.error("run_ai error: {}".format(e))
    finally:
        gc.collect()

    ed.fill(0xFFFF)
    display_img()
    tim_show = True


def display_info():
    if tim_show:
        display_time()
        display_th()


def main():
    ed.fill(0xFFFF)
    ed.show()
    BTN_PIN.irq(trigger=Pin.IRQ_FALLING, handler=lambda t: run_ai())

    display_img()
    tim_tm.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: display_info())
    tim_ntp.init(period=1000 * 60, mode=Timer.PERIODIC, callback=lambda t: ntp_sync())


if __name__ == "__main__":
    main()
