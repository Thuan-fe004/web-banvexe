import os
import random
import string
from datetime import datetime
from faker import Faker
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.config.config import Config

fake = Faker(['vi_VN'])

class Helpers:
    """Helper functions cho test automation"""
    
    @staticmethod
    def take_screenshot(driver, name):
        """Chụp screenshot và lưu với timestamp"""
        os.makedirs(Config.SCREENSHOTS_PATH, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(Config.SCREENSHOTS_PATH, filename)
        driver.save_screenshot(filepath)
        print(f"📸 Screenshot saved: {filepath}")
        return filepath
    
    @staticmethod
    def wait_for_element(driver, locator, timeout=None):
        """Đợi element xuất hiện"""
        if timeout is None:
            timeout = Config.EXPLICIT_WAIT
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located(locator))
    
    @staticmethod
    def wait_for_element_clickable(driver, locator, timeout=None):
        """Đợi element có thể click được"""
        if timeout is None:
            timeout = Config.EXPLICIT_WAIT
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.element_to_be_clickable(locator))
    
    @staticmethod
    def generate_random_username(length=8):
        """Tạo username ngẫu nhiên"""
        return 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    @staticmethod
    def generate_random_email():
        """Tạo email ngẫu nhiên"""
        return fake.email()
    
    @staticmethod
    def generate_random_phone():
        """Tạo số điện thoại Việt Nam ngẫu nhiên (10 số)"""
        return '09' + ''.join(random.choices(string.digits, k=8))
    
    @staticmethod
    def generate_random_name():
        """Tạo tên tiếng Việt ngẫu nhiên"""
        return fake.name()
    
    @staticmethod
    def generate_random_address():
        """Tạo địa chỉ tiếng Việt ngẫu nhiên"""
        return fake.address()