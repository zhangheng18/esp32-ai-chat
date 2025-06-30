# 服务层
from .network import network_manager
from .ai_chat import ai_chat
from .speech_recognition import speech_recognition
from .text_to_speech import text_to_speech

__all__ = [
    'network_manager',
    'ai_chat', 
    'speech_recognition',
    'text_to_speech'
] 