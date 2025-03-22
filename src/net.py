import time

import network
import ntptime
import logging

wlan = network.WLAN(network.STA_IF)

def wifi_connect(ssid: str, password: str, timeout: int = 5):
    """只支持 2.4Ghz wifi"""
    wlan.active(True)
    time.sleep(1)
    if not wlan.isconnected():
        logging.info('connecting to network...')
        wlan.connect(ssid, password)  # WIFI名字密码
        i = 1
        while not wlan.isconnected() or i < timeout:
            i += 1
            time.sleep(1)
    logging.info(
        'network config: {} status:{}'.format(wlan.ifconfig()[0], wlan.isconnected())
    )
    return wlan


def wifi_scan():
    wlan.active(True)
    time.sleep(1)
    networks = wlan.scan()
    # 按信号强度排序
    networks.sort(key=lambda x: x[3], reverse=True)
    for ssid, bssid, channel, rssi, authmode, hidden in networks:
        logging.info('ssid:{} rssi:{} db'.format(ssid, rssi))


def ntp_sync(server: str = None):
    ntptime.host = server or 'time.windows.com'
    ntptime.settime()
    logging.info('Time synced ok:{}'.format(time.gmtime()))


if __name__ == '__main__':
    wifi_scan()
