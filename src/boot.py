import esp
import micropython
import logging
import gc

# 导入配置
from config import WIFI_SSID, WIFI_PASS, DEBUG


# 显示系统信息
logging.info("=" * 20)
logging.info("ESP32 AI Chat 启动中...")
logging.info("Flash大小: {} MB".format(esp.flash_size() // 1024 // 1024))
logging.info("空闲内存: {} KB".format(gc.mem_free() // 1024))
logging.info("=" * 20)

# 导入网络管理器
from services import network_manager

# 连接WiFi
if network_manager.connect(WIFI_SSID, WIFI_PASS):
    # 同步时间
    network_manager.sync_time()
else:
    logging.error("无法连接到WiFi: {}".format(WIFI_SSID))
gc.collect()
logging.info("启动完成，空闲内存: {} KB".format(gc.mem_free() // 1024))
