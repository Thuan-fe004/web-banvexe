import pytest
import allure
import time
from tests.utils.helpers import Helpers  # THÊM DÒNG NÀY
from selenium.webdriver.common.by import By   # THÊM DÒNG NÀY
from tests.page_objects.register_page import RegisterPageLocators  # THÊM DÒNG NÀY

@allure.feature("Authentication")
@allure.suite("Register Tests")
class TestRegister:
    """Test cases cho tính năng đăng ký"""
    
    @allure.title("TC_REG_001: Đăng ký thành công với dữ liệu hợp lệ")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_register_success(self, register_page):
        """Test đăng ký thành công"""
        with allure.step("Mở trang đăng ký"):
            register_page.open_register_page()
            time.sleep(1)
        
        with allure.step("Verify đang ở trang register"):
            assert register_page.is_on_register_page()
        
        # Tạo dữ liệu random để tránh trùng
        username = Helpers.generate_random_username()
        email = Helpers.generate_random_email()
        phone = Helpers.generate_random_phone()
        
        with allure.step(f"Điền thông tin đăng ký với username: {username}"):
            register_page.register(
                full_name=Helpers.generate_random_name(),
                username=username,
                email=email,
                phone=phone,
                address=Helpers.generate_random_address(),
                password="Test@123456"
            )
            time.sleep(2)

        with allure.step("Kiểm tra thông báo đăng ký thành công"):
            success_msg = register_page.get_success_message()
            assert success_msg is not None, "Không hiển thị thông báo thành công"
            assert any(keyword in success_msg.lower() for keyword in 
                    ["thành công", "đăng ký thành công", "welcome", "tạo tài khoản"]), \
                f"Thông báo không đúng: {success_msg}"

        with allure.step("Kiểm tra đã redirect về trang chủ hoặc login"):
            current_url = register_page.get_current_url()
            assert "register" not in current_url.lower(), "Vẫn còn ở trang register sau khi đăng ký thành công"


@allure.title("TC_REG_002: Đăng ký thất bại - Username đã tồn tại")
@allure.severity(allure.severity_level.NORMAL)
def test_register_duplicate_username( register_page, test_data):
    """Test đăng ký với username đã tồn tại"""
    with allure.step("Mở trang đăng ký"):
        register_page.open_register_page()
        time.sleep(1)

    existing_user = test_data["valid_user"]["username"]
    with allure.step(f"Điền thông tin với username đã tồn tại: {existing_user}"):
        register_page.register(
            full_name=Helpers.generate_random_name(),
            username=existing_user,  # trùng
            email=Helpers.generate_random_email(),
            phone=Helpers.generate_random_phone(),
            address=Helpers.generate_random_address(),
            password="Test@123456"
        )
        time.sleep(2)

    with allure.step("Kiểm tra thông báo lỗi username đã tồn tại"):
        error_msg = register_page.get_error_message()
        assert error_msg is not None, "Không có thông báo lỗi khi username trùng"
        assert any(keyword in error_msg.lower() for keyword in 
                  ["đã tồn tại", "username already", "tài khoản đã được sử dụng"]), \
            f"Thông báo lỗi không đúng: {error_msg}"


@allure.title("TC_REG_003: Đăng ký thất bại - Email đã được sử dụng")
@allure.severity(allure.severity_level.NORMAL)
def test_register_duplicate_email(register_page):
    """Test đăng ký với email đã tồn tại trong hệ thống"""
    with allure.step("Mở trang đăng ký"):
        register_page.open_register_page()
        time.sleep(1)

    with allure.step("Điền thông tin với email đã tồn tại"):
        register_page.register(
            full_name=Helpers.generate_random_name(),
            username=Helpers.generate_random_username(),
            email="test@example.com",  # giả sử email này đã có trong DB seed
            phone=Helpers.generate_random_phone(),
            address=Helpers.generate_random_address(),
            password="Test@123456"
        )
        time.sleep(2)

    with allure.step("Kiểm tra thông báo lỗi email đã tồn tại"):
        error_msg = register_page.get_error_message()
        assert error_msg is not None
        assert any(keyword in error_msg.lower() for keyword in 
                  ["email", "đã tồn tại", "already", "sử dụng"]), \
            f"Thông báo lỗi không đề cập đến email: {error_msg}"


