# ESP32 AI聊天项目配置文件
import logging

# =============================================================================
# 基础配置
# =============================================================================

# 调试模式
DEBUG = True

# 日志配置
logging.basicConfig(
    level=logging.INFO, 
    format="[%(asctime)s] [%(levelname)s]:%(message)s"
)

# 时区配置（北京时间 UTC+8）
TIMEZONE_OFFSET = 8 * 3600

# =============================================================================
# 网络配置
# =============================================================================

# WiFi配置
WIFI_SSID = ""
WIFI_PASS = ""

# NTP服务器
NTP_SERVER = 'time.windows.com'

# =============================================================================
# 硬件引脚配置
# =============================================================================

# 麦克风引脚
MIC_SD_PIN = 39
MIC_SCK_PIN = 40
MIC_WS_PIN = 41

# 扬声器引脚
SPEAKER_BCLK_PIN = 18
SPEAKER_LRC_PIN = 17
SPEAKER_DIN_PIN = 16

# 显示屏引脚
DISPLAY_SCK_PIN = 12
DISPLAY_MOSI_PIN = 11
DISPLAY_CS_PIN = 10
DISPLAY_DC_PIN = 13
DISPLAY_RST_PIN = 14
DISPLAY_BL_PIN = 9

# 按钮引脚
BUTTON_PIN = 1

# DHT20引脚（可选）
DHT_SDA_PIN = 4
DHT_SCL_PIN = 5

# I2S配置
I2S_CONFIG = {
    "bits": 16,
    "format": "MONO",
    "rate": 16000,
    "ibuf": 16000,
}

# 显示屏配置
DISPLAY_CONFIG = {
    "width": 240,
    "height": 320,
    "rotate": 1,
    "invert": True,
    "rgb": False,
}

# =============================================================================
# 讯飞API配置
# =============================================================================

# 讯飞API配置
XF_APPID = ""
XF_APISecret = ""
XF_APIKey = ""

# AI模型版本
# general指向Lite版本;
# generalv2指向V2.0版本;
# generalv3指向Pro版本;
# pro-128k指向Pro-128K版本;
# generalv3.5指向Max版本;
# 4.0Ultra指向4.0 Ultra版本;
XF_AI_MODEL = "generalv3"

# 语音识别配置
IAT_CONFIG = {
    "domain": "iat",
    "language": "zh_cn",
    "accent": "mandarin",
    "vinfo": 0,
    "vad_eos": 2000,
    "nbest": 1,
    "wbest": 1,
}

# TTS配置
TTS_CONFIG = {
    "voice": "xiaoyan",
    "speed": 50,
    "volume": 10,
    "pitch": 50,
} 