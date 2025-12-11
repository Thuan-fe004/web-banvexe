from selenium.webdriver.common.by import By
from tests.page_objects.base_page import BasePage
from tests.config.config import Config

class LoginPageLocators:
    """Locators cho Login Page"""
    # Form fields
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    
    # Buttons
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    
    # Links
    REGISTER_LINK = (By.CSS_SELECTOR, ".register-link a")
    
    # Bằng 2 dòng này (hỗ trợ mọi kiểu flash message):
    ALERT_SUCCESS = (By.XPATH, "//*[contains(@class,'alert') and contains(@class,'success')] | //div[contains(text(),'thành công')] | //div[@role='alert' and contains(.,'thành công')]")
    ALERT_DANGER = (By.XPATH, "//*[contains(@class,'alert') and contains(@class,'danger')] | //*[contains(@class,'alert') and contains(@class,'error')] | //div[@role='alert' and contains(.,'lỗi')] | //div[contains(@class,'text-danger')]")
        
    # Headers
    PAGE_TITLE = (By.CSS_SELECTOR, ".header h2")
    BUS_ICON = (By.CSS_SELECTOR, ".bus-icon")

class LoginPage(BasePage):
    """Page Object cho Login Page"""
    
    def __init__(self, driver):
        super().__init__(driver)
        self.url = Config.get_url("/login")
    
    def open_login_page(self):
        """Mở trang đăng nhập"""
        self.open(self.url)
    
    def fill_username(self, username):
        """Nhập username"""
        self.type(LoginPageLocators.USERNAME_INPUT, username)
    
    def fill_password(self, password):
        """Nhập password"""
        self.type(LoginPageLocators.PASSWORD_INPUT, password)
    
    def click_login_button(self):
        """Click nút đăng nhập"""
        self.click(LoginPageLocators.LOGIN_BUTTON)
    
    def click_register_link(self):
        """Click link đăng ký"""
        self.click(LoginPageLocators.REGISTER_LINK)
    
    def login(self, username, password):
        """Thực hiện đăng nhập (shortcut method)"""
        self.fill_username(username)
        self.fill_password(password)
        self.click_login_button()
    
    def get_success_message(self):
        """Lấy thông báo thành công"""
        if self.is_displayed(LoginPageLocators.ALERT_SUCCESS):
            return self.get_text(LoginPageLocators.ALERT_SUCCESS)
        return None
    
    def get_error_message(self):
        """Lấy thông báo lỗi"""
        if self.is_displayed(LoginPageLocators.ALERT_DANGER):
            return self.get_text(LoginPageLocators.ALERT_DANGER)
        return None
    
    def is_on_login_page(self):
        """Kiểm tra đang ở trang login"""
        return self.is_displayed(LoginPageLocators.PAGE_TITLE) and \
               "login" in self.get_current_url().lower()
    
    def get_page_title(self):
        """Lấy tiêu đề trang"""
        return self.get_text(LoginPageLocators.PAGE_TITLE)