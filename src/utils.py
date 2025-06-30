import gc
import time
from config import TIMEZONE_OFFSET, DEBUG


# Weekday and month names for HTTP date/time formatting; always English!
_weekdayname = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_monthname = (
    None,  # Dummy so we can use 1-based month numbers
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def format_date_time(timestamp):
    # https://docs.micropython.org/en/latest/library/time.html
    year, month, day, hh, mm, ss, wd, yd = time.gmtime(timestamp)
    return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
        _weekdayname[wd],
        day,
        _monthname[month],
        year,
        hh,
        mm,
        ss,
    )


def get_local_time():
    # 获取当前UTC时间并应用时区偏移量
    t = time.time() + TIMEZONE_OFFSET
    return time.localtime(t)


def format_datetime(tm):
    date_str = '{:04}-{:02}-{:02}'.format(tm[0], tm[1], tm[2])
    time_str = '{:02}:{:02}:{:02}'.format(tm[3], tm[4], tm[5])
    return date_str, time_str


def urlencode(params):
    """
    A simple urlencode function compatible with MicroPython.

    :param params: A dictionary of parameters to encode.
    :return: An URL-encoded string.
    """

    def quote(string):
        """
        A simple implementation of URL quoting.
        """
        reserved = b"!#$&'()*+,/:;=?@[]"
        result = ""
        for char in string:
            c = ord(char)
            if (
                (48 <= c <= 57) or (65 <= c <= 90) or (97 <= c <= 122) or c in (45, 46, 95, 126)
            ):  # 0-9, A-Z, a-z, -._~
                result += char
            elif char == ' ':
                result += "%20"
            elif char.encode('ascii') in reserved:
                result += "%" + "{:02X}".format(c)
            else:
                result += "%" + "{:02X}".format(c)
        return result

    return "&".join("{}={}".format(quote(str(k)), quote(str(v))) for k, v in params.items())


def timeit(func, *args, **kwargs):
    """测试函数运行时间"""
    # 当交叉编译后无法获取函数名
    try:
        _name = func.__name__
    except AttributeError:
        _name = "Unknown"

    def get_running_time(*args, **kwargs):
        if DEBUG:
            t = time.ticks_us()
            result = func(*args, **kwargs)
            delta = time.ticks_diff(time.ticks_us(), t)
            print(
                'Func {} Time={:6.3f}ms  Mem:{:.3f} MB'.format(
                    _name, delta / 1000, gc.mem_free() / 1024 / 1024
                )
            )
            return result
        return func(*args, **kwargs)

    return get_running_time


# 测试代码
if __name__ == "__main__":
    import time as time_module
    
    print("=== 工具函数测试 ===")
    
    # 测试1：日期时间格式化测试
    print("\n1. 日期时间格式化测试")
    
    # 测试format_date_time
    print("测试format_date_time...")
    current_timestamp = time_module.time()
    formatted = format_date_time(current_timestamp)
    print("当前时间戳: {}".format(current_timestamp))
    print("格式化结果: {}".format(formatted))
    
    # 测试不同的时间戳
    test_timestamps = [
        0,  # 1970-01-01
        1640995200,  # 2022-01-01
        current_timestamp,  # 当前时间
    ]
    
    for ts in test_timestamps:
        result = format_date_time(ts)
        print("时间戳 {} -> {}".format(ts, result))
    
    # 测试2：本地时间测试
    print("\n2. 本地时间测试")
    
    # 测试get_local_time
    print("测试get_local_time...")
    local_tm = get_local_time()
    print("本地时间: {}".format(local_tm))
    print("年: {}, 月: {}, 日: {}".format(local_tm[0], local_tm[1], local_tm[2]))
    print("时: {}, 分: {}, 秒: {}".format(local_tm[3], local_tm[4], local_tm[5]))
    
    # 测试format_datetime
    print("\n测试format_datetime...")
    date_str, time_str = format_datetime(local_tm)
    print("日期字符串: {}".format(date_str))
    print("时间字符串: {}".format(time_str))
    
    # 测试3：URL编码测试
    print("\n3. URL编码测试")
    
    test_params = [
        {"key": "value"},
        {"name": "张三", "age": "25"},
        {"url": "http://example.com", "query": "test&debug=1"},
        {"special": "!@#$%^&*()"},
        {"space": "hello world"},
    ]
    
    for params in test_params:
        encoded = urlencode(params)
        print("参数: {} -> {}".format(params, encoded))
    
    # 测试4：timeit装饰器测试
    print("\n4. timeit装饰器测试")
    
    # 创建测试函数
    @timeit
    def test_function(delay_ms):
        """测试函数，延迟指定毫秒"""
        start = time_module.ticks_ms()
        while time_module.ticks_diff(time_module.ticks_ms(), start) < delay_ms:
            pass
        return "完成"
    
    # 测试不同的延迟
    print("测试不同延迟的函数...")
    DEBUG = True  # 确保启用调试输出
    
    for delay in [10, 50, 100]:
        print("\n延迟 {}ms:".format(delay))
        result = test_function(delay)
        print("返回值: {}".format(result))
    
    # 测试DEBUG关闭时的行为
    print("\n测试DEBUG=False时的行为...")
    DEBUG = False
    result = test_function(50)
    print("返回值: {} (应该没有时间输出)".format(result))
    DEBUG = True
    
    # 测试5：内存和垃圾回收测试
    print("\n5. 内存测试")
    
    print("创建大对象前:")
    print("空闲内存: {} KB".format(gc.mem_free() // 1024))
    
    # 创建一些大对象
    big_list = [bytearray(1024) for _ in range(10)]  # 10KB
    print("\n创建10KB对象后:")
    print("空闲内存: {} KB".format(gc.mem_free() // 1024))
    
    # 删除并回收
    del big_list
    gc.collect()
    print("\n垃圾回收后:")
    print("空闲内存: {} KB".format(gc.mem_free() // 1024))
    
    print("\n工具函数测试完成")
