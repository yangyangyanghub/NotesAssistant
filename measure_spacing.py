"""测量右侧收藏列表中相邻卡片的 Y 坐标间距"""
import subprocess
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 50)
print("测量收藏卡片间距")
print("=" * 50)
print()
print("操作步骤：")
print("1. 确保微信收藏夹已打开")
print("2. 将鼠标移到【第一条收藏】卡片中心")
print("3. 按 Enter")
print("4. 将鼠标移到【第二条收藏】卡片中心")
print("5. 按 Enter")
print()

try:
    input("移好鼠标到第一条收藏后，按 Enter...")
    import pyautogui
    import time
    pos1 = pyautogui.position()
    print(f"  第一条 = X={pos1.x}, Y={pos1.y}")
    
    input("移好鼠标到第二条收藏后，按 Enter...")
    pos2 = pyautogui.position()
    print(f"  第二条 = X={pos2.x}, Y={pos2.y}")
    
    diff = pos2.y - pos1.y
    print()
    print(f"卡片间距: {diff} 像素")
    print(f"第一条 X = {pos1.x}")
    print(f"第一条 Y = {pos1.y}")
    print()
    print(f"请将以下坐标更新到配置中:")
    print(f"  FIRST_ITEM_X = {pos1.x}")
    print(f"  FIRST_ITEM_Y = {pos1.y}")
    print(f"  ITEM_HEIGHT = {diff}")
    print("=" * 50)

except Exception as e:
    print(f"错误: {e}")
