import hashlib
import hmac
import json
import logging
import time
import gc
from base64 import b64encode
import ws.client
from utils import urlencode, format_date_time


class WebSocketBase:
    """WebSocket基础类"""
    
    def __init__(self, app_id, api_key, api_secret):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws = None
        
    def create_url(self, host, path):
        """创建带签名的WebSocket URL"""
        date = format_date_time(time.time())
        
        # 生成签名
        signature_origin = "host: {}\n".format(host)
        signature_origin += "date: {}\n".format(date)
        signature_origin += "GET {} HTTP/1.1".format(path)
        
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            hashlib.sha256,
        ).digest()
        signature = b64encode(signature_sha).decode('utf-8')
        
        # 生成授权头
        authorization_origin = (
            'api_key="{}", algorithm="hmac-sha256", '
            'headers="host date request-line", signature="{}"'.format(
                self.api_key, signature
            )
        )
        authorization = b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        # 构造URL参数
        headers = {
            "authorization": authorization,
            "date": date,
            "host": host,
        }
        
        return "ws://{}{}?".format(host, path) + urlencode(headers)
    
    def connect(self, url, timeout=5):
        """连接WebSocket"""
        try:
            # 关闭之前的连接
            if self.ws:
                self.close()
            
            self.ws = ws.client.connect(url)
            self.ws.settimeout(timeout)
            logging.info("WebSocket连接成功: {}".format(url))
            return True
        except Exception as e:
            logging.error("WebSocket连接失败: {}".format(e))
            self.ws = None
            return False
    
    def send_json(self, data):
        """发送JSON数据"""
        if self.ws:
            try:
                json_data = json.dumps(data)
                self.ws.send(json_data)
                return True
            except Exception as e:
                logging.error("发送数据失败: {}".format(e))
                # 连接出错时关闭连接
                self.close()
                return False
        else:
            logging.error("WebSocket未连接，无法发送数据")
            return False
    
    def receive_json(self):
        """接收JSON数据"""
        if self.ws:
            try:
                message = self.ws.recv()
                if message:
                    return json.loads(message)
                else:
                    logging.warning("收到空消息，连接可能已断开")
                    return None
            except Exception as e:
                logging.error("接收数据失败: {}".format(e))
                # 连接出错时关闭连接
                self.close()
                return None
        else:
            logging.error("WebSocket未连接，无法接收数据")
            return None
    
    def close(self):
        """关闭连接"""
        if self.ws:
            try:
                self.ws.close()
                logging.info("WebSocket连接已关闭")
            except:
                pass
            finally:
                self.ws = None
        gc.collect()
    
    def __del__(self):
        """析构函数"""
        self.close() 