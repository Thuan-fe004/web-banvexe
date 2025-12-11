from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.config.config import Config
from tests.utils.helpers import Helpers

class BasePage:
    """Base class cho tất cả Page Objects"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, Config.EXPLICIT_WAIT)
    
    def open(self, url):
        """Mở URL"""
        self.driver.get(url)
    
    def find_element(self, locator):
        """Tìm element"""
        return self.driver.find_element(*locator)
    
    def find_elements(self, locator):
        """Tìm nhiều elements"""
        return self.driver.find_elements(*locator)
    
    def click(self, locator):
        """Click vào element"""
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()
    
    def type(self, locator, text):
        """Nhập text vào input"""
        element = self.wait.until(EC.presence_of_element_located(locator))
        element.clear()
        element.send_keys(text)
    
    def get_text(self, locator):
        """Lấy text của element"""
        element = self.wait.until(EC.presence_of_element_located(locator))
        return element.text
    
    def is_displayed(self, locator, timeout=5):
        """Kiểm tra element có hiển thị không"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False
    
    def get_current_url(self):
        """Lấy URL hiện tại"""
        return self.driver.current_url
    
    def take_screenshot(self, name):
        """Chụp screenshot"""
        return Helpers.take_screenshot(self.driver, name)