from machine import Pin, I2S
import gc
import struct
from config import (
    MIC_SD_PIN, MIC_SCK_PIN, MIC_WS_PIN,
    SPEAKER_BCLK_PIN, SPEAKER_LRC_PIN, SPEAKER_DIN_PIN,
    I2S_CONFIG
)


def create_wav_header(sample_rate, bits_per_sample, channels, data_size):
    """创建WAV文件头"""
    # 计算一些参数
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    # WAV文件头结构
    header = struct.pack('<4sI4s',      # RIFF头
                        b'RIFF',        # ChunkID
                        36 + data_size, # ChunkSize
                        b'WAVE')        # Format
    
    header += struct.pack('<4sIHHIIHH', # fmt子块
                         b'fmt ',       # Subchunk1ID
                         16,            # Subchunk1Size (PCM)
                         1,             # AudioFormat (PCM)
                         channels,      # NumChannels
                         sample_rate,   # SampleRate
                         byte_rate,     # ByteRate
                         block_align,   # BlockAlign
                         bits_per_sample) # BitsPerSample
    
    header += struct.pack('<4sI',       # data子块头
                         b'data',       # Subchunk2ID
                         data_size)     # Subchunk2Size
    
    return header


class AudioInput:
    """麦克风输入管理"""
    def __init__(self):
        self.i2s = None
        self._init_i2s()
    
    def _init_i2s(self):
        """初始化I2S输入"""
        self.i2s = I2S(
            0,
            sck=Pin(MIC_SCK_PIN),
            ws=Pin(MIC_WS_PIN),
            sd=Pin(MIC_SD_PIN),
            mode=I2S.RX,
            bits=I2S_CONFIG["bits"],
            format=I2S.MONO,
            rate=I2S_CONFIG["rate"],
            ibuf=I2S_CONFIG["ibuf"],
        )
    
    def read(self, buffer):
        """读取音频数据"""
        return self.i2s.readinto(buffer)
    
    def deinit(self):
        """释放资源"""
        if self.i2s:
            self.i2s.deinit()
            self.i2s = None
        gc.collect()


class AudioOutput:
    """扬声器输出管理"""
    def __init__(self):
        self.i2s = None
        self._init_i2s()
    
    def _init_i2s(self):
        """初始化I2S输出"""
        self.i2s = I2S(
            1,
            sck=Pin(SPEAKER_BCLK_PIN),
            ws=Pin(SPEAKER_LRC_PIN),
            sd=Pin(SPEAKER_DIN_PIN),
            mode=I2S.TX,
            bits=I2S_CONFIG["bits"],
            format=I2S.MONO,
            rate=I2S_CONFIG["rate"],
            ibuf=I2S_CONFIG["ibuf"] * 2,
        )
    
    def write(self, data):
        """写入音频数据"""
        return self.i2s.write(data)
    
    def deinit(self):
        """释放资源"""
        if self.i2s:
            self.i2s.deinit()
            self.i2s = None
        gc.collect()


# 模块级单例实例
audio_input = AudioInput()
audio_output = AudioOutput()


