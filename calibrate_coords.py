#!/usr/bin/env python3
"""
快速坐标校准工具 - 用于获取 Windows 微信收藏夹的准确坐标
"""
import time
import pyautogui
from PIL import ImageGrab

print("=" * 50)
print("Windows 微信收藏夹坐标校准")
print("=" * 50)
print()
print("步骤:")
print("1. 确保微信已打开，且收藏夹页面可见")
print("2. 将鼠标移到右侧列表【第一条收藏】的中心")
print("3. 回到此窗口按 Enter 记录坐标")
print()

input("移好鼠标后，按 Enter 记录第一条收藏坐标...")
time.sleep(0.3)
pos = pyautogui.position()
print(f"  第一条收藏坐标: ({pos.x}, {pos.y})")

print()
print("4. 将鼠标移到左侧【全部收藏】文字上")
print("5. 回到此窗口按 Enter 记录坐标")
print()

input("移好鼠标后，按 Enter 记录全部收藏坐标...")
time.sleep(0.3)
cat_pos = pyautogui.position()
print(f"  全部收藏坐标: ({cat_pos.x}, {cat_pos.y})")

print()
print("5. 用截图确认坐标是否正确")
print("   截图将显示第一条收藏的位置...")
time.sleep(1)

# 截取目标区域
x, y = pos.x, pos.y
screenshot = pyautogui.screenshot(region=(x - 100, y - 30, 300, 80))
screenshot.save("calibration_preview.png")
print(f"  截图已保存到 calibration_preview.png")

print()
print("=" * 50)
print("校准结果")
print("=" * 50)
print(f"ITEM_X = {pos.x}")
print(f"ITEM_Y = {pos.y}")
print(f"LIST_AREA_X = {cat_pos.x}")
print(f"LIST_AREA_Y = {cat_pos.y}")
print()
print("请将以上坐标更新到 auto_export.py 中替换")
print("=" * 50)
