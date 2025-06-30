import logging
import gc
from base64 import b64encode
import micropython
from config import XF_APPID, XF_APIKey, XF_APISecret, IAT_CONFIG
from services.websocket_base import WebSocketBase
from hardware import audio_input
from utils import timeit


# 帧状态常量
STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2


class SpeechRecognition(WebSocketBase):
    """语音识别服务"""
    
    def __init__(self):
        super().__init__(XF_APPID, XF_APIKey, XF_APISecret)
        self.audio_input = audio_input
        self.iat_config = IAT_CONFIG
        
    def create_iat_url(self):
        """创建语音识别URL"""
        return self.create_url('ws-api.xfyun.cn', '/v2/iat')
    
    @timeit
    def recognize(self):
        """执行语音识别"""
        url = self.create_iat_url()
        
        if not self.connect(url):
            return ""
        
        try:
            # 执行识别
            result = self._do_recognition()
            return result
        except Exception as e:
            logging.error("语音识别错误: {}".format(e))
            return ""
        finally:
            self.close()
            gc.collect()
    
    def _do_recognition(self):
        """执行实际的语音识别流程"""
        chunk = bytearray(3200)
        status = STATUS_FIRST_FRAME
        result = ""
        frame_count = 0
        sent_frames = 0
        # 时间配置（单位：帧，每帧100ms）
        max_total_frames = 600    # 总超时时间：60秒
        max_recording_frames = 300  # 最大录音时长：30秒
        
        # 语音检测参数
        speech_detector = SpeechDetector()
        
        logging.info("开始语音检测，等待说话...")
        
        # 音频生成器
        for audio, rms, is_speech in self._audio_generator(chunk, speech_detector):
            frame_count += 1
            
            # 总时间超时保护
            if frame_count > max_total_frames:
                logging.warning("总时间超时（{}秒），停止识别".format(max_total_frames // 10))
                break
            
            # 发送音频数据
            if status == STATUS_FIRST_FRAME:
                # 快速开始策略：检测到可能的语音就立即开始
                if rms > speech_detector.min_rms or is_speech:
                    logging.info("检测到语音活动，开始识别")
                    self._send_first_frame(audio)
                    status = STATUS_CONTINUE_FRAME
                    sent_frames = 1
                elif frame_count > 30:  # 3秒内没有语音就发送第一帧保持连接
                    logging.info("超时保护，发送第一帧维持连接")
                    self._send_first_frame(audio)
                    status = STATUS_CONTINUE_FRAME
                    sent_frames = 1
            else:
                # 限制发送频率和录音时长
                if sent_frames < max_recording_frames and frame_count % 2 == 0:  # 每200ms发送一次
                    if not self._send_continue_frame(audio):
                        logging.error("发送失败，停止识别")
                        break
                    sent_frames += 1
                elif sent_frames >= max_recording_frames:
                    logging.info("达到最大录音时长（{}秒），停止识别".format(max_recording_frames // 5))
                    break
            
            # 检查是否应该停止
            if speech_detector.should_stop():
                logging.info("检测到语音结束")
                break
        
        # 发送最后一帧
        if status == STATUS_CONTINUE_FRAME:
            self._send_last_frame()
            result = self._receive_results()
            logging.info("发送了 {} 个音频帧".format(sent_frames))
        else:
            logging.warning("未检测到有效语音")
        
        return result
    
    def _audio_generator(self, chunk, detector):
        """音频数据生成器"""
        while True:
            # 读取音频
            data_len = self.audio_input.read(chunk)
            if data_len > 0:
                audio = chunk[:data_len]
                rms = self._calculate_rms(audio, data_len)
                is_speech = detector.process(rms)
                yield audio, rms, is_speech
            else:
                yield None, 0, False
    
    @micropython.native
    def _calculate_rms(self, buffer, length):
        """计算音频RMS值"""
        sum_val = 0
        for i in range(0, length, 2):
            sample = int((buffer[i + 1] << 8) | buffer[i])
            if sample >= 32768:
                sample -= 65536
            sum_val += sample * sample
        return int((sum_val / (length // 2)) ** 0.5)
    
    def _send_first_frame(self, audio):
        """发送第一帧"""
        data = {
            "common": {"app_id": self.app_id},
            "business": self.iat_config,
            "data": {
                "status": STATUS_FIRST_FRAME,
                "format": "audio/L16;rate=16000",
                "audio": str(b64encode(audio), 'utf-8'),
                "encoding": "raw",
            },
        }
        self.send_json(data)
        logging.debug("发送第一帧音频")
    
    def _send_continue_frame(self, audio):
        """发送中间帧"""
        data = {
            "data": {
                "status": STATUS_CONTINUE_FRAME,
                "format": "audio/L16;rate=16000",
                "audio": str(b64encode(audio), 'utf-8'),
                "encoding": "raw",
            }
        }
        return self.send_json(data)
    
    def _send_last_frame(self):
        """发送最后一帧"""
        data = {
            "data": {
                "status": STATUS_LAST_FRAME,
                "format": "audio/L16;rate=16000",
                "audio": "",
                "encoding": "raw",
            }
        }
        self.send_json(data)
        logging.debug("发送最后一帧")
    
    def _receive_results(self):
        """接收识别结果"""
        full_result = ""
        
        while True:
            msg = self.receive_json()
            if not msg:
                break
            
            # 解析结果
            result = self._parse_result(msg)
            if result:
                full_result += result
            
            # 检查是否结束
            if msg.get("data", {}).get("status") == 2:
                break
        
        logging.info("识别结果: {}".format(full_result))
        return full_result
    
    def _parse_result(self, msg):
        """解析单条消息结果"""
        try:
            code = msg.get("code", -1)
            if code != 0:
                logging.error("识别错误: {}".format(msg.get('message', 'Unknown error')))
                return ""
            
            # 提取文本
            result = ""
            data = msg.get("data", {}).get("result", {}).get("ws", [])
            for ws_item in data:
                for cw_item in ws_item.get("cw", []):
                    result += cw_item.get("w", "")
            
            return result
        except Exception as e:
            logging.error("结果解析错误: {}".format(e))
            return ""


class SpeechDetector:
    """语音活动检测器"""
    
    def __init__(self):
        # 噪音基准
        self.noise_floor = None
        self.noise_adapt_rate = 0.9
        self.speech_threshold_factor = 1.8  # 降低阈值，更敏感
        
        # 语音状态
        self.is_recording = False
        self.speech_count = 0
        self.silence_count = 0
        self.total_frames = 0
        self.recording_frames = 0  # 录音帧计数
        
        # 阈值（更快响应和结束）
        self.min_speech_count = 2  # 减少到2帧就开始
        self.max_silence_count = 8  # 减少静音容忍度，更快结束
        self.min_rms = 6  # 降低最小RMS阈值
        self.warm_up_frames = 10  # 预热帧数
        self.max_recording_frames = 300  # 最大录音帧数（30秒）
    
    def process(self, rms):
        """处理RMS值，返回是否为语音"""
        self.total_frames += 1
        
        # 更新噪音基准
        if self.noise_floor is None:
            self.noise_floor = max(rms, 3)  # 避免过低的噪音基准
        elif rms < self.noise_floor * 1.5:
            self.noise_floor = (
                self.noise_floor * self.noise_adapt_rate + 
                rms * (1 - self.noise_adapt_rate)
            )
        
        # 判断是否为语音
        speech_threshold = self.noise_floor * self.speech_threshold_factor
        is_speech = rms > max(speech_threshold, self.min_rms)
        
        # 预热期间更宽松的检测
        if self.total_frames <= self.warm_up_frames:
            is_speech = rms > self.min_rms
        
        # 更新计数器
        if is_speech:
            self.speech_count += 1
            self.silence_count = 0
            
            # 开始录音
            if self.speech_count >= self.min_speech_count:
                if not self.is_recording:
                    logging.info("开始录音 (RMS: {}, 阈值: {})".format(rms, speech_threshold))
                self.is_recording = True
        else:
            self.silence_count += 1
            self.speech_count = 0
        
        # 录音状态跟踪
        if self.is_recording:
            self.recording_frames += 1
        
        # 调试信息（仅在关键时刻）
        if self.total_frames % 20 == 0:  # 每2秒输出一次
            logging.debug("RMS: {}, 噪音基准: {:.1f}, 阈值: {:.1f}, 录音: {}, 静音: {}".format(
                rms, self.noise_floor, speech_threshold, self.is_recording, self.silence_count))
        
        # 返回是否应该处理此帧
        return is_speech and self.is_recording
    
    def should_stop(self):
        """检查是否应该停止录音"""
        if not self.is_recording:
            return False
        
        # 多种停止条件
        conditions = [
            # 静音时间足够长
            self.silence_count >= self.max_silence_count,
            # 录音时间过长
            self.recording_frames >= self.max_recording_frames,
        ]
        
        should_stop = any(conditions)
        
        if should_stop:
            reason = ""
            if self.silence_count >= self.max_silence_count:
                reason = "静音时间过长({}帧/{:.1f}秒)".format(self.silence_count, self.silence_count * 0.1)
            elif self.recording_frames >= self.max_recording_frames:
                reason = "录音时间过长({}帧/{:.1f}秒)".format(self.recording_frames, self.recording_frames * 0.1)
            
            logging.info("停止录音: {}".format(reason))
        
        return should_stop


# 模块级单例实例
speech_recognition = SpeechRecognition() 


# 测试代码
if __name__ == "__main__":
    import time
    import gc
    
    print("=== 语音识别服务测试 ===")
    print("配置：总超时60秒，最大录音30秒")
    
    try:
        # 确保已连接网络
        from services.network import network_manager
        network = network_manager
        if not network.is_connected:
            print("正在连接网络...")
            if not network.connect():
                print("网络连接失败，无法测试语音识别")
                exit()
        
        speech = speech_recognition
        
        # 测试1：基础识别测试
        print("\n1. 基础语音识别测试")
        print("请准备说话，系统将立即开始监听...")
        print("提示：可以说 '你好' 或 '测试一下'")
        print("系统会在检测到语音后立即开始识别")
        
        time.sleep(1)
        print("\n开始监听...")
        
        start_time = time.ticks_ms()
        result = speech.recognize()
        elapsed = time.ticks_diff(time.ticks_ms(), start_time)
        
        if result:
            print("识别结果: '{}'".format(result))
            print("识别时间: {}ms".format(elapsed))
        else:
            print("未识别到语音或识别失败")
            print("可能原因：1)环境过于安静 2)网络问题 3)麦克风问题")
        
        # 测试2：音频环境测试
        print("\n2. 音频环境测试")
        print("测试当前环境的音频情况...")
        
        detector = SpeechDetector()
        samples = []
        speech_samples = []
        
        # 采集环境样本
        chunk = bytearray(1600)  # 使用与识别相同的缓冲区大小
        audio = speech.audio_input
        
        print("采集环境音频样本（3秒）...")
        for i in range(30):  # 3秒
            length = audio.read(chunk)
            if length > 0:
                rms = speech._calculate_rms(chunk, length)
                samples.append(rms)
                is_speech = detector.process(rms)
                if is_speech:
                    speech_samples.append(rms)
                    
                # 实时显示音量
                if i % 5 == 0:
                    volume_bar = "#" * (min(rms // 5, 20))
                    print("音量: [{}{}] RMS:{}".format(
                        volume_bar, 
                        " " * (20 - len(volume_bar)), 
                        rms
                    ))
            time.sleep_ms(100)
        
        if samples:
            avg_noise = sum(samples) / len(samples)
            max_noise = max(samples)
            min_noise = min(samples)
            
            print("\n环境音频分析:")
            print("  平均RMS: {:.1f}".format(avg_noise))
            print("  RMS范围: {} - {}".format(min_noise, max_noise))
            print("  噪音基准: {:.1f}".format(detector.noise_floor or 0))
            print("  语音阈值: {:.1f}".format((detector.noise_floor or 0) * detector.speech_threshold_factor))
            print("  检测到语音帧: {} / {}".format(len(speech_samples), len(samples)))
            
            # 给出建议
            if avg_noise < 5:
                print("  环境评估: 非常安静，语音检测可能过于敏感")
            elif avg_noise < 15:
                print("  环境评估: 较安静，适合语音识别")
            elif avg_noise < 30:
                print("  环境评估: 有一定噪音，建议调高说话音量")
            else:
                print("  环境评估: 噪音较大，可能影响识别效果")
        
        # 测试3：快速识别测试
        print("\n3. 快速识别测试")
        print("测试快速语音识别响应...")
        print("请说一个简短的词语（如'你好'）...")
        
        time.sleep(2)
        
        start_time = time.ticks_ms()
        result = speech.recognize()
        elapsed = time.ticks_diff(time.ticks_ms(), start_time)
        
        if result:
            print("识别结果: '{}'".format(result))
            print("识别时间: {}ms".format(elapsed))
            
            # 评估性能
            if elapsed < 5000:
                print("性能评估: 优秀（< 5秒）")
            elif elapsed < 10000:
                print("性能评估: 良好（< 10秒）")
            elif elapsed < 15000:
                print("性能评估: 一般（< 15秒）")
            else:
                print("性能评估: 需要优化（>= 15秒）")
        else:
            print("未识别到语音或识别失败")
        
        print("内存使用: {} KB".format(gc.mem_alloc() // 1024))
        gc.collect()
        
        # 测试4：WebSocket连接测试
        print("\n4. WebSocket连接测试")
        print("测试创建URL...")
        
        url = speech.create_iat_url()
        print("URL创建成功: {}...".format(url[:50]))
        
        print("测试连接...")
        if speech.connect(url):
            print("连接成功")
            speech.close()
        else:
            print("连接失败")
        
        print("\n语音识别服务测试完成")
        
    except Exception as e:
        print("语音识别服务测试失败: {}".format(e))
        import sys
        sys.print_exception(e)
    finally:
        gc.collect() 