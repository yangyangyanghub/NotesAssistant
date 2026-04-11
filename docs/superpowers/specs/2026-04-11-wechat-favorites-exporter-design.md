# WeChat Favorites Exporter - macOS 设计文档

## 概述

基于 pyautogui + AppleScript 的 macOS 微信收藏夹批量导出工具。通过 UI 自动化模拟操作，逐条打开收藏内容，截图保存并尝试提取文本/链接，支持按分类批处理和断点续传。

## 目标环境

- macOS (Darwin)
- 微信 Mac 4.x
- Python 3.10+

## 项目结构

```
wechat_favorites_exporter/
├── main.py              # 入口，命令行参数解析
├── calibrator.py         # 坐标校准模块
├── exporter.py           # 主导出流程控制
├── window_manager.py     # AppleScript 窗口管理
├── content_extractor.py  # 文本/链接提取
├── config.py             # 配置和状态持久化
├── progress.json         # 断点续传状态文件（运行时生成）
├── calibration.json      # 校准数据（运行时生成）
└── output/               # 导出结果目录
    ├── 链接/
    │   ├── 001/
    │   │   ├── screenshot.png
    │   │   ├── content.txt
    │   │   └── meta.json
    │   └── 002/
    └── 笔记/
        └── ...
```

## 核心流程

```
启动 → 选择分类（全部收藏/链接/笔记/文件/...）
  → 校准（或加载已有校准数据）
  → 检查 progress.json，询问是否从上次中断位置继续
  → 如需恢复：智能跳过已导出条目（见优化 4）
  → 循环：
      1. 【优化 1：列表预览提取】
         对列表最顶部可见条目区域截图 → OCR 提取预览信息（标题、来源、日期、类型标识）
         → 写入 meta.json 的 preview 字段
         → 判断类型：
           - 纯文字笔记且预览内容已完整 → 仅保存列表截图，跳到步骤 9
           - 其他类型 → 继续步骤 2 打开详情
      2. 点击列表最顶部可见条目
      3. AppleScript 检测新窗口弹出（超时 5 秒）
         - 弹窗成功：继续步骤 4
         - 超时未弹窗：对列表区域截图作为 fallback，记录 open_failed，跳到步骤 9
      4. 等待内容加载（随机延时，见优化 3）
      5. AppleScript 获取新窗口坐标和尺寸
      6. 【优化 2：详情长截图】
         对新窗口区域截图 → 保存 screenshot_001.png
         → 在详情窗口内滚动 → 截图 screenshot_002.png
         → 重复直到连续 2 次截图底部区域相似（滚不动了）
         → 拼接所有截图为 screenshot.png
      7. Cmd+A → Cmd+C 尝试提取文本 → 保存 content.txt
      8. 从文本中正则提取 URL → 写入 meta.json
      9. 关闭新窗口（AppleScript，如果打开了的话）
      10. 图像去重校验：与上一条截图做像素差异比较
          - 如果差异过小（可能是同一条）：多滚动一些，重试
      11. 更新 progress.json（当前序号 +1）
      12. 【优化 3：随机化延时】
          向下滚动（列表可见区域高度的 ~80%），下一条移至顶部
          随机等待 max(0.8, gauss(1.5, 0.3)) 秒
      13. 终止检测：连续 3 次截图高度相似 → 判定到达末尾
  → 完成，输出统计信息
```

## 模块设计

### 1. calibrator.py - 坐标校准

**校准流程（4 步）：**

1. "请把鼠标移到左侧分类栏第一个分类（全部收藏）的位置，按 Enter"
   → 记录 `category_start_pos`，后续分类按 Y 轴偏移推算
2. "请把鼠标移到右侧列表第一条收藏的中心，按 Enter"
   → 记录 `first_item_pos`
3. "请把鼠标移到右侧列表可见区域的底部边缘，按 Enter"
   → 记录 `list_bottom_pos`
4. "当前可见几条收藏？请输入数字"
   → 记录 `visible_count`

**计算：**
- `list_area_height = list_bottom_pos.y - first_item_pos.y`
- `scroll_amount = list_area_height * 0.8`（每次滚动量）
- `click_x = first_item_pos.x`（点击的 X 坐标固定）
- `click_y = first_item_pos.y`（始终点击最顶部条目位置）

