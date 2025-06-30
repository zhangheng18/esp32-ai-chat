import logging
import gc
from base64 import b64decode, b64encode
from config import XF_APPID, XF_APIKey, XF_APISecret, TTS_CONFIG
from services.websocket_base import WebSocketBase
from hardware import audio_output
from utils import timeit


class TextToSpeech(WebSocketBase):
    """文字转语音服务"""
    
    def __init__(self):
        super().__init__(XF_APPID, XF_APIKey, XF_APISecret)
        self.audio_output = audio_output
        self.tts_config = TTS_CONFIG.copy()
        
    def create_tts_url(self):
        """创建TTS URL"""
        return self.create_url('ws-api.xfyun.cn', '/v2/tts')
    
    @timeit
    def synthesize(self, text):
        """合成语音并播放"""
        if not text:
            logging.warning("TTS: 空文本")
            return False
        
        url = self.create_tts_url()
        
        if not self.connect(url):
            return False
        
        try:
            # 发送文本
            self._send_text(text)
            
            # 接收并播放音频
            success = self._receive_and_play_audio()
            return success
            
        except Exception as e:
            logging.error("TTS错误: {}".format(e))
            return False
        finally:
            self.close()
            gc.collect()
    
    def _send_text(self, text):
        """发送要合成的文本"""
        # 构建请求数据
        data = {
            "common": {"app_id": self.app_id},
            "business": {
                "aue": "raw",
                "auf": "audio/L16;rate=16000",
                "vcn": self.tts_config.get("voice", "xiaoyan"),
                "speed": self.tts_config.get("speed", 50),
                "volume": self.tts_config.get("volume", 50),
                "pitch": self.tts_config.get("pitch", 50),
                "tte": "UTF8",
            },
            "data": {
                "text": str(b64encode(text.encode('utf-8')), 'utf-8'),
                "status": 2  # 一次性发送
            }
        }
        
        self.send_json(data)
        logging.info("TTS: 发送文本 '{}'".format(text))
    
    def _receive_and_play_audio(self):
        """接收并播放音频数据"""
        audio_buffer = bytearray()
        total_received = 0
        
        while True:
            msg = self.receive_json()
            if not msg:
                break
            
            # 检查错误
            code = msg.get("code", -1)
            if code != 0:
                logging.error("TTS错误: {}".format(msg.get('message', 'Unknown error')))
                return False
            
            # 提取音频数据
            audio_data = msg.get("data", {}).get("audio")
            if audio_data:
                # 解码音频
                decoded = b64decode(audio_data)
                audio_buffer.extend(decoded)
                total_received += len(decoded)
                
                # 当缓冲区足够大时播放
                if len(audio_buffer) >= 3200:
                    self._play_buffer(audio_buffer)
                    audio_buffer = bytearray()
            
            # 检查是否结束
            if msg.get("data", {}).get("status") == 2:
                break
        
        # 播放剩余数据
        if audio_buffer:
            self._play_buffer(audio_buffer)
        
        logging.info("TTS: 播放完成，共 {} 字节".format(total_received))
        return True
    
    def _play_buffer(self, buffer):
        """播放音频缓冲区"""
        try:
            self.audio_output.write(buffer)
        except Exception as e:
            logging.error("音频播放错误: {}".format(e))
    
    def set_voice(self, voice):
        """设置语音"""
        self.tts_config["voice"] = voice
    
    def set_speed(self, speed):
        """设置语速 (0-100)"""
        if 0 <= speed <= 100:
            self.tts_config["speed"] = speed
    
    def set_volume(self, volume):
        """设置音量 (0-100)"""
        if 0 <= volume <= 100:
            self.tts_config["volume"] = volume
    
    def set_pitch(self, pitch):
        """设置音调 (0-100)"""
        if 0 <= pitch <= 100:
            self.tts_config["pitch"] = pitch


# 模块级单例实例
text_to_speech = TextToSpeech() 


# 测试代码
if __name__ == "__main__":
    import time
    import gc
    
    print("=== 文字转语音服务测试 ===")
    
    try:
        # 确保已连接网络
        from services.network import network_manager
        network = network_manager
        if not network.is_connected:
            print("正在连接网络...")
            if not network.connect():
                print("网络连接失败，无法测试TTS服务")
                exit()
        
        tts = text_to_speech
        
        # 测试1：基础合成测试
        print("\n1. 基础语音合成测试")
        test_texts = [
            "你好，我是AI助手",
            "今天天气真不错",
            "1234567890",
            "Hello World",
        ]
        
        for text in test_texts:
            print("\n合成文本: '{}'".format(text))
            start_time = time.ticks_ms()
            
            success = tts.synthesize(text)
            
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            if success:
                print("合成成功，耗时: {}ms".format(elapsed))
            else:
                print("合成失败")
            
            time.sleep(1)
        
        # 测试2：语音参数测试
        print("\n2. 语音参数测试")
        test_text = "测试不同的语音参数"
        
        # 测试语速
        print("\n测试语速变化...")
        for speed in [30, 50, 70]:
            print("语速: {}".format(speed))
            tts.set_speed(speed)
            tts.synthesize(test_text)
            time.sleep(1)
        
        # 恢复默认语速
        tts.set_speed(50)
        
        # 测试音量
        print("\n测试音量变化...")
        for volume in [30, 50, 80]:
            print("音量: {}".format(volume))
            tts.set_volume(volume)
            tts.synthesize("音量{}".format(volume))
            time.sleep(1)
        
        # 恢复默认音量
        tts.set_volume(50)
        
        # 测试3：错误处理测试
        print("\n3. 错误处理测试")
        
        # 测试空文本
        print("测试空文本...")
        success = tts.synthesize("")
        print("空文本结果: {}".format(success))
        
        # 测试超长文本
        print("测试长文本...")
        long_text = "这是一段很长的测试文本。" * 10
        success = tts.synthesize(long_text[:100])  # 只取前100字符
        print("长文本结果: {}".format(success))
        
        # 测试4：WebSocket连接测试
        print("\n4. WebSocket连接测试")
        print("测试创建URL...")
        
        url = tts.create_tts_url()
        print("URL创建成功: {}...".format(url[:50]))
        
        print("测试连接...")
        if tts.connect(url):
            print("连接成功")
            tts.close()
        else:
            print("连接失败")
        
        # 测试5：内存管理测试
        print("\n5. 内存管理测试")
        print("合成前内存: {} KB".format(gc.mem_free() // 1024))
        
        tts.synthesize("内存测试")
        
        gc.collect()
        print("合成后内存: {} KB".format(gc.mem_free() // 1024))
        
        print("\n文字转语音服务测试完成")
        
    except Exception as e:
        print("文字转语音服务测试失败: {}".format(e))
        import sys
        sys.print_exception(e)
    finally:
        gc.collect() 