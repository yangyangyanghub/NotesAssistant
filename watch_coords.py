"""
实时鼠标坐标追踪 - 把鼠标移到目标位置，按 's' 键记录坐标
按 'q' 退出，坐标保存到 cal_coords.txt
"""
import pyautogui
import time
import keyboard

print("=== 微信坐标校准器 ===")
print("鼠标移动时，坐标会实时更新")
print("移到目标位置后，按 'S' 保存坐标，按 'Q' 退出\n")

log = []

print("开始追踪...\n")
try:
    while True:
        x, y = pyautogui.position()
        print(f"\rX={x:4d}  Y={y:4d}", end="", flush=True)
        
        if keyboard.is_pressed("s"):
            entry = f"({x}, {y})"
            log.append(entry)
            print(f"\n  [已保存 #{len(log)}] {entry}")
            time.sleep(1.5)
            
        if keyboard.is_pressed("q"):
            print("\n退出")
            break
            
        time.sleep(0.05)
except KeyboardInterrupt:
    pass

with open("cal_coords.txt", "w", encoding="utf-8") as f:
    for i, entry in enumerate(log, 1):
        f.write(f"记录 #{i}: {entry}\n")

print(f"\n已保存 {len(log)} 组坐标到 cal_coords.txt")
