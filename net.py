import time

import network
import ntptime


def wifi_connect(ssid: str, password: str, timeout: int = 5):
    """只支持 2.4Ghz wifi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(ssid, password)  # WIFI名字密码
        i = 1
        while not wlan.isconnected() or i < timeout:
            i += 1
            time.sleep(1)
    print('network config: ', wlan.ifconfig()[0], "status:", wlan.isconnected())
    return wlan


def ntp_sync(server: str = None):
    ntptime.host = server or 'time.windows.com'
    ntptime.settime()
    print('Time synced ok:', time.gmtime())
