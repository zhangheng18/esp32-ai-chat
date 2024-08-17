import time

t = time.ticks_us()

from machine import Pin, I2S, SPI, I2C

# 控制 @timeit 是否显示函数运行时间
DEBUG = True

import logging

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s]:%(name)s:%(message)s"
)


# 讯飞API 服务
XF_APPID = ""
XF_APIKey = ""
XF_APISecret = ""

"""
general指向Lite版本;
generalv2指向V2.0版本;
generalv3指向Pro版本;
pro-128k指向Pro-128K版本;
generalv3.5指向Max版本;
4.0Ultra指向4.0 Ultra版本;
"""
XF_AI = "generalv3"


# WIFI 名称 和 密码
WIFI_SSID = ""
WIFI_PASS = ""


# 初始化麦克风
in_sd_pin = Pin(39)
in_sck_pin = Pin(40)
in_ws_pin = Pin(41)
audio_input = I2S(
    0,
    sck=in_sck_pin,
    ws=in_ws_pin,
    sd=in_sd_pin,
    mode=I2S.RX,
    bits=16,
    format=I2S.MONO,
    rate=16000,
    ibuf=16000,
)


# 初始化喇叭
bclk_pin = Pin(18)  # 串行时钟输出
lrc_pin = Pin(17)  # 字时钟
din_pin = Pin(16)  # 串行数据输出初始化i2s
audio_out = I2S(
    1,
    sck=bclk_pin,
    ws=lrc_pin,
    sd=din_pin,
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=16000,
    ibuf=16000 * 2,
)


# 配置时区偏移量（例如，北京时间偏移量为8小时）
TIMEZONE_OFFSET = 8 * 3600

# 初始化屏幕
import st7789_buf as st7789
from easydisplay import EasyDisplay

spi = SPI(1, baudrate=40000000, sck=Pin(12), mosi=Pin(11))
dp = st7789.ST7789(
    width=240,
    height=320,
    spi=spi,
    cs=10,
    dc=13,
    res=14,
    rotate=1,  # 旋转屏幕
    bl=9,  # 调节背光亮度
    invert=True,
    rgb=True,
)
dp.back_light(90)  # 设置亮度为90
ed = EasyDisplay(
    dp,
    "RGB565",
    font="font/text_lite_24px_2312.v3.bmf",
    show=True,
    color=0x0000,
    bg_color=0xFFFF,
    clear=False,
    auto_wrap=True,
)

# 初始化按钮
BTN_PIN = Pin(1, Pin.IN, Pin.PULL_UP)


# DHT20 温湿度
import dht20

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
dht = dht20.DHT20(i2c)

print('load config', time.ticks_diff(time.ticks_us(), t) / 1000, ' ms')