# 测试代码
if __name__ == "__main__":
    import time
    import gc
    
    print("=== 音频硬件测试 ===")
    
    try:
        audio_in = audio_input
        audio_out = audio_output
        
        # 测试1：录音回放测试
        print("\n1. 录音回放测试")
        print("准备录音3秒，请开始说话...")
        time.sleep(2)  # 给用户准备时间
        
        # 录音阶段
        print("开始录音...")
        recorded_data = bytearray()
        buffer = bytearray(1600)  # 0.1秒的音频缓冲区
        
        start_time = time.time()
        sample_count = 0
        max_volume = 0
        
        while time.time() - start_time < 3:
            length = audio_in.read(buffer)
            if length > 0:
                sample_count += 1
                # 保存录制的音频数据
                recorded_data.extend(buffer[:length])
                
                # 计算音量（用于显示录音状态）
                volume = sum(abs(b - 128) for b in buffer[:length]) // length
                max_volume = max(max_volume, volume)
                
                # 显示录音状态
                if sample_count % 10 == 0:  # 每秒显示一次
                    print("录音中... 音量: {}".format("#" * (volume // 8)))
        
        print("录音完成！")
        print("录制了 {} 个音频块，共 {} 字节".format(sample_count, len(recorded_data)))
        print("最大音量: {}".format(max_volume))
        
        if len(recorded_data) == 0:
            print("警告：没有录制到音频数据")
        else:
            # 保存录音文件为WAV格式
            print("\n保存录音文件...")
            try:
                import time
                timestamp = "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(*time.localtime()[:6])
                filename = "recorded_audio_{}.wav".format(timestamp)
                
                # 获取音频参数
                sample_rate = I2S_CONFIG["rate"]      # 16000 Hz
                bits_per_sample = I2S_CONFIG["bits"]  # 16 bit
                channels = 1                          # 单声道
                data_size = len(recorded_data)
                
                # 创建WAV文件头
                wav_header = create_wav_header(sample_rate, bits_per_sample, channels, data_size)
                
                # 保存WAV文件
                with open(filename, 'wb') as f:
                    f.write(wav_header)      # 写入WAV头
                    f.write(recorded_data)   # 写入PCM数据
                
                print("录音已保存到: {}".format(filename))
                print("文件格式: WAV ({}kHz, {}bit, {})".format(
                    sample_rate // 1000, 
                    bits_per_sample,
                    "Mono" if channels == 1 else "Stereo"
                ))
                print("文件大小: {} 字节 (含44字节WAV头)".format(len(wav_header) + data_size))
                print("录音时长: {:.1f} 秒".format(data_size / (sample_rate * channels * bits_per_sample // 8)))
                
            except Exception as e:
                print("保存录音文件失败: {}".format(e))
            time.sleep(1)
            
            # 播放阶段
            print("\n2. 播放录制的音频...")
            print("开始播放刚才录制的内容...")
            
            try:
                # 分块播放音频数据
                chunk_size = 1600
                total_chunks = len(recorded_data) // chunk_size
                
                for i in range(0, len(recorded_data), chunk_size):
                    chunk = recorded_data[i:i + chunk_size]
                    if len(chunk) > 0:
                        audio_out.write(chunk)
                        
                        # 显示播放进度
                        progress = (i // chunk_size + 1)
                        if progress % 10 == 0:
                            print("播放进度: {}/{}".format(progress, total_chunks))
                
                print("播放完成！")
                
            except Exception as e:
                print("播放失败: {}".format(e))
            
            time.sleep(1)
            
            # 测试2：音频质量测试
            print("\n3. 音频质量分析...")
            if len(recorded_data) >= 3200:  # 至少0.2秒的数据
                # 分析前0.2秒的音频
                sample_data = recorded_data[:3200]
                
                # 计算平均音量
                total_volume = sum(abs(b - 128) for b in sample_data)
                avg_volume = total_volume // len(sample_data)
                
                # 计算动态范围
                max_val = max(sample_data)
                min_val = min(sample_data)
                dynamic_range = max_val - min_val
                
                print("音频质量分析:")
                print("  平均音量: {}".format(avg_volume))
                print("  动态范围: {}".format(dynamic_range))
                print("  数据范围: {} - {}".format(min_val, max_val))
                
                # 简单的信噪比评估
                if dynamic_range > 50:
                    print("  音频质量: 良好 (动态范围充足)")
                elif dynamic_range > 20:
                    print("  音频质量: 一般 (动态范围较小)")
                else:
                    print("  音频质量: 较差 (可能是噪音或静音)")
        
    except Exception as e:
        print("音频测试失败: {}".format(e))
        import sys
        sys.print_exception(e)
    
    finally:
        # 清理资源
        print("\n5. 清理资源...")
        try:
            audio_input.deinit()
            print("音频输入资源已释放")
            audio_output.deinit()
            print("音频输出资源已释放")
        except:
            pass
        
        gc.collect()
        print("内存已清理")
    
    print("\n音频测试完成！") 