@allure.title("TC_REG_004: Đăng ký thất bại - Để trống các trường bắt buộc")
@allure.severity(allure.severity_level.NORMAL)
def test_register_empty_required_fields(register_page):
    """Test validation frontend khi để trống các field required"""
    with allure.step("Mở trang đăng ký"):
        register_page.open_register_page()
        time.sleep(1)

    with allure.step("Click nút Đăng ký mà không nhập gì"):
        register_page.click_register_button()
        time.sleep(1)

    with allure.step("Kiểm tra vẫn ở trang đăng ký (HTML5 validation)"):
        assert register_page.is_on_register_page(), "Đã rời khỏi trang register dù chưa nhập dữ liệu"

    # Kiểm tra một vài field required có hiển thị lỗi (nếu dùng Bootstrap validation)
    
    assert register_page.is_displayed((By.CSS_SELECTOR, "input:invalid")), \
        "Không có field nào bị invalid (validation không hoạt động)"


@allure.title("TC_REG_005: Đăng ký thất bại - Mật khẩu quá ngắn (< 6 ký tự)")
@allure.severity(allure.severity_level.NORMAL)
def test_register_short_password(register_page):
    """Test validation frontend: mật khẩu phải ≥ 6 ký tự"""
    with allure.step("Mở trang đăng ký"):
        register_page.open_register_page()
        time.sleep(1)

    with allure.step("Điền form với password chỉ 5 ký tự"):
        register_page.fill_full_name(Helpers.generate_random_name())
        register_page.fill_username(Helpers.generate_random_username())
        register_page.fill_email(Helpers.generate_random_email())
        register_page.fill_phone(Helpers.generate_random_phone())
        register_page.fill_address(Helpers.generate_random_address())
        register_page.fill_password("12345")  # quá ngắn

    with allure.step("Click nút đăng ký"):
        register_page.click_register_button()
        time.sleep(1)

    with allure.step("Kiểm tra trình duyệt CHẶN submit do minlength"):
        # Không được rời khỏi trang register
        assert register_page.is_on_register_page(), "Đã rời trang dù password quá ngắn"

        # Kiểm tra input password có class :invalid không
        password_field = register_page.driver.find_element(By.ID, "password")
        is_invalid = register_page.driver.execute_script(
            "return arguments[0].validity.valid === false && arguments[0].validationMessage !== ''", 
            password_field
        )
        assert is_invalid, "Trình duyệt không chặn password quá ngắn!"

        print("HTML5 validation hoạt động đúng: chặn password < 6 ký tự")


@allure.title("TC_REG_006: Click link 'Đăng nhập ngay' từ trang đăng ký")
@allure.severity(allure.severity_level.MINOR)
def test_click_login_link_from_register(register_page):
    """Test chuyển từ trang đăng ký về trang đăng nhập"""
    with allure.step("Mở trang đăng ký"):
        register_page.open_register_page()
        time.sleep(1)

    with allure.step("Click link 'Đã có tài khoản? Đăng nhập ngay'"):
        register_page.click_login_link()
        time.sleep(2)

    with allure.step("Kiểm tra đã redirect về trang login"):
        current_url = register_page.get_current_url()
        assert "login" in current_url.lower(), "Không redirect về trang login"


@allure.title("TC_REG_007: Kiểm tra giao diện các thành phần trên trang đăng ký")
@allure.severity(allure.severity_level.TRIVIAL)
def test_register_page_ui_elements(register_page):
    """Kiểm tra các element UI hiển thị đầy đủ"""
    with allure.step("Mở trang đăng ký"):
        register_page.open_register_page()
        time.sleep(2)

    with allure.step("Kiểm tra tiêu đề trang"):
        title = register_page.get_text(RegisterPageLocators.PAGE_TITLE)
        assert "đăng ký" in title.lower() or "register" in title.lower()

    with allure.step("Kiểm tra tất cả input fields hiển thị"):
     
        assert register_page.is_displayed(RegisterPageLocators.FULL_NAME_INPUT)
        assert register_page.is_displayed(RegisterPageLocators.USERNAME_INPUT)
        assert register_page.is_displayed(RegisterPageLocators.EMAIL_INPUT)
        assert register_page.is_displayed(RegisterPageLocators.PHONE_INPUT)
        assert register_page.is_displayed(RegisterPageLocators.ADDRESS_TEXTAREA)
        assert register_page.is_displayed(RegisterPageLocators.PASSWORD_INPUT)
        assert register_page.is_displayed(RegisterPageLocators.REGISTER_BUTTON)
        assert register_page.is_displayed(RegisterPageLocators.LOGIN_LINK)