**分类坐标推算：**
左侧分类列表按固定间距排列，从截图观察约 56px 间距。分类映射：
```python
CATEGORIES = ["全部收藏", "最近使用", "链接", "图片与视频", "笔记", "文件", "聊天记录", "位置", "小程序"]
```
每个分类的 Y 坐标 = `category_start_pos.y + index * category_spacing`

**持久化：** 保存到 `calibration.json`，下次启动可复用，提示"是否使用上次校准数据？(y/n)"

### 2. window_manager.py - AppleScript 窗口管理

通过 `subprocess.run(["osascript", "-e", script])` 调用 AppleScript。

**核心功能：**

```python
def get_wechat_window_count() -> int:
    """获取微信当前窗口数量"""
    # tell application "System Events" to tell process "WeChat"
    #   count of windows
    # end tell

def wait_for_new_window(original_count: int, timeout: float = 5.0) -> bool:
    """等待新窗口弹出，返回是否成功"""
    # 轮询检查窗口数 > original_count

def get_front_window_bounds() -> tuple[int, int, int, int]:
    """获取最前面窗口的坐标和尺寸 (x, y, width, height)"""
    # tell application "System Events" to tell process "WeChat"
    #   get {position, size} of front window
    # end tell

def close_front_window():
    """关闭最前面的窗口"""
    # tell application "System Events" to tell process "WeChat"
    #   click button 1 of front window  -- 关闭按钮
    # end tell
    # 或者用 Cmd+W

def activate_wechat():
    """将微信带到前台"""
    # tell application "WeChat" to activate
```

### 3. content_extractor.py - 内容提取

```python
def extract_text_from_active_window() -> str | None:
    """Cmd+A → Cmd+C → 读取剪贴板"""
    # pyautogui.hotkey('command', 'a')
    # pyautogui.hotkey('command', 'c')
    # 使用 subprocess pbpaste 或 pyperclip 读取剪贴板

def extract_urls(text: str) -> list[str]:
    """正则从文本中提取 URL"""
    # 匹配 http/https 开头的 URL

def capture_window_screenshot(bounds: tuple) -> Image:
    """截取指定区域的屏幕截图"""
    # PIL.ImageGrab.grab(bbox=bounds)，比 pyautogui.screenshot 更精确

def capture_long_screenshot(bounds: tuple, scroll_func) -> Image:
    """【优化 2】详情窗口长截图：滚动 + 截图 + 拼接"""
    # 1. 截取第一屏
    # 2. 在详情窗口内滚动一屏高度的 80%
    # 3. 截取下一屏
    # 4. 检测底部区域是否与上一屏相似（连续 2 次相似 = 到底）
    # 5. 裁剪重叠区域，垂直拼接所有截图
    # 返回拼接后的完整长图

def ocr_extract_preview(image: Image) -> dict:
    """【优化 1】OCR 提取列表预览信息"""
    # 使用 pytesseract 或 macOS Vision framework 识别截图中的文字
    # 返回 {"title": "...", "source": "...", "date": "...", "type_hint": "..."}

def compute_image_hash(image: Image) -> str:
    """计算图片的感知哈希，用于去重比较"""
    # 缩小到 8x8 灰度图，计算均值哈希

def is_preview_sufficient(preview: dict) -> bool:
    """【优化 1】判断预览信息是否足够，不需要打开详情"""
    # 纯文字笔记且内容短 → True
    # 链接/文件/图片/视频 → False
```

### 4. config.py - 配置与状态

```python
# 可调参数
CLICK_DELAY_MEAN = 1.5   # 【优化 3】点击后等待时间均值（秒）
CLICK_DELAY_STD = 0.3    # 【优化 3】点击后等待时间标准差（秒）
CLICK_DELAY_MIN = 0.8    # 【优化 3】最小延时（秒）
SCROLL_DELAY = 0.5       # 滚动后等待时间（秒）
WINDOW_TIMEOUT = 5.0     # 等待新窗口超时（秒）
DUPLICATE_THRESHOLD = 5  # 图像差异阈值（低于此值视为重复）
END_DETECTION_COUNT = 3  # 连续重复 N 次判定到达末尾
LONG_SCREENSHOT_OVERLAP = 0.2  # 【优化 2】长截图重叠比例
OUTPUT_DIR = "output"
```

