"""测量收藏详情页顶部导航栏按钮坐标"""
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 50)
print("测量收藏详情页「...」按钮坐标")
print("=" * 50)
print("\n操作步骤:\n")
print("1. 打开任意一条收藏，进入详情页")
print("2. 将鼠标移到右上角「...」三个点上，按 Enter")
print("3. 点击「...」弹出菜单后")
print("4. 将鼠标移到「复制链接」上，按 Enter")
print()

try:
    input("移好鼠标到「...」按钮后，按 Enter...")
    import pyautogui
    pos1 = pyautogui.position()
    print(f"  「...」= X={pos1.x}, Y={pos1.y}")
    
    input("点击「...」，然后把鼠标移到「复制链接」上，按 Enter...")
    pos2 = pyautogui.position()
    print(f"  「复制链接」= X={pos2.x}, Y={pos2.y}")
    
    print("\n" + "=" * 50)
    print("测量结果:")
    print(f"  三点按钮: ({pos1.x}, {pos1.y})")
    print(f"  复制链接: ({pos2.x}, {pos2.y})")
    print("=" * 50)
    
except Exception as e:
    print(f"错误: {e}")
