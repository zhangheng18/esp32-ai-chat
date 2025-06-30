import time
import network
import ntptime
import logging
import gc
from config import WIFI_SSID, WIFI_PASS, NTP_SERVER


class NetworkManager:
    """网络管理器"""
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.is_connected = False
    
    def connect(self, ssid=None, password=None, timeout=10):
        """连接WiFi"""
        ssid = ssid or WIFI_SSID
        password = password or WIFI_PASS
        
        self.wlan.active(True)
        time.sleep(1)
        
        if not self.wlan.isconnected():
            logging.info('正在连接到 {}...'.format(ssid))
            self.wlan.connect(ssid, password)
            
            # 等待连接
            start_time = time.time()
            while not self.wlan.isconnected():
                if time.time() - start_time > timeout:
                    logging.error('连接 {} 超时'.format(ssid))
                    return False
                time.sleep(0.5)
        
        self.is_connected = True
        ip = self.wlan.ifconfig()[0]
        logging.info('WiFi已连接: {}'.format(ip))
        return True
    
    def disconnect(self):
        """断开WiFi连接"""
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self.wlan.active(False)
        self.is_connected = False
        logging.info('WiFi已断开')
    
    def scan(self):
        """扫描可用的WiFi网络"""
        self.wlan.active(True)
        time.sleep(1)
        
        networks = self.wlan.scan()
        # 按信号强度排序
        networks.sort(key=lambda x: x[3], reverse=True)
        
        result = []
        for ssid, bssid, channel, rssi, authmode, hidden in networks:
            result.append({
                'ssid': ssid.decode('utf-8'),
                'rssi': rssi,
                'channel': channel,
                'authmode': authmode,
                'hidden': hidden
            })
            logging.info('发现网络: {} ({} dBm)'.format(ssid.decode("utf-8"), rssi))
        
        return result
    
    def sync_time(self, server=None):
        """同步NTP时间"""
        if not self.is_connected:
            logging.error('未连接到网络，无法同步时间')
            return False
        
        try:
            ntptime.host = server or NTP_SERVER
            ntptime.settime()
            logging.info('时间同步成功: {}'.format(time.gmtime()))
            return True
        except Exception as e:
            logging.error('时间同步失败: {}'.format(e))
            return False
    
    def get_status(self):
        """获取网络状态"""
        if self.wlan.isconnected():
            config = self.wlan.ifconfig()
            return {
                'connected': True,
                'ip': config[0],
                'netmask': config[1],
                'gateway': config[2],
                'dns': config[3],
                'rssi': self.wlan.status('rssi') if hasattr(self.wlan, 'status') else None
            }
        else:
            return {'connected': False}
    
    def __del__(self):
        """清理资源"""
        self.disconnect()
        gc.collect()


# 模块级单例实例
network_manager = NetworkManager() 


# 测试代码
if __name__ == "__main__":
    import time
    
    print("=== 网络服务测试 ===")
    
    try:
        net = network_manager
        
        # 测试1：扫描WiFi
        print("\n1. 扫描WiFi网络...")
        networks = net.scan()
        print("发现 {} 个网络:".format(len(networks)))
        for i, wifi_net in enumerate(networks[:5]):  # 只显示前5个
            print("  {}. {} ({}dBm)".format(i+1, wifi_net['ssid'], wifi_net['rssi']))
        
        # 测试2：连接状态
        print("\n2. 检查连接状态...")
        status = net.get_status()
        if status['connected']:
            print("已连接到网络:")
            print("  IP地址: {}".format(status['ip']))
            print("  网关: {}".format(status['gateway']))
            print("  DNS: {}".format(status['dns']))
        else:
            print("未连接到网络")
            
            # 尝试连接
            print("\n3. 尝试连接WiFi...")
            if net.connect():
                print("连接成功!")
                status = net.get_status()
                print("  IP地址: {}".format(status['ip']))
            else:
                print("连接失败!")
        
        # 测试3：时间同步
        if net.is_connected:
            print("\n4. 测试NTP时间同步...")
            print("同步前时间: {}".format(time.gmtime()))
            
            if net.sync_time():
                print("时间同步成功!")
                print("同步后时间: {}".format(time.gmtime()))
            else:
                print("时间同步失败!")
        
        # 测试4：断开连接
        print("\n5. 测试断开连接...")
        net.disconnect()
        print("已断开网络连接")
        
        # 测试5：重新连接
        print("\n6. 测试重新连接...")
        if net.connect(timeout=5):
            print("重新连接成功!")
        else:
            print("重新连接失败!")
        
        print("\n网络服务测试完成")
        
    except Exception as e:
        print("网络服务测试失败: {}".format(e))
        import sys
        sys.print_exception(e) 