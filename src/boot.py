import esp
import micropython
import logging
from config import WIFI_SSID, WIFI_PASS
import net

# esp.osdebug(0)  # redirect vendor O/S debugging messages to UART(0)

micropython.alloc_emergency_exception_buf(128)

logging.info("rom:{}".format(esp.flash_size()))
logging.info(micropython.mem_info())


wifi = net.wifi_connect(WIFI_SSID, WIFI_PASS)
if wifi.isconnected():
    net.ntp_sync()
else:
    logging.error("wifi connect {} failed".format(WIFI_SSID))
