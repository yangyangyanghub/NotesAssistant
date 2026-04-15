"""测量微信收藏列表精确滚动一屏的距离"""
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 50)
print("测量滚动一屏的距离 (Scroll Distance)")
print("=" * 50)
print("\n操作步骤:")
print("1. 打开微信收藏夹，确保列表在初始位置（顶部）")
print("2. 将鼠标放在【收藏卡片列表】区域")
print("3. 按 Enter 记录基准位置")
print("4. 手动滚动一屏（让原本底部的卡片出现在顶部位置）")
print("   * 注意：尽量让某张卡片的顶端对齐上一屏某张卡片的顶端")
print("5. 将鼠标移到【刚才那张卡片的顶端】")
print("6. 按 Enter 记录结束位置")
print()

try:
    input("移好鼠标后，按 Enter...")
    import pyautogui
    pos1 = pyautogui.position()
    print(f"  起始位置 = Y={pos1.y}")
    
    input("\n滚好一屏，鼠标移好位置后，按 Enter...")
    pos2 = pyautogui.position()
    print(f"  结束位置 = Y={pos2.y}")
    
    diff = pos2.y - pos1.y
    print()
    print(f"计算结果:")
    print(f"  滚动一屏的精确距离: {diff} 像素")
    
    print("\n建议更新 auto_export.py 中的配置:")
    print(f"  # 如果 diff 与 ITEMS_PER_PAGE * ITEM_HEIGHT (7 * 130 = {7 * 130}) 差距较大")
    print(f"  # 可以在 main() 函数中调整 scroll 循环次数")
    print(f"  # 例如：for _ in range({int(1500 / 15)}):  # 假设每次滚 15 像素")
    
    print("=" * 50)

except Exception as e:
    print(f"错误: {e}")
