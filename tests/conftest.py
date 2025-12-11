import pytest
import json
import os
from tests.utils.driver_factory import DriverFactory
from tests.page_objects.login_page import LoginPage
from tests.page_objects.register_page import RegisterPage
from tests.config.config import Config

# Pytest hooks
def pytest_configure(config):
    """Tạo thư mục reports nếu chưa có"""
    os.makedirs(Config.SCREENSHOTS_PATH, exist_ok=True)
    os.makedirs(Config.LOGS_PATH, exist_ok=True)
    os.makedirs(Config.ALLURE_RESULTS_PATH, exist_ok=True)

@pytest.fixture(scope="function")
def driver():
    """Fixture để khởi tạo và đóng WebDriver"""
    driver = DriverFactory.get_driver()
    yield driver
    driver.quit()

@pytest.fixture(scope="function")
def login_page(driver):
    """Fixture để khởi tạo LoginPage"""
    return LoginPage(driver)

@pytest.fixture(scope="function")
def register_page(driver):
    """Fixture để khởi tạo RegisterPage"""
    return RegisterPage(driver)

@pytest.fixture(scope="session")
def test_data():
    """Fixture để load test data từ JSON"""
    json_path = os.path.join(Config.TEST_DATA_PATH, "users.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Hook để capture screenshot khi test fail
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook để chụp screenshot khi test fail"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        # Lấy driver từ fixture
        if "driver" in item.funcargs:
            driver = item.funcargs["driver"]
            # Chụp screenshot
            screenshot_name = f"FAILED_{item.name}"
            from tests.utils.helpers import Helpers
            screenshot_path = Helpers.take_screenshot(driver, screenshot_name)
            
            # Attach vào Allure report
            if screenshot_path:
                import allure
                allure.attach.file(
                    screenshot_path,
                    name=screenshot_name,
                    attachment_type=allure.attachment_type.PNG
                )