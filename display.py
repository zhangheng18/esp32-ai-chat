import gc
import time
from io import BytesIO

from config import dp, ed, dht
from utils import timeit, get_local_time, format_datetime


@timeit
def display_time():
    """显示日期和时间"""

    # 获取当前日期和时间
    tm = get_local_time()
    date_str, time_str = format_datetime(tm)

    # 计算文本居中的位置
    date_width = len(date_str) * 12
    time_width = len(time_str) * 12

    x_date = (dp.width - date_width) // 2
    x_time = (dp.width - time_width) // 2

    y_date = (dp.height // 2) - 24 - 12
    y_time = dp.height // 2 - 12

    # 显示日期和时间
    ed.text(
        date_str,
        x_date,
        y_date,
        bg_color=0xFFFF,
        size=24,
    )
    ed.text(
        time_str,
        x_time,
        y_time,
        size=24,
    )


@timeit
def display_gif():
    """显示GIF图片"""
    # 读取到内存，加速渲染
    img_file = ["gif/img{}.pbm".format(i) for i in range(1, 5)]
    img_io = []
    for i in img_file:
        with open(i, 'rb') as f:
            b = BytesIO()
            b.write(f.read())
            img_io.append(b)
    gc.collect()
    # 遍历图片，模拟动画
    for f in img_io:
        f.seek(0)
        ed.pbm(f, 150, 185, invert=True)


@timeit
def display_img():
    """显示图片"""
    ed.pbm("gif/img1.pbm", 160, 200, invert=True)


@timeit
def display_th(dht):
    if dht.measure():
        temp_str = "T:{:.1f}C".format(dht.temperature())
        humi_str = "H:{:.1f}%".format(dht.humidity())
        ed.text(
            temp_str,
            40,
            200,
            color=ed.rgb565_color(255, 0, 0),
            bg_color=0xFFFF,
            size=24,
        )
        ed.text(
            humi_str,
            40,
            224,
            color=ed.rgb565_color(0, 255, 0),
            bg_color=0xFFFF,
            size=24,
        )


if __name__ == "__main__":
    # # 红色
    # ed.fill(ed.rgb565_color(255, 0, 0))
    # ed.show()
    # time.sleep(1)
    #
    # # 绿色
    # ed.fill(ed.rgb565_color(0, 255, 0))
    # ed.show()
    # time.sleep(1)
    #
    # # 蓝色
    # ed.fill(ed.rgb565_color(0, 0, 255))
    # ed.show()
    # time.sleep(1)

    # 填充白色
    ed.fill(0xFFFF)
    ed.show()
    time.sleep(1)

    y = 0

    ed.text(
        "Hello, 张三",
        0,
        0,
        size=24,
    )

    # ed.pbm("gif/img1.pbm", 80, 200,invert=True)

    display_time()
    display_time()

    display_gif()
    display_th(dht)
