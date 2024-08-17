# Github: https://github.com/funnygeeker/micropython-easybutton
# Author: funnygeeker (稽术宅)
# License: MIT
#
# 参考资料：
# MicroPython优雅的实现中断：https://www.skyone.host/2021/micropython-interrupt
import time

from machine import Pin


def _call(func, *args):
    """
    调用函数并传递参数
        如果 func 是可调用对象，则执行 func(*args)
        如果 func 是元组且第一个元素为可调用对象，则执行 func[0](*(func[1] + args))

    Args:
        func: 函数或函数元组
        *args: 传递给函数的参数
    """
    if callable(func):
        func(*args)
    elif type(func) is tuple and callable(func[0]):
        in_args = func[1] if type(func[1]) is tuple or type(func[1]) is list else (func[1],)
        func[0](*tuple(list(in_args) + list(args)))

class EasyButton:
    def __init__(self, button: Pin, hold: int = 350, long: int = 1000, interval: int = 30):
        """
        Args:
            button: For example: `Pin(2, Pin.IN, Pin.PULL_UP)`  # 按钮实例
            hold: The duration for each judgment cycle after the button is pressed, in milliseconds  # 按钮按下后每个判断周期的时长，单位：毫秒
            long: The time for the button press action to be considered a long press, in milliseconds  # 按钮按下行为被判定为长按的时间，单位：毫秒
            interval: The interval between two key detections (to eliminate bounce), in milliseconds  # 两次按键检测的间隔时间（消除抖动），单位：毫秒
        """
        self.__num = 1
        'hold function execution times (number of loops)'  # hold 函数执行次数（循环次数）
        self.__interval = 0
        'time interval from the last button press to release, in milliseconds'  # 上一次按钮按下时到松开时的时间间隔，单位：毫秒
        self.__end_time = 0
        'end time of the last button press, in milliseconds'  # 上一次按钮被按下的结束时间，单位：毫秒
        self.__start_time = 0
        'start time of the button press, in milliseconds'  # 按钮被按下的开始时间，单位：毫秒
        self.button = button
        'button object'  # 按钮对象
        self.hold_time = hold
        'the interval for the function to be executed after pressing, in milliseconds'  # 按下后函数每隔多久执行一次，单位：毫秒
        self.long_time = long
        'time for the button press action to be considered a long press, in milliseconds'  # 按钮按下行为被判定为长按的时间，单位：毫秒
        self.interval_time = interval
        'the interval between two key detections, in milliseconds'  # 两次按键的检测间隔时间，单位：毫秒
        self.irq = self.button.irq(handler=self._detection, trigger=Pin.IRQ_FALLING)
        'button interrupt handler'  # 按钮中断处理函数，详见：https://docs.micropython.org/en/latest/library/machine.Pin.html
        self.up_func = None
        'function to be executed when the button is released'  # 按钮松开时执行的函数
        self.down_func = None
        'function to be executed when the button is pressed'  # 按钮按下时执行的函数
        self.long_func = None
        'function to be executed when the button is long pressed and released'  # 按钮长按松开时执行的函数
        self.hold_func = None
        'function to be executed at regular intervals when the button is pressed'  # 按钮按下时每隔一段时间执行的函数
        self.short_func = None
        'function to be executed when the button is short pressed and released'  # 按钮短按松开时执行的函数

    def _detection(self, *args):
        if time.ticks_ms() > self.__end_time + self.interval_time:  # 按键消抖 (eliminate bounce)
            self.__start_time = time.ticks_ms()
            self._down()  # 执行按钮被按下的函数 (Execute the function when the button is pressed)
            while not self.button.value():  # 在按钮松开之前一直循环 (Loop until the button is released)
                self.__interval = time.ticks_ms() - self.__start_time  # 获取现在和开始之间的时差 (Get the time difference between now and the start)
                if self.__interval > self.hold_time * self.__num:  # 每达到一个周期执行一次周期函数 (Execute a periodic function every time a cycle is reached)
                    self.__num += 1
                    self._hold()
            if self.__interval > self.long_time:  # 如果按钮判断为长按  (If the button press is judged as a long press)
                self._long()
            else:
                self._short()
            self._up()  # 执行按钮被松开的函数 (Execute the function when the button is released)
            self.__num = 1  # 复位周期函数执行次数 (Reset the number of times the periodic function is executed)
            self.__run_time = 0  # 复位函数运行时消耗的时间 (Reset the time consumed by the function)
            self.__end_time = time.ticks_ms()  # 获取当前被按下的开始时间 (Get the current start time of the button press)

    def _up(self):
        _call(self.up_func)

    def _down(self):
        _call(self.down_func)

    def _hold(self):
        _call(self.hold_func)

    def _long(self):
        _call(self.long_func)

    def _short(self):
        _call(self.short_func)