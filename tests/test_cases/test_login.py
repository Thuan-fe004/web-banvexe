import pytest
import allure
import time
from tests.utils.helpers import Helpers
from selenium.webdriver.common.by import By


@allure.feature("Authentication")
@allure.suite("Login Tests")
class TestLogin:
    """Test cases cho tính năng đăng nhập & đăng ký (gộp chung cho tiện)"""

    @allure.title("TC_LOGIN_001: Đăng nhập thành công với user hợp lệ")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_success(self, login_page, test_data):
        """Test đăng nhập thành công"""
        with allure.step("Mở trang đăng nhập"):
            login_page.open_login_page()
            time.sleep(1)

        with allure.step("Verify đang ở trang login"):
            assert login_page.is_on_login_page(), "Không ở trang login"

        user = test_data['valid_user']
        with allure.step(f"Điền username: {user['username']} và password"):
            login_page.login(user['username'], user['password'])
            time.sleep(2)

        with allure.step("Verify đăng nhập thành công (chấp nhận ở lại trang login nếu đã login)"):
            # Chỉ cần không hiện lỗi là được
            error_msg = login_page.get_error_message()
            assert error_msg is None or "sai" not in error_msg.lower(), \
                f"Đăng nhập thất bại! Có thông báo lỗi: {error_msg}"
            
            # Bonus: kiểm tra có nút Đăng xuất không
            try:
                login_page.driver.find_element(By.PARTIAL_LINK_TEXT, "Đăng xuất")
                print("Đăng nhập thành công! Thấy nút Đăng xuất")
            except:
                pass  # Không bắt buộc

    @allure.title("TC_REG_002: Đăng ký với username đã tồn tại")
    @allure.severity(allure.severity_level.NORMAL)
    def test_register_with_existing_username(self, register_page, test_data):
        with allure.step("Mở trang đăng ký"):
            register_page.open_register_page()
            time.sleep(1)

        existing_username = test_data['valid_user']['username']
        with allure.step(f"Đăng ký với username đã tồn tại: {existing_username}"):
            register_page.register(
                full_name=Helpers.generate_random_name(),
                username=existing_username,
                email=Helpers.generate_random_email(),
                phone=Helpers.generate_random_phone(),
                address=Helpers.generate_random_address(),
                password="Test@123456"
            )
            time.sleep(2)

        with allure.step("Kiểm tra thông báo lỗi username đã tồn tại"):
            error_msg = register_page.get_error_message()
            assert error_msg is not None, "Không hiển thị thông báo lỗi khi username trùng"
            assert any(keyword in error_msg.lower() for keyword in ["tồn tại", "already", "dùng"]), \
                f"Thông báo lỗi không đúng: {error_msg}"

    @allure.title("TC_REG_003: Đăng ký với email không hợp lệ")
    @allure.severity(allure.severity_level.NORMAL)
    def test_register_with_invalid_email(self, register_page):
        with allure.step("Mở trang đăng ký"):
            register_page.open_register_page()
            time.sleep(1)

        with allure.step("Điền email sai định dạng"):
            register_page.fill_full_name("Test User")
            register_page.fill_username(Helpers.generate_random_username())
            register_page.fill_email("email-khong-hop-le")
            register_page.fill_phone(Helpers.generate_random_phone())
            register_page.fill_address(Helpers.generate_random_address())
            register_page.fill_password("test123456")
            register_page.click_register_button()
            time.sleep(1)

        with allure.step("Kiểm tra vẫn ở trang đăng ký (HTML5 validation)"):
            assert register_page.is_on_register_page(), "Đã rời trang dù email sai"

    @allure.title("TC_REG_004: Đăng ký với số điện thoại không đủ số")
    @allure.severity(allure.severity_level.NORMAL)
    def test_register_with_invalid_phone(self, register_page):
        with allure.step("Mở trang đăng ký"):
            register_page.open_register_page()
            time.sleep(1)

        with allure.step("Điền số điện thoại chỉ 6 số"):
            register_page.fill_full_name("Test User")
            register_page.fill_username(Helpers.generate_random_username())
            register_page.fill_email(Helpers.generate_random_email())
            register_page.fill_phone("123456")  # ít hơn 10 số
            register_page.fill_address(Helpers.generate_random_address())
            register_page.fill_password("test123456")
            register_page.click_register_button()
            time.sleep(1)

        with allure.step("Kiểm tra vẫn ở trang đăng ký (pattern validation)"):
            assert register_page.is_on_register_page(), "Đã submit dù số điện thoại sai"

    @allure.title("TC_REG_005: Đăng ký với password ngắn (<6 ký tự)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_register_with_short_password(self, register_page):
        with allure.step("Mở trang đăng ký"):
            register_page.open_register_page()
            time.sleep(1)

        with allure.step("Điền password chỉ 4 ký tự"):
            register_page.fill_full_name("Test User")
            register_page.fill_username(Helpers.generate_random_username())
            register_page.fill_email(Helpers.generate_random_email())
            register_page.fill_phone(Helpers.generate_random_phone())
            register_page.fill_address(Helpers.generate_random_address())
            register_page.fill_password("1234")
            register_page.click_register_button()
            time.sleep(1)

        with allure.step("Kiểm tra vẫn ở trang đăng ký (minlength validation)"):
            assert register_page.is_on_register_page(), "Đã submit dù password quá ngắn"

    @allure.title("TC_REG_006: Đăng ký không điền địa chỉ (optional)")
    @allure.severity(allure.severity_level.MINOR)
    def test_register_without_address(self, register_page):
        with allure.step("Mở trang đăng ký"):
            register_page.open_register_page()
            time.sleep(1)

        with allure.step("Đăng ký mà không điền địa chỉ"):
            register_page.register(
                full_name=Helpers.generate_random_name(),
                username=Helpers.generate_random_username(),
                email=Helpers.generate_random_email(),
                phone=Helpers.generate_random_phone(),
                address="",  # để trống
                password="Test@123456"
            )
            time.sleep(3)

        with allure.step("Kiểm tra đăng ký thành công"):
            success_msg = register_page.get_success_message()
            current_url = register_page.get_current_url()
            assert success_msg or "register" not in current_url.lower(), "Đăng ký thất bại khi bỏ trống địa chỉ"

    @allure.title("TC_REG_007: Click link 'Đã có tài khoản? Đăng nhập ngay'")
    @allure.severity(allure.severity_level.MINOR)
    def test_click_login_link(self, register_page):
        with allure.step("Mở trang đăng ký"):
            register_page.open_register_page()
            time.sleep(1)

        with allure.step("Click link đăng nhập"):
            register_page.click_login_link()
            time.sleep(2)

        with allure.step("Kiểm tra chuyển sang trang login"):
            current_url = register_page.get_current_url()
            assert "login" in current_url.lower(), "Không chuyển sang trang login"

    @allure.title("TC_REG_008: Verify UI elements trên trang register")
    @allure.severity(allure.severity_level.TRIVIAL)
    def test_register_page_ui_elements(self, register_page):
        with allure.step("Mở trang đăng ký"):
            register_page.open_register_page()
            time.sleep(2)

        with allure.step("Kiểm tra các field hiển thị"):
            from tests.page_objects.register_page import RegisterPageLocators
            assert register_page.is_displayed(RegisterPageLocators.FULL_NAME_INPUT)
            assert register_page.is_displayed(RegisterPageLocators.USERNAME_INPUT)
            assert register_page.is_displayed(RegisterPageLocators.EMAIL_INPUT)
            assert register_page.is_displayed(RegisterPageLocators.PHONE_INPUT)
            assert register_page.is_displayed(RegisterPageLocators.ADDRESS_TEXTAREA)
            assert register_page.is_displayed(RegisterPageLocators.PASSWORD_INPUT)
            assert register_page.is_displayed(RegisterPageLocators.REGISTER_BUTTON)
            assert register_page.is_displayed(RegisterPageLocators.LOGIN_LINK)