```python
# 【优化 3】随机延时函数
def random_delay():
    """正态分布随机延时，模拟人工操作节奏"""
    delay = max(CLICK_DELAY_MIN, random.gauss(CLICK_DELAY_MEAN, CLICK_DELAY_STD))
    time.sleep(delay)
```

**progress.json 结构：**
```json
{
  "category": "链接",
  "last_completed_index": 42,
  "started_at": "2026-04-11T10:00:00",
  "updated_at": "2026-04-11T10:35:00"
}
```

**meta.json 结构（每条收藏）：**
```json
{
  "index": 1,
  "category": "链接",
  "timestamp": "2026-04-11T10:01:23",
  "has_text": true,
  "urls": ["https://example.com/..."],
  "open_failed": false,
  "skipped_detail": false,
  "preview": {
    "title": "OpenClaw Token Optimization Guide",
    "source": "撕考者",
    "date": "3月4日",
    "type_hint": "DOCX 29.0KB"
  },
  "error": null,
  "image_hash": "a1b2c3d4e5f6",
  "screenshot_pages": 1
}
```

### 5. main.py - 命令行入口

```
用法：python main.py [选项]

选项：
  --category TEXT    指定分类（默认交互式选择）
  --resume           从上次中断位置继续
  --recalibrate      强制重新校准
  --output-dir PATH  导出目录（默认 ./output）
  --delay FLOAT      操作间隔秒数（默认 1.5）
```

### 6. exporter.py - 主流程控制

整合以上模块的主循环逻辑。核心是一个 `export_category(category: str)` 方法，执行"核心流程"中描述的循环。

**【优化 6：智能跳过已导出】恢复逻辑：**

断点续传恢复时，不仅靠序号定位，还比对列表预览内容：

```python
def should_skip(index: int, preview: dict, output_dir: str) -> bool:
    """判断当前条目是否已导出，应跳过"""
    item_dir = os.path.join(output_dir, f"{index:03d}")
    if not os.path.exists(item_dir):
        return False
    meta_path = os.path.join(item_dir, "meta.json")
    if not os.path.exists(meta_path):
        return False
    existing_meta = json.load(open(meta_path))
    # 比对预览标题+日期，防止因滚动偏移导致序号错位
    return (existing_meta.get("preview", {}).get("title") == preview.get("title")
            and existing_meta.get("preview", {}).get("date") == preview.get("date"))
```

恢复流程：
1. 从列表顶部开始，快速滚动
2. 每滚动一次，OCR 读取顶部条目预览
3. 与已导出的 meta.json 比对
4. 找到第一个未导出的条目后，开始正常处理

## 安全机制

1. **紧急停止**：`pyautogui.FAILSAFE = True`（鼠标移到屏幕左上角触发 FailSafeException）
2. **键盘中断**：监听 Esc 键，优雅退出并保存进度
3. **操作间隔**：每条之间 1.5-2 秒延时
4. **单条容错**：任何一条处理失败不中断整体流程，记录错误到 meta.json

## 优化总结

| 编号 | 优化项 | 说明 | 影响 |
|------|--------|------|------|
| 优化 1 | 先读列表再决定是否打开 | OCR 提取预览信息，纯文字笔记可跳过打开详情 | 预估减少 30-40% 处理时间 |
| 优化 2 | 详情长截图 | 详情窗口内滚动+截图+拼接，确保长内容完整导出 | 完整性提升 |
| 优化 3 | 随机化延时 | 正态分布随机延时，模拟人工操作节奏 | 安全性提升 |
| 优化 6 | 智能跳过已导出 | 恢复时比对预览标题+日期，防止序号错位导致重复 | 可靠性提升 |

## 依赖

```
pyautogui
Pillow
pyperclip
pytesseract        # 优化 1：OCR 提取列表预览（或使用 macOS Vision framework）
```

## 使用流程

1. `pip install pyautogui Pillow pyperclip`
2. macOS 系统设置 → 隐私与安全 → 辅助功能 → 允许终端/Python 控制电脑
3. 打开微信，进入收藏夹页面
4. `python main.py`
5. 按提示完成校准
6. 选择分类，开始导出
7. 导出完成后在 `output/` 目录查看结果
