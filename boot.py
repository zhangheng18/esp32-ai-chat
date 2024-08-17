import esp
import micropython

from config import WIFI_SSID, WIFI_PASS

# esp.osdebug(0)  # redirect vendor O/S debugging messages to UART(0)

micropython.alloc_emergency_exception_buf(100)
# low level methods to interact with flash storage
print("rom:{}", esp.flash_size())
print(micropython.mem_info())


import net

wifi = net.wifi_connect(WIFI_SSID, WIFI_PASS)
if wifi.isconnected():
    net.ntp_sync()
else:
    print("wifi connect {} failed".format(WIFI_SSID))
