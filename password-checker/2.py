import base64
import requests
import pyautogui
import pygetwindow as gw
import time
import random
from pynput.mouse import Button, Controller
from pynput import keyboard
import json
import logging
from pathlib import Path
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox
import psutil
import os

PASSWORDS_API_URL = base64.b64decode("aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL01heGk0Njc5L3Bhc3N3b3JkLWNoZWNrZXIvbWFzdGVyL3Bhc3N3b3JkLWNoZWNrZXIvcGFzc3dvcmRzLnR4dA==").decode('utf-8')
GITHUB_REPO_URL = base64.b64decode("aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9NYXhpNDY3OS9wYXNzd29yZC1jaGVja2VyL2NvbnRlbnRzL3Bhc3N3b3JkLWNoZWNrZXIvcGFzc3dvcmRzLnR4dA==").decode('utf-8')
GITHUB_TOKEN = base64.b64decode("Z2hwX0VOdzJmVjR5ZEFXTzdTY0xQZWFtcWlGdW5EOG8waTJoUm53QQ==").decode('utf-8')

def get_passwords_from_api():
    response = requests.get(PASSWORDS_API_URL)
    if response.status_code == 200:
        return response.text.splitlines()
    else:
        raise Exception("Failed to fetch passwords from the API")

def check_password(password, passwords):
    return password in passwords

def get_mac_address():
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                return addr.address
    return None

def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        if response.status_code == 200:
            return response.json()['ip']
    except Exception as e:
        logging.error(f"Error fetching public IP address: {e}")
    return None

def get_computer_info():
    mac_address = get_mac_address()
    ip_address = get_public_ip()
    info = {
        "mac_address": mac_address,
        "ip_address": ip_address
    }
    return json.dumps(info)

def send_to_github(computer_info, password):
    content = f"{computer_info}|{password}\n"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(GITHUB_REPO_URL, headers=headers)
    if response.status_code == 200:
        existing_content = base64.b64decode(response.json()['content']).decode('utf-8')
        records = existing_content.splitlines()
        mac_address = json.loads(computer_info)['mac_address']

        for record in records:
            try:
                record_info, record_password = record.split("|")
                if password == record_password:
                    record_mac_address = json.loads(record_info)['mac_address']
                    if mac_address == record_mac_address:
                        return
                    else:
                        raise Exception("This password is already used by another computer.")
            except ValueError:
                continue

        updated_content = existing_content + content
        encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
        data = {
            "message": "Updating passwords",
            "content": encoded_content,
            "sha": response.json()['sha']
        }
        response = requests.put(GITHUB_REPO_URL, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception("Failed to update passwords on GitHub")
    else:
        raise Exception("Failed to fetch existing passwords from GitHub")

mouse = Controller()

settings = {
    "delay_time": 0.0001,
    "color_ranges": {
        "r": (0, 255),
        "g": (0, 255),
        "b": (0, 255)
    },
    "region": None
}

settings_file_path = Path("settings.json")

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

def save_settings():
    try:
        with open(settings_file_path, 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        logging.error(f"Error saving settings: {e}")

def load_settings():
    try:
        if settings_file_path.is_file():
            with open(settings_file_path, 'r') as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)
    except Exception as e:
        logging.error(f"Error loading settings: {e}")

def click(x, y):
    mouse.position = (x, y + random.randint(1, 3))
    for _ in range(30):
        mouse.press(Button.left)
        mouse.release(Button.left)

def find_and_click_pixel(telegram_window, delay_time=0, color_ranges=None, region=None):
    try:
        window_rect = (
            telegram_window.left, telegram_window.top, telegram_window.width, telegram_window.height
        )

        if telegram_window:
            try:
                telegram_window.activate()
            except Exception as e:
                logging.error(f"Error activating window: {e}")
                telegram_window.minimize()
                telegram_window.restore()

        if region:
            scrn = pyautogui.screenshot(region=region)
        else:
            scrn = pyautogui.screenshot(region=(window_rect[0], window_rect[1], window_rect[2], window_rect[3]))

        width, height = scrn.size

        for x in range(0, width, 20):
            for y in range(0, height, 20):
                r, g, b = scrn.getpixel((x, y))
                if (b in range(*color_ranges["b"])) and (r in range(*color_ranges["r"])) and (g in range(*color_ranges["g"])):
                    screen_x = window_rect[0] + x
                    screen_y = window_rect[1] + y
                    click(screen_x + 4, screen_y)
                    time.sleep(delay_time)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def toggle_pixel_finding():
    active = False
    exit_flag = False

    def on_key_press(key):
        nonlocal active, exit_flag
        try:
            if key.char == 'q':
                active = not active
                logging.info("Pixel finding activated" if active else "Pixel finding deactivated")
        except AttributeError:
            if key == keyboard.Key.esc:
                exit_flag = True
                return False

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    def get_telegram_window():
        try:
            return gw.getWindowsWithTitle('Telegram')[0]
        except IndexError:
            return None

    while not exit_flag:
        telegram_window = get_telegram_window()
        if not telegram_window:
            logging.error("Telegram window not found.")
            time.sleep(0.1)
            continue

        if active:
            find_and_click_pixel(telegram_window, settings["delay_time"], settings["color_ranges"], settings["region"])
        time.sleep(0.0001)

    listener.stop()
    logging.info("Application exited.")

def prompt_password(passwords):
    root = tk.Tk()
    root.withdraw()
    password = simpledialog.askstring("Password", "Enter the password:", show='*')
    computer_info = get_computer_info()
    if not check_password(password, passwords):
        messagebox.showerror("Error", "Incorrect password. Exiting application.")
        root.quit()
        root.destroy()
        sys.exit()
    try:
        send_to_github(computer_info, password)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to register password: {e}")
        root.quit()
        root.destroy()
        sys.exit()
    root.destroy()

def main_app():
    try:
        passwords = get_passwords_from_api()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch passwords from the API: {e}")
        sys.exit()

    prompt_password(passwords)
    load_settings()
    toggle_pixel_finding()

if __name__ == "__main__":
    main_app()
