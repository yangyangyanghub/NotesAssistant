# wechat_favorites_exporter/calibrator.py
import json
import os
from dataclasses import dataclass

from wechat_favorites_exporter.config import CATEGORIES


@dataclass
class CalibrationData:
    category_start_pos: tuple[int, int]
    first_item_pos: tuple[int, int]
    list_bottom_pos: tuple[int, int]
    visible_count: int
    category_spacing: int = 56

    @property
    def list_area_height(self) -> int:
        return self.list_bottom_pos[1] - self.first_item_pos[1]

    @property
    def scroll_amount(self) -> int:
        return int(self.list_area_height * 0.8)

    @property
    def click_x(self) -> int:
        return self.first_item_pos[0]

    @property
    def click_y(self) -> int:
        return self.first_item_pos[1]


def save_calibration(data: CalibrationData, path: str) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    obj = {
        "category_start_pos": list(data.category_start_pos),
        "first_item_pos": list(data.first_item_pos),
        "list_bottom_pos": list(data.list_bottom_pos),
        "visible_count": data.visible_count,
        "category_spacing": data.category_spacing,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def load_calibration(path: str) -> CalibrationData | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return CalibrationData(
        category_start_pos=tuple(obj["category_start_pos"]),
        first_item_pos=tuple(obj["first_item_pos"]),
        list_bottom_pos=tuple(obj["list_bottom_pos"]),
        visible_count=obj["visible_count"],
        category_spacing=obj.get("category_spacing", 56),
    )


def compute_category_position(data: CalibrationData, category: str) -> tuple[int, int] | None:
    if category not in CATEGORIES:
        return None
    index = CATEGORIES.index(category)
    x = data.category_start_pos[0]
    y = data.category_start_pos[1] + index * data.category_spacing
    return (x, y)


def run_calibration() -> CalibrationData:
    import pyautogui
    print("\n=== 坐标校准 ===")
    print("请确保微信收藏夹页面已打开且可见（不要被其他窗口挡住）")
    print("校准时：先把鼠标移到指定位置，再切回终端按 Enter\n")

    print("步骤 1/4：请把鼠标移到左侧「全部收藏」文字上")
    print("         （注意是微信窗口里的，不是终端里的）")
    _wait_for_mouse_position()
    category_start_pos = pyautogui.position()
    print(f"  ✓ 记录: ({category_start_pos.x}, {category_start_pos.y})")

    print("\n步骤 2/4：请把鼠标移到右侧列表【第一条收藏】的中心位置")
    print("         （右侧大面积区域里最上面那条卡片的中间）")
    _wait_for_mouse_position()
    first_item_pos = pyautogui.position()
    print(f"  ✓ 记录: ({first_item_pos.x}, {first_item_pos.y})")

    print("\n步骤 3/4：请把鼠标移到右侧列表可见区域的【最底部边缘】")
    print("         （最后一条可见卡片的下边沿）")
    _wait_for_mouse_position()
    list_bottom_pos = pyautogui.position()
    print(f"  ✓ 记录: ({list_bottom_pos.x}, {list_bottom_pos.y})")

    visible_count = int(input("\n步骤 4/4：当前右侧列表里能看到几条收藏？请输入数字: "))

    data = CalibrationData(
        category_start_pos=(category_start_pos.x, category_start_pos.y),
        first_item_pos=(first_item_pos.x, first_item_pos.y),
        list_bottom_pos=(list_bottom_pos.x, list_bottom_pos.y),
        visible_count=visible_count,
    )

    # 校验合理性
    if data.list_area_height < 100:
        print(f"\n⚠ 警告：列表区域高度只有 {data.list_area_height}px，可能校准有误！")
        print("  第一条收藏 Y={}, 底部边缘 Y={}".format(first_item_pos.y, list_bottom_pos.y))
        print("  请确认步骤 2 和 3 指的是微信右侧列表区域，不是左侧分类栏")
        retry = input("  要重新校准吗？(y/n): ").strip().lower()
        if retry == "y":
            return run_calibration()

    print(f"\n校准完成！列表区域高度: {data.list_area_height}px, 每次滚动: {data.scroll_amount}px")
    return data


def _wait_for_mouse_position():
    """等待用户移动鼠标到目标位置后按 Enter。提示用户先移鼠标再回终端按键。"""
    import pyautogui
    input("         >>> 移好鼠标后，切回终端按 Enter <<<")
    # 给用户一小段时间确保鼠标在正确位置
    import time
    time.sleep(0.3)
