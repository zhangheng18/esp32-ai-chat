from hardware import display
from utils import get_local_time, format_datetime, timeit


class BaseView:
    """视图基类"""
    
    def __init__(self):
        self.display = display
    
    def show(self):
        """显示视图"""
        raise NotImplementedError
    
    def clear(self):
        """清除视图"""
        self.display.clear()


class TimeView(BaseView):
    """时间显示视图"""
    
    @timeit
    def show(self):
        """显示日期和时间"""
        # 获取当前时间
        tm = get_local_time()
        date_str, time_str = format_datetime(tm)
        
        # 计算居中位置
        date_width = len(date_str) * 12
        time_width = len(time_str) * 12
        
        x_date = (self.display.width - date_width) // 2
        x_time = (self.display.width - time_width) // 2
        
        y_date = (self.display.height // 2) - 36
        y_time = self.display.height // 2 - 12
        
        # 显示
        self.display.text(date_str, x_date, y_date, bg_color=0xFFFF, size=24)
        self.display.text(time_str, x_time, y_time, size=24)
        self.display.show()  # 刷新显示


class ImageView(BaseView):
    """图片显示视图"""
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
    
    @timeit
    def show(self):
        """显示图片"""
        self.display.image(self.image_path, 160, 200, invert=True)
        self.display.show()  # 刷新显示


class ChatView(BaseView):
    """聊天显示视图"""
    
    def __init__(self):
        super().__init__()
        self.question = ""
        self.answer = ""
        self.status = ""
    
    def set_status(self, status):
        """设置状态信息"""
        self.status = status
        self._update_display()
    
    def set_question(self, question):
        """设置问题"""
        self.question = question
        self._update_display()
    
    def set_answer(self, answer):
        """设置答案"""
        self.answer = answer
        self._update_display()
    
    def _update_display(self):
        """更新显示内容"""
        self.display.clear()
        
        y_offset = 10
        
        # 显示状态
        if self.status:
            self.display.text(self.status, 0, y_offset, size=24)
            y_offset += 30
        
        # 显示问题
        if self.question:
            self.display.text("问: {}".format(self.question), 0, y_offset, size=24)
            y_offset += 30
        
        # 显示答案
        if self.answer:
            # 自动换行显示长答案
            self.display.text("答: {}".format(self.answer), 0, y_offset, size=24)
        
        self.display.show()  # 刷新显示
    
    def clear(self):
        """清除聊天内容"""
        self.question = ""
        self.answer = ""
        self.status = ""
        super().clear()


# 测试代码
if __name__ == "__main__":
    import time
    
    print("=== UI视图测试 ===")
    
    try:
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
            
        # 测试1：时间视图测试
        print("\n1. 时间视图测试")
        time_view = TimeView()
        
        print("显示当前时间...")
        for i in range(5):
            time_view.show()
            time.sleep(1)
        
        # 测试2：图片视图测试
        print("\n2. 图片视图测试")
        
        # 测试显示不同的图片
        image_files = ["gif/img1.pbm", "gif/img2.pbm", "gif/img3.pbm", "gif/img4.pbm"]
        
        for img_file in image_files:
            try:
                print("显示图片: {}".format(img_file))
                img_view = ImageView(img_file)
                img_view.clear()  # 清屏
                img_view.show()
                time.sleep(1)
            except Exception as e:
                print("图片显示失败: {}".format(e))
        
        # 测试3：聊天视图测试
        print("\n3. 聊天视图测试")
        chat_view = ChatView()
        
        # 测试不同状态
        print("测试状态显示...")
        chat_view.set_status("正在初始化...")
        time.sleep(1)
        
        chat_view.set_status("正在听...")
        time.sleep(1)
        
        # 测试问答显示
        print("测试问答显示...")
        test_qa = [
            ("你好", "你好！有什么可以帮助你的吗？"),
            ("今天天气怎么样", "今天天气晴朗，温度适宜。"),
            ("现在几点了", "现在是下午3点25分。"),
        ]
        
        for question, answer in test_qa:
            chat_view.clear()
            chat_view.set_status("识别中...")
            time.sleep(0.5)
            
            chat_view.set_question(question)
            chat_view.set_status("思考中...")
            time.sleep(1)
            
            chat_view.set_answer(answer)
            chat_view.set_status("")
            time.sleep(2)
        
        # 测试长文本显示
        print("测试长文本显示...")
        chat_view.clear()
        long_question = "这是一个很长的问题，用来测试自动换行功能是否正常工作"
        long_answer = "这是一个非常长的回答，包含了很多内容。" * 5
        
        chat_view.set_question(long_question)
        chat_view.set_answer(long_answer)
        time.sleep(3)
        
        # 测试清除功能
        print("测试清除功能...")
        chat_view.clear()
        time.sleep(1)
        
        # 测试4：混合显示测试
        print("\n4. 混合显示测试")
        
        # 先显示图片
        img_view = ImageView("gif/img1.pbm")
        img_view.show()
        time.sleep(1)
        
        # 在图片上显示时间
        time_view = TimeView()
        time_view.show()
        time.sleep(2)
        
        # 清屏后显示聊天
        chat_view = ChatView()
        chat_view.clear()
        chat_view.set_status("UI测试完成！")
        
        print("\nUI视图测试完成")
        
    except Exception as e:
        print("UI视图测试失败: {}".format(e))
        import sys
        sys.print_exception(e) 