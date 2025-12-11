from selenium.webdriver.common.by import By
from tests.page_objects.base_page import BasePage
from tests.config.config import Config

class RegisterPageLocators:
    """Locators cho Register Page"""
    # Form fields
    FULL_NAME_INPUT = (By.ID, "full_name")
    USERNAME_INPUT = (By.ID, "username")
    EMAIL_INPUT = (By.ID, "email")
    PHONE_INPUT = (By.ID, "phone")
    ADDRESS_TEXTAREA = (By.ID, "address")
    PASSWORD_INPUT = (By.ID, "password")
    
    # Buttons
    REGISTER_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    
    # Links
    LOGIN_LINK = (By.CSS_SELECTOR, ".login-link a")
    
    ALERT_SUCCESS = (By.XPATH, "//div[contains(@class,'alert') and contains(@class,'success')] | //*[contains(text(),'thành công')]")
    ALERT_DANGER = (By.XPATH, "//div[contains(@class,'alert') and contains(@class,'danger')] | //*[contains(text(),'lỗi')] | //*[contains(text(),'không hợp lệ')] | //*[contains(text(),'tồn tại')] | //div[@role='alert' and not(contains(@class,'success'))]")
    # Headers
    PAGE_TITLE = (By.CSS_SELECTOR, ".header h2")

class RegisterPage(BasePage):
    """Page Object cho Register Page"""
    
    def __init__(self, driver):
        super().__init__(driver)
        self.url = Config.get_url("/register")
    
    def open_register_page(self):
        """Mở trang đăng ký"""
        self.open(self.url)
    
    def fill_full_name(self, name):
        """Nhập họ tên"""
        self.type(RegisterPageLocators.FULL_NAME_INPUT, name)
    
    def fill_username(self, username):
        """Nhập username"""
        self.type(RegisterPageLocators.USERNAME_INPUT, username)
    
    def fill_email(self, email):
        """Nhập email"""
        self.type(RegisterPageLocators.EMAIL_INPUT, email)
    
    def fill_phone(self, phone):
        """Nhập số điện thoại"""
        self.type(RegisterPageLocators.PHONE_INPUT, phone)
    
    def fill_address(self, address):
        """Nhập địa chỉ"""
        self.type(RegisterPageLocators.ADDRESS_TEXTAREA, address)
    
    def fill_password(self, password):
        """Nhập mật khẩu"""
        self.type(RegisterPageLocators.PASSWORD_INPUT, password)
    
    def click_register_button(self):
        """Click nút đăng ký"""
        self.click(RegisterPageLocators.REGISTER_BUTTON)
    
    def click_login_link(self):
        """Click link đăng nhập"""
        self.click(RegisterPageLocators.LOGIN_LINK)
    
    def register(self, full_name, username, email, phone, address, password):
        """Thực hiện đăng ký (shortcut method)"""
        self.fill_full_name(full_name)
        self.fill_username(username)
        self.fill_email(email)
        self.fill_phone(phone)
        if address:
            self.fill_address(address)
        self.fill_password(password)
        self.click_register_button()
    
    def get_success_message(self):
        """Lấy thông báo thành công"""
        if self.is_displayed(RegisterPageLocators.ALERT_SUCCESS):
            return self.get_text(RegisterPageLocators.ALERT_SUCCESS)
        return None
    
    def get_error_message(self):
        """Lấy thông báo lỗi"""
        if self.is_displayed(RegisterPageLocators.ALERT_DANGER):
            return self.get_text(RegisterPageLocators.ALERT_DANGER)
        return None
    
    def is_on_register_page(self):
        """Kiểm tra đang ở trang register"""
        return self.is_displayed(RegisterPageLocators.PAGE_TITLE) and \
               "register" in self.get_current_url().lower()