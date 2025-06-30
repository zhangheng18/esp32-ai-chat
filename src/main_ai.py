import gc
import logging
from machine import Timer
import time

# 导入服务
from services import (
    network_manager,
    ai_chat,
    speech_recognition,
    text_to_speech
)

# 导入硬件
from hardware import button, display

# 导入UI视图
from ui import TimeView, ImageView, ChatView

# 导入工具
from utils import timeit


class AIAssistant:
    """AI助手主类"""
    
    def __init__(self):
        # 初始化服务
        self.network = network_manager
        self.ai_chat = ai_chat
        self.speech_recognition = speech_recognition
        self.tts = text_to_speech
        
        # 初始化硬件
        self.button = button
        self.display = display
        
        # 初始化UI视图
        self.time_view = TimeView()
        self.image_view = ImageView("gif/img1.pbm")
        self.chat_view = ChatView()
        
        # 定时器
        self.time_timer = Timer(0)
        self.ntp_timer = Timer(1)
        
        # 状态
        self.is_idle = True
        
    def start(self):
        """启动助手"""
        logging.info("AI助手启动中...")
        
        # 初始化显示
        self.display.clear()
        self.image_view.show()
        
        # 设置按钮回调
        self.button.set_callback(self._on_button_press)
        
        # 启动定时器
        self._start_timers()
        
        logging.info("AI助手已启动")
    
    def _start_timers(self):
        """启动定时器"""
        # 每秒更新时间显示
        self.time_timer.init(
            period=1000, 
            mode=Timer.PERIODIC, 
            callback=lambda t: self._update_time_display()
        )
        
        # 每小时同步NTP时间
        self.ntp_timer.init(
            period=3600000,  # 1小时
            mode=Timer.PERIODIC,
            callback=lambda t: self._sync_time()
        )
    
    def _update_time_display(self):
        """更新时间显示"""
        if self.is_idle:
            self.time_view.show()
    
    def _sync_time(self):
        """同步NTP时间"""
        try:
            self.network.sync_time()
        except Exception as e:
            logging.error("时间同步失败: {}".format(e))
    
    def _on_button_press(self):
        """按钮按下处理"""
        if not self.is_idle:
            return
        
        # 在新的任务中处理，避免阻塞中断
        self._process_voice_chat()
    
    @timeit
    def _process_voice_chat(self):
        """处理语音聊天"""
        self.is_idle = False
        gc.collect()
        
        try:
            # 显示聊天界面
            self.chat_view.clear()
            self.chat_view.set_status("正在听...")
            
            # 语音识别
            question = self.speech_recognition.recognize()
            if not question:
                self.chat_view.set_status("没有听到声音")
                time.sleep(2)
                return
            
            logging.info("识别结果: {}".format(question))
            self.chat_view.set_question(question)
            self.chat_view.set_status("正在思考...")
            
            # AI对话
            answer = self.ai_chat.chat(question)
            logging.info("AI回复: {}".format(answer))
            self.chat_view.set_answer(answer)
            self.chat_view.set_status("")
            
            # 语音合成
            self.tts.synthesize(answer)
            
        except Exception as e:
            logging.error("语音聊天错误: {}".format(e))
            self.chat_view.set_status("出错了，请重试")
            time.sleep(2)
        finally:
            # 恢复待机界面
            time.sleep(1)
            self.display.clear()
            self.image_view.show()
            self.is_idle = True
            gc.collect()
    
    def stop(self):
        """停止助手"""
        # 停止定时器
        self.time_timer.deinit()
        self.ntp_timer.deinit()
        
        # 禁用按钮中断
        self.button.disable_irq()
        
        logging.info("AI助手已停止")


def main():
    """主函数"""
    try:
        # 创建并启动AI助手
        assistant = AIAssistant()
        assistant.start()
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("收到中断信号")
        assistant.stop()
    except Exception as e:
        logging.error("主程序错误: {}".format(e))
        raise


if __name__ == "__main__":
    main() 