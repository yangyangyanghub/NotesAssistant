# wechat_favorites_exporter/main.py
import argparse
import os
import sys
import time

import pyautogui

from wechat_favorites_exporter.calibrator import (
    CalibrationData,
    compute_category_position,
    load_calibration,
    run_calibration,
    save_calibration,
)
from wechat_favorites_exporter.config import (
    CATEGORIES,
    END_DETECTION_COUNT,
    OUTPUT_DIR,
    load_progress,
    random_delay,
    save_progress,
)
from wechat_favorites_exporter.content_extractor import (
    capture_window_screenshot,
    compute_image_hash,
    images_are_similar,
    ocr_extract_preview,
)
from wechat_favorites_exporter.exporter import export_one_item, should_skip
from wechat_favorites_exporter.window_manager import activate_wechat

pyautogui.FAILSAFE = True


def select_category() -> str:
    print("\n可用分类：")
    for i, cat in enumerate(CATEGORIES):
        print(f"  {i + 1}. {cat}")
    while True:
        choice = input("\n请输入分类编号: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(CATEGORIES):
                return CATEGORIES[idx]
        except ValueError:
            pass
        print("无效输入，请重试")


def main():
    parser = argparse.ArgumentParser(description="微信收藏夹批量导出工具")
    parser.add_argument("--category", type=str, help="指定分类")
    parser.add_argument("--resume", action="store_true", help="从上次中断位置继续")
    parser.add_argument("--recalibrate", action="store_true", help="强制重新校准")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR, help="导出目录")
    parser.add_argument("--delay", type=float, default=None, help="操作间隔秒数")
    args = parser.parse_args()

    output_dir = args.output_dir
    cal_path = os.path.join(output_dir, "calibration.json")
    progress_path = os.path.join(output_dir, "progress.json")

    category = args.category or select_category()
    if category not in CATEGORIES:
        print(f"错误：未知分类 '{category}'")
        sys.exit(1)

    category_dir = os.path.join(output_dir, category)
    os.makedirs(category_dir, exist_ok=True)

    cal = None
    if not args.recalibrate:
        cal = load_calibration(cal_path)
        if cal:
            use_existing = input(f"发现已有校准数据，是否使用？(y/n): ").strip().lower()
            if use_existing != "y":
                cal = None
    if cal is None:
        cal = run_calibration()
        save_calibration(cal, cal_path)

    start_index = 1
    if args.resume:
        progress = load_progress(progress_path)
        if progress and progress.get("category") == category:
            start_index = progress["last_completed_index"] + 1
            print(f"从第 {start_index} 条继续")

    activate_wechat()
    time.sleep(0.5)
    cat_pos = compute_category_position(cal, category)
    if cat_pos:
        pyautogui.click(cat_pos[0], cat_pos[1])
        time.sleep(1.0)

    if start_index > 1:
        print(f"跳过前 {start_index - 1} 条...")
        for _ in range(start_index - 1):
            pyautogui.scroll(-3)
            time.sleep(0.15)
        time.sleep(0.5)

    print(f"\n开始导出分类「{category}」...")
    index = start_index
    consecutive_end = 0
    prev_hash = None
    exported = 0
    skipped = 0
    failed = 0

    try:
        while True:
            list_bounds = (cal.click_x - 300, cal.click_y - 40, 600, 80)
            list_img = capture_window_screenshot(list_bounds)
            preview = ocr_extract_preview(list_img)

            if should_skip(index, preview, category_dir):
                print(f"  [{index}] 已导出，跳过")
                skipped += 1
            else:
                try:
                    meta = export_one_item(index, cal, category, category_dir, prev_hash)
                    if meta:
                        prev_hash = meta.get("image_hash")
                        status = "跳过详情" if meta.get("skipped_detail") else "OK"
                        if meta.get("open_failed"):
                            status = "打开失败(已截图)"
                            failed += 1
                        else:
                            exported += 1
                        title = meta.get("preview", {}).get("title", "")[:30]
                        print(f"  [{index}] {status} - {title}")

                        if prev_hash and images_are_similar(list_img, list_img):
                            consecutive_end += 1
                        else:
                            consecutive_end = 0

                        if consecutive_end >= END_DETECTION_COUNT:
                            print("\n检测到已到达列表末尾")
                            break
                except Exception as e:
                    print(f"  [{index}] 错误: {e}")
                    failed += 1

            save_progress({
                "category": category,
                "last_completed_index": index,
                "started_at": load_progress(progress_path).get("started_at", time.strftime("%Y-%m-%dT%H:%M:%S")) if load_progress(progress_path) else time.strftime("%Y-%m-%dT%H:%M:%S"),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }, progress_path)

            pyautogui.scroll(-3)
            random_delay()
            index += 1

    except KeyboardInterrupt:
        print("\n\n用户中断，进度已保存")
    except pyautogui.FailSafeException:
        print("\n\n安全停止（鼠标移到屏幕左上角），进度已保存")

    print(f"\n=== 导出完成 ===")
    print(f"分类: {category}")
    print(f"成功导出: {exported}")
    print(f"跳过(已导出): {skipped}")
    print(f"失败: {failed}")
    print(f"导出目录: {os.path.abspath(category_dir)}")


if __name__ == "__main__":
    main()
