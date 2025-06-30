from machine import Pin, SPI
import st7789_buf as st7789
from easydisplay import EasyDisplay
from config import (
    DISPLAY_SCK_PIN, DISPLAY_MOSI_PIN, DISPLAY_CS_PIN,
    DISPLAY_DC_PIN, DISPLAY_RST_PIN, DISPLAY_BL_PIN,
    DISPLAY_CONFIG
)


class Display:
    """显示屏管理"""
    def __init__(self):
        self.spi = None
        self.driver = None
        self.ed = None
        self._init_display()
    
    def _init_display(self):
        """初始化显示屏"""
        # 初始化SPI
        self.spi = SPI(1, baudrate=40000000, 
                      sck=Pin(DISPLAY_SCK_PIN), 
                      mosi=Pin(DISPLAY_MOSI_PIN))
        
        # 初始化显示驱动
        self.driver = st7789.ST7789(
            width=DISPLAY_CONFIG["width"],
            height=DISPLAY_CONFIG["height"],
            spi=self.spi,
            cs=DISPLAY_CS_PIN,
            dc=DISPLAY_DC_PIN,
            res=DISPLAY_RST_PIN,
            rotate=DISPLAY_CONFIG["rotate"],
            bl=DISPLAY_BL_PIN,
            invert=DISPLAY_CONFIG["invert"],
            rgb=DISPLAY_CONFIG["rgb"],
        )
        
        self.driver.back_light(255)
        
        # 初始化EasyDisplay
        self.ed = EasyDisplay(
            self.driver,
            "RGB565",
            font="font/text_lite_24px_2312.v3.bmf",
            show=True,
            color=0x0000,
            bg_color=0xffff,
            clear=False,
            auto_wrap=True,
        )
    
    def clear(self, color=0xFFFF):
        """清屏"""
        self.ed.fill(color)
        self.ed.show()
    
    def text(self, text, x, y, **kwargs):
        """显示文本"""
        self.ed.text(text, x, y, **kwargs)
    
    def image(self, filename, x, y, **kwargs):
        """显示图片"""
        self.ed.pbm(filename, x, y, **kwargs)
    
    def fill(self, color):
        """填充颜色"""
        self.ed.fill(color)
        self.ed.show()
    def rgb565_color(self, r, g, b):
        """将RGB颜色转换为RGB565颜色"""
        return self.ed.rgb565_color(r, g, b)
    
    def show(self):
        """刷新显示"""
        self.ed.show()
    
    def set_backlight(self, brightness):
        """设置背光亮度 (0-100)"""
        self.driver.back_light(brightness)
    
    @property
    def width(self):
        return self.driver.width
    
    @property
    def height(self):
        return self.driver.height


# 模块级单例实例
display = Display() 


# 测试代码
if __name__ == "__main__":
    import time
    
    print("=== 显示屏硬件测试 ===")
    
    try:
        display_device = display
        display.show()
        time.sleep(1)
        # 测试1：颜色测试
        print("\n1. 颜色测试...")
        colors = [
            (0xF800, "红色"),  # RGB565红色
            (0x07E0, "绿色"),  # RGB565绿色
            (0x001F, "蓝色"),  # RGB565蓝色
            (0xFFFF, "白色"),  # RGB565白色
            (0x0000, "黑色"),  # RGB565黑色
        ]
        
        for color, name in colors:
            print("显示{}".format(name))
            display.fill(color)
            display.show()
            time.sleep(1)
        
        # 测试2：文本显示
        print("\n2. 文本显示测试...")
        display.clear()
        
        # 测试不同位置的文本
        texts = [
            ("左上角", 0, 0),
            ("右上角", display_device.width - 60, 0),
            ("中心", display_device.width // 2 - 30, display_device.height // 2 - 12),
            ("左下角", 0, display_device.height - 24),
            ("右下角", display_device.width - 60, display_device.height - 24),
        ]
        
        for text, x, y in texts:
            display.text(text, x, y, size=24)
        display_device.show()
        time.sleep(3)
        
        # 测试3：图片显示
        print("\n3. 图片显示测试...")
        display.clear()
        try:
            display.image("gif/img1.pbm", display_device.width // 2 - 40, display_device.height // 2 - 40)
            print("图片显示成功")
        except Exception as e:
            print("图片显示失败: {}".format(e))
            display_device.text("No Image", display_device.width // 2 - 48, display_device.height // 2 - 12)
        display_device.show()
        time.sleep(2)
        
        # 测试4：背光调节
        print("\n4. 背光调节测试...")
        for brightness in [100, 75, 50, 25, 0]:
            print("背光亮度: {}%".format(brightness))
            display_device.set_backlight(brightness)
            time.sleep(0.5)
        display_device.set_backlight(100)  # 恢复最大亮度
        
        # 测试5：绘制图形
        print("\n5. 图形绘制测试...")
        display_device.clear()
        
        # 绘制边框
        for x in range(display_device.width):
            display_device.ed.pixel(x, 0, 0xF800)  # 上边框
            display_device.ed.pixel(x, display_device.height - 1, 0xF800)  # 下边框
        
        for y in range(display_device.height):
            display_device.ed.pixel(0, y, 0xF800)  # 左边框
            display_device.ed.pixel(display_device.width - 1, y, 0xF800)  # 右边框
        
        # 显示测试完成信息
        display_device.text("测试完成!", display_device.width // 2 - 48, display_device.height // 2 - 12, size=24)
        display_device.show()
        
        print("\n显示屏测试完成")
        
    except Exception as e:
        print("显示屏测试失败: {}".format(e))
        import sys
        sys.print_exception(e) 