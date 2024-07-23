from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Listener as KeyboardListener, Key, KeyCode
import threading
import time
import configparser
import os
import sys

mouse = MouseController()
keyboard = KeyboardController()

# 热键
toggle_hotkey = KeyCode(char='b')
position_hotkey = Key.f8
press_time_hotkey = Key.f6
interval_time_hotkey = Key.f7

# 是否运行
running = False
# 鼠标当前位置
initial_mouse_position = None
# 控制检测
detection_thread = None
# 定位模式
positioning = False

# 默认时间ms
default_press_time = 30
default_interval_time = 50

# 配置文件
def get_config_path():
    if getattr(sys, 'frozen', False):  # 是否打包
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(application_path, 'config.ini')

config_file = get_config_path()

# 读取配置
config = configparser.ConfigParser()
if os.path.exists(config_file):
    config.read(config_file)
    user_x = int(config['DEFAULT'].get('x', '1250'))
    user_y = int(config['DEFAULT'].get('y', '1030'))
    press_time = int(config['DEFAULT'].get('press_time', default_press_time))
    interval_time = int(config['DEFAULT'].get('interval_time', default_interval_time))
else:
    # 默认
    user_x = 1250
    user_y = 1030
    press_time = default_press_time
    interval_time = default_interval_time

    # 先保存默认设置到配置文件
    config['DEFAULT'] = {
        'x': str(user_x),
        'y': str(user_y),
        'press_time': str(press_time),
        'interval_time': str(interval_time)
    }
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def perform_actions():
    global running, press_time, interval_time
    keys = ['w', 'a', 's', 'd']
    while running:
        mouse.click(Button.left, 1)  # 单击
        for key in keys:
            # 读取配置
            press_time = int(config['DEFAULT'].get('press_time', default_press_time))
            interval_time = int(config['DEFAULT'].get('interval_time', default_interval_time))
            keyboard.press(key)
            time.sleep(press_time / 1000)  # 按下时间
            keyboard.release(key)
            time.sleep(interval_time / 1000)  # 间隔时间

def toggle(key):
    global running, initial_mouse_position, detection_thread
    if key == toggle_hotkey:
        if not running:
            running = True
            # 移动鼠标到指定位置
            mouse.position = (user_x, user_y)
            t = threading.Thread(target=perform_actions)
            t.start()
            print("start")
            # 延迟1s检测鼠标移动
            detection_thread = threading.Thread(target=start_detection)
            detection_thread.start()
        else:
            running = False
            print("stop")

def handle_positioning(key):
    global user_x, user_y, positioning
    if key == position_hotkey:
        if not positioning:
            # 定位
            positioning = True
            print("开始定位")
            detection_thread = threading.Thread(target=detect_position)
            detection_thread.start()
        else:
            # 保存位置
            positioning = False
            print(f"已保存新位置: ({user_x}, {user_y})")
            config['DEFAULT'] = {
                'x': str(user_x),
                'y': str(user_y),
                'press_time': str(press_time),
                'interval_time': str(interval_time)
            }
            with open(config_file, 'w') as configfile:
                config.write(configfile)

def detect_position():
    global user_x, user_y
    while positioning:
        current_position = mouse.position
        user_x, user_y = current_position
        print(f"当前鼠标位置: {current_position}")
        time.sleep(0.1)  # 100毫秒更新一次位置

def clear_input_buffer():
    import msvcrt
    while msvcrt.kbhit():
        msvcrt.getch()

def update_press_time():
    global press_time
    def get_input():
        global press_time
        clear_input_buffer()
        try:
            new_press_time = input("按下时间 (毫秒): ").strip()
            if new_press_time:
                press_time = int(new_press_time)
            config['DEFAULT']['press_time'] = str(press_time)
            with open(config_file, 'w') as configfile:
                config.write(configfile)
            print(f"新设置已保存: 按下时间={press_time}毫秒")
        except ValueError:
            print("输入无效，使用当前设置")
    input_thread = threading.Thread(target=get_input)
    input_thread.start()

def update_interval_time():
    global interval_time
    def get_input():
        global interval_time
        clear_input_buffer()
        try:
            new_interval_time = input("间隔时间 (毫秒): ").strip()
            if new_interval_time:
                interval_time = int(new_interval_time)
            config['DEFAULT']['interval_time'] = str(interval_time)
            with open(config_file, 'w') as configfile:
                config.write(configfile)
            print(f"新设置已保存: 间隔时间={interval_time}毫秒")
        except ValueError:
            print("输入无效，使用当前设置")
    input_thread = threading.Thread(target=get_input)
    input_thread.start()

def start_detection():
    global running, initial_mouse_position
    time.sleep(1)  # 延迟1s
    initial_mouse_position = mouse.position  # 更新初始鼠标位置
    print(f"开始检测鼠标位置: {initial_mouse_position}")
    while running:
        current_position = mouse.position
        # 鼠标移动距离
        distance = ((current_position[0] - initial_mouse_position[0]) ** 2 +
                    (current_position[1] - initial_mouse_position[1]) ** 2) ** 0.5
        # 移动距离大于阈值就停止
        if distance > 15:
            running = False
            print(f"鼠标移动停止执行. 距离: {distance:.2f}")
            break
        time.sleep(0.05)  # 50毫秒检查一次

# 热键监听
def on_press(key):
    try:
        if key == toggle_hotkey:
            toggle(key)
        elif key == position_hotkey:
            handle_positioning(key)
        elif key == press_time_hotkey:
            update_press_time()
        elif key == interval_time_hotkey:
            update_interval_time()
    except AttributeError:
        print(f"无法识别的键: {key}")

# 启动键盘监听
keyboard_listener = KeyboardListener(on_press=on_press)
keyboard_listener.start()

print(f" 先进入游戏确定回城位置")
print(f" F8定位回城位置，第一次按下开始定位，确定位置后再次按F8\n")
print(f" F6设置按键按下时间，默认30ms，一般不用改\n")
print(f" F7设置按键间隔时间，默认50ms，间隔越短成功率越大\n")
print(f" 短时间内输出大量按键信息可能会导致游戏崩溃")
print(f" 短时间内输出大量按键信息可能会导致游戏崩溃")
print(f" 短时间内输出大量按键信息可能会导致游戏崩溃\n")
print(f" B键启动，移动鼠标自动停止")
keyboard_listener.join()
