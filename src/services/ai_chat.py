import json
import logging
import gc
import requests
from config import XF_APIKey, XF_APISecret, XF_AI_MODEL
from utils import timeit


class AIChat:
    """AI聊天服务"""
    
    def __init__(self, model=None):
        self.model = model or XF_AI_MODEL
        self.api_key = XF_APIKey
        self.api_secret = XF_APISecret
        self.url = "https://spark-api-open.xf-yun.com/v1/chat/completions"
        
        # 请求头
        self.headers = {
            "Authorization": "Bearer {}:{}".format(self.api_key, self.api_secret),
            "Content-Type": "application/json",
        }
        
        # 基础消息模板
        self.messages = [
            {
                "role": "system",
                "content": "你是一个智能助手,请用最简洁的语言回答我",
            },
            {"role": "user", "content": ""},
        ]
    
    @timeit
    def chat(self, message, stream=False):
        """发送聊天请求"""
        if not message:
            return "请说点什么吧"
        
        # 构建请求数据
        self.messages[1]['content'] = message
        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": stream,
        }
        
        try:
            # 发送请求
            response = self._send_request(payload)
            if response:
                return self._parse_response(response)
            else:
                return "抱歉，我没有理解你的问题"
                
        except Exception as e:
            logging.error("AI聊天错误: {}".format(e))
            return "抱歉，出现了一些问题"
        finally:
            gc.collect()
    
    def _send_request(self, payload):
        """发送HTTP请求"""
        try:
            data = json.dumps(payload).encode('utf-8')
            response = requests.post(
                self.url, 
                headers=self.headers, 
                data=data, 
                stream=False
            )
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            logging.error("请求发送失败: {}".format(e))
            return None
    
    def _parse_response(self, response_text):
        """解析响应"""
        try:
            data = json.loads(response_text)
            
            # 检查错误
            if 'error' in data:
                logging.error("API错误: {}".format(data['error']))
                return "服务暂时不可用"
            
            # 提取回复
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            else:
                return "没有收到有效回复"
                
        except json.JSONDecodeError:
            logging.error("响应解析失败")
            return "响应格式错误"
    
    def set_system_prompt(self, prompt):
        """设置系统提示"""
        self.messages[0]['content'] = prompt
    
    def clear_context(self):
        """清除上下文"""
        self.messages = self.messages[:2]
        gc.collect()


# 模块级单例实例
ai_chat = AIChat() 


# 测试代码
if __name__ == "__main__":
    import time
    import gc
    
    print("=== AI聊天服务测试 ===")
    
    try:
        # 确保已连接网络
        from services.network import network_manager
        network = network_manager
        if not network.is_connected:
            print("正在连接网络...")
            if not network.connect():
                print("网络连接失败，无法测试AI服务")
                exit()
        
        chat_service = ai_chat
        
        # 测试1：基础对话测试
        print("\n1. 基础对话测试...")
        test_questions = [
            "你好",
            "今天天气怎么样",
            "1+1等于几",
            "给我讲个笑话",
        ]
        
        for question in test_questions:
            print("\n问: {}".format(question))
            start_time = time.ticks_ms()
            
            answer = chat_service.chat(question)
            
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            print("答: {}".format(answer))
            print("响应时间: {}ms".format(elapsed))
            print("内存使用: {} KB".format(gc.mem_alloc() // 1024))
            
            time.sleep(1)  # 避免请求过快
        
        # 测试2：系统提示测试
        print("\n2. 系统提示测试...")
        chat_service.set_system_prompt("你是一个专业的数学老师，请用简单的语言解释数学概念")
        
        math_question = "什么是质数？"
        print("\n问: {}".format(math_question))
        answer = chat_service.chat(math_question)
        print("答: {}".format(answer))
        
        # 恢复默认提示
        chat_service.set_system_prompt("你是一个智能助手,请用最简洁的语言回答我")
        
        # 测试3：错误处理测试
        print("\n3. 错误处理测试...")
        
        # 测试空消息
        print("测试空消息...")
        answer = chat_service.chat("")
        print("空消息回复: {}".format(answer))
        
        # 测试超长消息（如果需要）
        print("测试长消息...")
        long_message = "请用一句话回答：" + "测试" * 50
        answer = chat_service.chat(long_message)
        print("长消息回复: {}".format(answer[:50] + "..."))
        
        # 测试4：内存管理测试
        print("\n4. 内存管理测试...")
        print("清理前内存: {} KB".format(gc.mem_free() // 1024))
        chat_service.clear_context()
        gc.collect()
        print("清理后内存: {} KB".format(gc.mem_free() // 1024))
        
        print("\nAI聊天服务测试完成")
        
    except Exception as e:
        print("AI聊天服务测试失败: {}".format(e))
        import sys
        sys.print_exception(e) 