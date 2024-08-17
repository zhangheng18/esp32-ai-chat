import gc
import time

from config import TIMEZONE_OFFSET

DEBUG = True

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
                (48 <= c <= 57)
                or (65 <= c <= 90)
                or (97 <= c <= 122)
                or c in (45, 46, 95, 126)
            ):  # 0-9, A-Z, a-z, -._~
                result += char
            elif char == ' ':
                result += "%20"
            elif char.encode('ascii') in reserved:
                result += "%" + "{:02X}".format(c)
            else:
                result += "%" + "{:02X}".format(c)
        return result

    return "&".join(f"{quote(str(k))}={quote(str(v))}" for k, v in params.items())


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
