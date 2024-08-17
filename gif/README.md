
# 可以通过使用 python3 的 pillow 库将图片转换为 pbm 格式，比如：

```python3
from PIL import Image

convert_type = "1"  #  1 为黑白图像，RGBA 为彩色图像
with Image.open("filename.png", "r") as img:
    # 调整图片大小 为80x80
    img = img.resize((80, 80), Image.ANTIALIAS)
    img = img.convert(convert_type)
    
    img.save("filename.pbm")
```