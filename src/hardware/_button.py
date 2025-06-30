from machine import Pin
import time
from config import BUTTON_PIN


class Button:
    """按钮管理"""
    def __init__(self, pin_num=BUTTON_PIN, debounce_ms=50):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.debounce_ms = debounce_ms
        self._last_press_time = 0
        self._callback = None
    
    def set_callback(self, callback):
        """设置按钮回调函数"""
        self._callback = callback
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._irq_handler)
    
    def _irq_handler(self, pin):
        """中断处理函数，包含防抖处理"""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self._last_press_time) > self.debounce_ms:
            self._last_press_time = current_time
            if self._callback:
                self._callback()
    
    def is_pressed(self):
        """检查按钮是否被按下"""
        return self.pin.value() == 0
    
    def wait_for_press(self, timeout_ms=None):
        """等待按钮按下"""
        start = time.ticks_ms()
        while True:
            if self.is_pressed():
                # 等待释放
                while self.is_pressed():
                    time.sleep_ms(10)
                return True
            
            if timeout_ms and time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                return False
            
            time.sleep_ms(10)
    
    def disable_irq(self):
        """禁用中断"""
        self.pin.irq(handler=None)


# 模块级单例实例
button = Button() 


# 测试代码
if __name__ == "__main__":
    import time
    
    print("=== 按钮硬件测试 ===")
    
    try:
        button_device = button
        
        # 测试1：轮询模式测试
        print("\n1. 轮询模式测试")
        print("请在5秒内按下按钮...")
        
        start_time = time.time()
        press_count = 0
        
        while time.time() - start_time < 5:
            if button_device.is_pressed():
                press_count += 1
                print("按钮被按下！(第{}次)".format(press_count))
                # 等待释放
                while button_device.is_pressed():
                    time.sleep_ms(10)
            time.sleep_ms(50)
        
        print("轮询测试完成，按下次数: {}".format(press_count))
        
        # 测试2：中断模式测试
        print("\n2. 中断模式测试")
        print("请在5秒内按下按钮...")
        
        interrupt_count = 0
        
        def on_button_press():
            global interrupt_count
            interrupt_count += 1
            print("中断触发！(第{}次)".format(interrupt_count))
        
        button_device.set_callback(on_button_press)
        
        # 等待5秒
        time.sleep(5)
        
        # 禁用中断
        button_device.disable_irq()
        print("中断测试完成，触发次数: {}".format(interrupt_count))
        
        # 测试3：等待按钮测试
        print("\n3. 等待按钮测试")
        print("请在3秒内按下按钮...")
        
        if button_device.wait_for_press(timeout_ms=3000):
            print("按钮被按下!")
        else:
            print("超时，未检测到按钮按下")
        
        print("\n按钮测试完成")
        
    except Exception as e:
        print("按钮测试失败: {}".format(e))
        import sys
        sys.print_exception(e) 