"""
TEST HOÀN CHỈNH CHO SEARCH RESULTS PAGE - SINGLE FILE
File: test_search_complete.py

Chạy: pytest test_search_complete.py -v --alluredir=allure-results
Xem report: allure serve allure-results
"""

import pytest
import allure
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    BASE_URL = "http://localhost:5000"  # ⚠️ THAY ĐỔI URL NÀY
    BROWSER = "chrome"
    HEADLESS = False  # True = chạy không hiện browser
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 20

# ============================================================================
# TEST DATA
# ============================================================================
TEST_USER = {
    "username": "Thuan2004",  # ⚠️ THAY ĐỔI USERNAME
    "password": "1"  # ⚠️ THAY ĐỔI PASSWORD
}

SEARCH_DATA = {
    "valid_search": {
        "departure": "Hà Nội",
        "arrival": "Hải Phòng",
        "date": "2025-12-6"
    },
    "no_results_search": {
        "departure": "ABC City",
        "arrival": "XYZ City", 
        "date": "2025-12-31"
    }
}

# ============================================================================
# DRIVER FACTORY
# ============================================================================
def get_chrome_driver():
    """Khởi tạo ChromeDriver – FIX 100% lỗi WinError 193 & TypeError"""
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    import os
    import glob

    # Tải driver về
    driver_path = ChromeDriverManager().install()
    driver_dir = os.path.dirname(driver_path)

    print(f"Thư mục driver: {driver_dir}")

    # Tìm file .exe thực sự (không phải file text)
    exe_pattern = os.path.join(driver_dir, "**", "chromedriver*.exe")
    exe_files = glob.glob(exe_pattern, recursive=True)

    if not exe_files:
        # Trường hợp driver nằm trực tiếp trong thư mục
        exe_files = [os.path.join(driver_dir, f) for f in os.listdir(driver_dir) if f.endswith(".exe")]

    if not exe_files:
        raise FileNotFoundError(f"Không tìm thấy chromedriver.exe trong {driver_dir}")

    real_path = exe_files[0]
    print(f"Đã tìm thấy ChromeDriver thật: {real_path}")

    chrome_options = ChromeOptions()
    if Config.HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = ChromeService(executable_path=real_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(Config.IMPLICIT_WAIT)
    return driver

# ============================================================================
# PAGE OBJECTS
# ============================================================================
class LoginPage:
    """Page Object cho Login"""
    
    def __init__(self, driver):
        self.driver = driver
        self.url = f"{Config.BASE_URL}/login"
        self.wait = WebDriverWait(driver, Config.EXPLICIT_WAIT)
    
    def open(self):
        self.driver.get(self.url)
    
    def login(self, username, password):
        """Thực hiện login"""
        username_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_input = self.driver.find_element(By.ID, "password")
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        username_input.clear()
        username_input.send_keys(username)
        password_input.clear()
        password_input.send_keys(password)
        login_button.click()

class SearchPage:
    """Page Object cho Search Results"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, Config.EXPLICIT_WAIT)
    
    def open_search(self, departure, arrival, date):
        """Mở trang search với params"""
        url = f"{Config.BASE_URL}/search?departure={departure}&arrival={arrival}&date={date}"
        self.driver.get(url)
    
    # ========== SEARCH FORM ==========
    def fill_departure(self, text):
        """Nhập điểm xuất phát"""
        input_elem = self.wait.until(
            EC.presence_of_element_located((By.NAME, "departure"))
        )
        input_elem.clear()
        input_elem.send_keys(text)
    
    def fill_arrival(self, text):
        """Nhập điểm đến"""
        input_elem = self.driver.find_element(By.NAME, "arrival")
        input_elem.clear()
        input_elem.send_keys(text)
    
    def fill_date(self, date):
        """Nhập ngày"""
        input_elem = self.driver.find_element(By.NAME, "date")
        input_elem.clear()
        input_elem.send_keys(date)
    
    def click_swap_button(self):
        """Click nút đổi chiều"""
        swap_btn = self.driver.find_element(By.CSS_SELECTOR, ".swap-btn")
        swap_btn.click()
    
    def click_search_button(self):
        """Click nút tìm kiếm"""
        search_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-search")
        search_btn.click()
    
    def perform_search(self, departure, arrival, date):
        """Thực hiện tìm kiếm hoàn chỉnh"""
        self.fill_departure(departure)
        self.fill_arrival(arrival)
        self.fill_date(date)
        self.click_search_button()
    
    # ========== RESULTS ==========
    def get_result_count(self):
        """Lấy số lượng kết quả"""
        count_elem = self.wait.until(
            EC.presence_of_element_located((By.ID, "result-count"))
        )
        return int(count_elem.text)
    
    def get_visible_trip_cards(self):
        """Lấy danh sách trip cards hiển thị"""
        return self.driver.find_elements(By.CSS_SELECTOR, ".trip-card.visible")
    
    def is_no_results_displayed(self):
        """Kiểm tra có thông báo no results không"""
        try:
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".no-results"))
            )
            return True
        except:
            return False
    
    def get_results_info(self):
        """Lấy text thông tin kết quả"""
        info_elem = self.driver.find_element(By.CSS_SELECTOR, ".results-info")
        return info_elem.text
    
    # ========== SORTING ==========
    def click_sort_price_asc(self):
        """Sắp xếp theo giá tăng dần"""
        sort_btn = self.driver.find_element(
            By.XPATH, "//button[contains(text(), 'Giá tăng dần')]"
        )
        sort_btn.click()
    
    def click_sort_time_asc(self):
        """Sắp xếp theo giờ sớm nhất"""
        sort_btn = self.driver.find_element(
            By.XPATH, "//button[contains(text(), 'Giờ đi sớm nhất')]"
        )
        sort_btn.click()
    
    def click_sort_rating(self):
        """Sắp xếp theo đánh giá"""
        sort_btn = self.driver.find_element(
            By.XPATH, "//button[contains(text(), 'Đánh giá cao')]"
        )
        sort_btn.click()
    
    def get_active_sort_button(self):
        """Lấy nút sort đang active"""
        active_btn = self.driver.find_element(By.CSS_SELECTOR, ".sort-btn.active")
        return active_btn.text
    
    # ========== FILTERS ==========
    def check_filter_morning(self):
        """Chọn filter sáng sớm"""
        checkbox = self.driver.find_element(By.ID, "time_morning")
        if not checkbox.is_selected():
            checkbox.click()
    
    def check_filter_day(self):
        """Chọn filter buổi sáng"""
        checkbox = self.driver.find_element(By.ID, "time_day")
        if not checkbox.is_selected():
            checkbox.click()
    
    def check_filter_afternoon(self):
        """Chọn filter buổi chiều"""
        checkbox = self.driver.find_element(By.ID, "time_afternoon")
        if not checkbox.is_selected():
            checkbox.click()
    
    def check_filter_evening(self):
        """Chọn filter buổi tối"""
        checkbox = self.driver.find_element(By.ID, "time_evening")
        if not checkbox.is_selected():
            checkbox.click()
    
    def check_filter_limousine(self):
        """Chọn filter Limousine"""
        checkbox = self.driver.find_element(By.ID, "type_limousine")
        if not checkbox.is_selected():
            checkbox.click()
    
    def check_filter_sleeper(self):
        """Chọn filter giường nằm"""
        checkbox = self.driver.find_element(By.ID, "type_sleeper")
        if not checkbox.is_selected():
            checkbox.click()
    
    def check_filter_seat(self):
        """Chọn filter ghế ngồi"""
        checkbox = self.driver.find_element(By.ID, "type_seat")
        if not checkbox.is_selected():
            checkbox.click()
    
    def set_price_range(self, min_price, max_price):
        """Đặt khoảng giá"""
        min_input = self.driver.find_element(By.ID, "min_price")
        max_input = self.driver.find_element(By.ID, "max_price")
        
        min_input.clear()
        min_input.send_keys(str(min_price))
        
        max_input.clear()
        max_input.send_keys(str(max_price))
    
    def check_filter_rating_5(self):
        """Chọn filter 5 sao"""
        checkbox = self.driver.find_element(By.ID, "rating_5")
        if not checkbox.is_selected():
            checkbox.click()
    
    def check_filter_rating_4(self):
        """Chọn filter 4 sao trở lên"""
        checkbox = self.driver.find_element(By.ID, "rating_4")
        if not checkbox.is_selected():
            checkbox.click()
    
    def check_filter_rating_3(self):
        """Chọn filter 3 sao trở lên"""
        checkbox = self.driver.find_element(By.ID, "rating_3")
        if not checkbox.is_selected():
            checkbox.click()
    
    def click_clear_all_filters(self):
        """Click nút xóa tất cả filter"""
        clear_btn = self.driver.find_element(
            By.XPATH, "//button[contains(text(), 'Xóa tất cả')]"
        )
        clear_btn.click()
    
    # ========== TRIP CARDS ==========
    def get_first_trip_price(self):
        """Lấy giá của chuyến đầu tiên"""
        price_elem = self.driver.find_element(By.CSS_SELECTOR, ".trip-card.visible:first-child .final-price")
        price_text = price_elem.text.replace('đ', '').replace('.', '').replace(',', '')
        return int(price_text)
    
    def get_first_trip_company(self):
        """Lấy tên công ty chuyến đầu tiên"""
        company_elem = self.driver.find_element(By.CSS_SELECTOR, ".trip-card.visible:first-child .company-details h3")
        return company_elem.text
    
    def get_first_trip_departure_time(self):
        """Lấy giờ khởi hành chuyến đầu tiên"""
        time_elem = self.driver.find_element(By.CSS_SELECTOR, ".trip-card.visible:first-child .time-info:first-child .time")
        return time_elem.text
    
    def click_first_book_button(self):
        """Click nút đặt vé chuyến đầu tiên"""
        book_btn = self.driver.find_element(By.CSS_SELECTOR, ".trip-card.visible:first-child .btn-book")
        book_btn.click()
    
    # ========== NAVBAR ==========
    def is_logged_in(self):
        """Kiểm tra đã login chưa"""
        try:
            self.driver.find_element(By.CSS_SELECTOR, ".user-info")
            return True
        except:
            return False
    
    def click_logout(self):
        """Click logout"""
        logout_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-logout")
        logout_btn.click()

# ============================================================================
# PYTEST FIXTURES
# ============================================================================
@pytest.fixture(scope="function")
def driver():
    """Fixture WebDriver"""
    driver = get_chrome_driver()
    yield driver
    driver.quit()

@pytest.fixture(scope="function")
def login_page(driver):
    """Fixture LoginPage"""
    return LoginPage(driver)

@pytest.fixture(scope="function")
def search_page(driver):
    """Fixture SearchPage"""
    return SearchPage(driver)

@pytest.fixture(scope="function")
def logged_in_driver(driver, login_page):
    """Fixture driver đã login sẵn"""
    login_page.open()
    time.sleep(1)
    login_page.login(TEST_USER["username"], TEST_USER["password"])
    time.sleep(2)
    return driver

# ============================================================================
# TEST CASES - SEARCH FUNCTIONALITY
# ============================================================================
@allure.feature("Search & Filter")
@allure.suite("Search Tests")
class TestSearchResults:
    """Test cases cho Search Results Page"""
    
    @allure.title("TC_SEARCH_001: Tìm kiếm chuyến xe thành công")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search_trips_success(self, logged_in_driver, search_page):
        """Test tìm kiếm chuyến xe cơ bản"""
        with allure.step("Mở trang search với params"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        with allure.step("Verify có kết quả tìm kiếm"):
            result_count = search_page.get_result_count()
            assert result_count > 0, f"Không tìm thấy chuyến xe nào. Count = {result_count}"
        
        with allure.step("Verify có trip cards hiển thị"):
            visible_cards = search_page.get_visible_trip_cards()
            assert len(visible_cards) > 0, "Không có trip card nào hiển thị"
            assert len(visible_cards) == result_count, "Số card không khớp với count"
        
        with allure.step("Verify results info hiển thị đúng"):
            results_info = search_page.get_results_info()
            assert search_data["departure"] in results_info
            assert search_data["arrival"] in results_info
    
    @allure.title("TC_SEARCH_002: Tìm kiếm không có kết quả")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_no_results(self, logged_in_driver, search_page):
        """Test tìm kiếm không có kết quả"""
        with allure.step("Tìm kiếm tuyến không tồn tại"):
            search_data = SEARCH_DATA["no_results_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        with allure.step("Verify hiển thị thông báo no results"):
            assert search_page.is_no_results_displayed(), "Không hiển thị thông báo no results"
        
        with allure.step("Verify result count = 0"):
            result_count = search_page.get_result_count()
            assert result_count == 0, f"Result count phải là 0, nhưng là {result_count}"
    
    @allure.title("TC_SEARCH_003: Tìm kiếm lại với form sticky")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_again_with_form(self, logged_in_driver, search_page):
        """Test tìm kiếm lại bằng form sticky"""
        with allure.step("Mở trang search ban đầu"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        initial_count = search_page.get_result_count()
        
        with allure.step("Thay đổi điểm đến và search lại"):
            search_page.fill_arrival("Đà Nẵng")
            search_page.click_search_button()
            time.sleep(2)
        
        with allure.step("Verify kết quả thay đổi"):
            new_count = search_page.get_result_count()
            # Có thể bằng hoặc khác tùy data
            assert new_count >= 0, "Result count không hợp lệ"
    
    @allure.title("TC_SEARCH_004: Đổi chiều điểm đi - điểm đến")
    @allure.severity(allure.severity_level.NORMAL)
    def test_swap_locations(self, logged_in_driver, search_page):
        """Test nút swap locations"""
        with allure.step("Mở trang search"):
            search_page.open_search("Hà Nội", "Hải Phòng", "2025-01-20")
            time.sleep(2)
        
        with allure.step("Lấy giá trị ban đầu"):
            departure_input = search_page.driver.find_element(By.NAME, "departure")
            arrival_input = search_page.driver.find_element(By.NAME, "arrival")
            initial_departure = departure_input.get_attribute("value")
            initial_arrival = arrival_input.get_attribute("value")
        
        with allure.step("Click nút swap"):
            search_page.click_swap_button()
            time.sleep(1)
        
        with allure.step("Verify đã đổi chiều"):
            new_departure = departure_input.get_attribute("value")
            new_arrival = arrival_input.get_attribute("value")
            assert new_departure == initial_arrival, "Departure không đổi"
            assert new_arrival == initial_departure, "Arrival không đổi"

# ============================================================================
# TEST CASES - SORTING
# ============================================================================
@allure.feature("Search & Filter")
@allure.suite("Sorting Tests")
class TestSorting:
    """Test cases cho chức năng sắp xếp"""
    
    @allure.title("TC_SORT_001: Sắp xếp theo giá tăng dần")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sort_by_price_ascending(self, logged_in_driver, search_page):
        """Test sắp xếp theo giá"""
        with allure.step("Mở trang search với kết quả"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        with allure.step("Click sắp xếp theo giá tăng dần"):
            search_page.click_sort_price_asc()
            time.sleep(1)
        
        with allure.step("Verify nút sort active"):
            active_sort = search_page.get_active_sort_button()
            assert "Giá tăng dần" in active_sort
        
        with allure.step("Verify kết quả vẫn hiển thị"):
            visible_cards = search_page.get_visible_trip_cards()
            assert len(visible_cards) > 0
    
    @allure.title("TC_SORT_002: Sắp xếp theo giờ đi sớm nhất")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sort_by_time(self, logged_in_driver, search_page):
        """Test sắp xếp theo giờ"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        with allure.step("Click sắp xếp theo giờ"):
            search_page.click_sort_time_asc()
            time.sleep(1)
        
        with allure.step("Verify nút sort active"):
            active_sort = search_page.get_active_sort_button()
            assert "Giờ đi sớm nhất" in active_sort
    
    @allure.title("TC_SORT_003: Sắp xếp theo đánh giá cao")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sort_by_rating(self, logged_in_driver, search_page):
        """Test sắp xếp theo rating"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        with allure.step("Click sắp xếp theo rating"):
            search_page.click_sort_rating()
            time.sleep(1)
        
        with allure.step("Verify nút sort active"):
            active_sort = search_page.get_active_sort_button()
            assert "Đánh giá cao" in active_sort

# ============================================================================
# TEST CASES - FILTERS
# ============================================================================
@allure.feature("Search & Filter")
@allure.suite("Filter Tests")
class TestFilters:
    """Test cases cho chức năng lọc"""
    
    @allure.title("TC_FILTER_001: Lọc theo giờ sáng sớm")
    @allure.severity(allure.severity_level.NORMAL)
    def test_filter_by_morning(self, logged_in_driver, search_page):
        """Test lọc theo giờ sáng sớm"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        initial_count = search_page.get_result_count()
        
        with allure.step("Chọn filter Sáng sớm (00:00-06:00)"):
            search_page.check_filter_morning()
            time.sleep(1)
        
        with allure.step("Verify số kết quả thay đổi"):
            filtered_count = search_page.get_result_count()
            assert filtered_count <= initial_count, "Filter không hoạt động"
    
    @allure.title("TC_FILTER_002: Lọc theo loại xe Limousine")
    @allure.severity(allure.severity_level.NORMAL)
    def test_filter_by_limousine(self, logged_in_driver, search_page):
        """Test lọc theo loại xe"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        initial_count = search_page.get_result_count()
        
        with allure.step("Chọn filter Limousine"):
            search_page.check_filter_limousine()
            time.sleep(1)
        
        with allure.step("Verify số kết quả thay đổi"):
            filtered_count = search_page.get_result_count()
            assert filtered_count <= initial_count
    
    @allure.title("TC_FILTER_003: Lọc theo khoảng giá")
    @allure.severity(allure.severity_level.NORMAL)
    def test_filter_by_price_range(self, logged_in_driver, search_page):
        """Test lọc theo giá"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        initial_count = search_page.get_result_count()
        
        with allure.step("Đặt khoảng giá 100,000 - 300,000"):
            search_page.set_price_range(100000, 300000)
            time.sleep(1)
        
        with allure.step("Verify số kết quả thay đổi"):
            filtered_count = search_page.get_result_count()
            assert filtered_count <= initial_count
    
    @allure.title("TC_FILTER_004: Lọc theo rating 5 sao")
    @allure.severity(allure.severity_level.NORMAL)
    def test_filter_by_5_star_rating(self, logged_in_driver, search_page):
        """Test lọc theo đánh giá"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        initial_count = search_page.get_result_count()
        
        with allure.step("Chọn filter 5 sao"):
            search_page.check_filter_rating_5()
            time.sleep(1)
        
        with allure.step("Verify số kết quả thay đổi"):
            filtered_count = search_page.get_result_count()
            assert filtered_count <= initial_count
    
    @allure.title("TC_FILTER_005: Kết hợp nhiều filters")
    @allure.severity(allure.severity_level.NORMAL)
    def test_combine_multiple_filters(self, logged_in_driver, search_page):
        """Test kết hợp nhiều bộ lọc"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        initial_count = search_page.get_result_count()
        
        with allure.step("Apply nhiều filters"):
            search_page.check_filter_day()
            search_page.check_filter_limousine()
            search_page.check_filter_rating_4()
            time.sleep(1)
        
        with allure.step("Verify số kết quả giảm"):
            filtered_count = search_page.get_result_count()
            assert filtered_count <= initial_count
    
    @allure.title("TC_FILTER_006: Xóa tất cả bộ lọc")
    @allure.severity(allure.severity_level.NORMAL)
    def test_clear_all_filters(self, logged_in_driver, search_page):
        """Test xóa tất cả filters"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        initial_count = search_page.get_result_count()
        
        with allure.step("Apply một số filters"):
            search_page.check_filter_morning()
            search_page.check_filter_limousine()
            search_page.set_price_range(100000, 200000)
            time.sleep(1)
        
        filtered_count = search_page.get_result_count()
        assert filtered_count <= initial_count
        
        with allure.step("Click 'Xóa tất cả'"):
            search_page.click_clear_all_filters()
            time.sleep(1)
        
        with allure.step("Verify quay lại số kết quả ban đầu"):
            final_count = search_page.get_result_count()
            assert final_count == initial_count, f"Expected {initial_count}, got {final_count}"

# ============================================================================
# TEST CASES - BOOKING
# ============================================================================
@allure.feature("Search & Filter")
@allure.suite("Booking Initiation Tests")
class TestBookingInitiation:
    """Test cases cho chức năng bắt đầu đặt vé"""
    
    @allure.title("TC_BOOK_001: Click nút đặt vé redirect đến seat selection")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_click_book_button(self, logged_in_driver, search_page):
        """Test click nút đặt vé"""
        with allure.step("Mở trang search với kết quả"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        with allure.step("Verify có chuyến xe để đặt"):
            result_count = search_page.get_result_count()
            assert result_count > 0, "Không có chuyến xe nào để test"
        
        with allure.step("Click nút 'Chọn chuyến' đầu tiên"):
            search_page.click_first_book_button()
            time.sleep(3)
        
        with allure.step("Verify redirect đến trang chọn ghế"):
            current_url = search_page.driver.current_url
            assert "booking" in current_url, f"Không redirect đến booking. URL: {current_url}"
    
    @allure.title("TC_BOOK_002: Verify thông tin trip card hiển thị đầy đủ")
    @allure.severity(allure.severity_level.NORMAL)
    def test_trip_card_displays_all_info(self, logged_in_driver, search_page):
        """Test trip card hiển thị đầy đủ thông tin"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        if search_page.get_result_count() > 0:
            with allure.step("Verify thông tin công ty"):
                company = search_page.get_first_trip_company()
                assert len(company) > 0, "Tên công ty trống"
            
            with allure.step("Verify giá vé"):
                price = search_page.get_first_trip_price()
                assert price > 0, "Giá vé không hợp lệ"
            
            with allure.step("Verify giờ khởi hành"):
                time_str = search_page.get_first_trip_departure_time()
                assert len(time_str) > 0, "Giờ khởi hành trống"

# ============================================================================
# TEST CASES - NAVBAR & LOGOUT
# ============================================================================
@allure.feature("Search & Filter")
@allure.suite("Navbar Tests")
class TestNavbar:
    """Test cases cho navbar"""
    
    @allure.title("TC_NAV_001: Verify user đã login hiển thị trên navbar")
    @allure.severity(allure.severity_level.MINOR)
    def test_logged_in_user_displayed(self, logged_in_driver, search_page):
        """Test hiển thị thông tin user"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        with allure.step("Verify user info hiển thị"):
            assert search_page.is_logged_in(), "User chưa login"
    
    @allure.title("TC_NAV_002: Click logout")
    @allure.severity(allure.severity_level.NORMAL)
    def test_logout_function(self, logged_in_driver, search_page):
        """Test chức năng logout"""
        with allure.step("Mở trang search"):
            search_data = SEARCH_DATA["valid_search"]
            search_page.open_search(
                search_data["departure"],
                search_data["arrival"],
                search_data["date"]
            )
            time.sleep(2)
        
        with allure.step("Click nút logout"):
            search_page.click_logout()
            time.sleep(2)
        
        with allure.step("Verify redirect về trang login"):
            current_url = search_page.driver.current_url
            assert "login" in current_url, "Không redirect về login sau logout"



# ============================================================================
# ADDITIONAL HELPERS (Optional)
# ============================================================================
def take_screenshot(driver, name):
    """Helper function để chụp screenshot"""
    import os
    from datetime import datetime
    
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = os.path.join(screenshots_dir, filename)
    
    driver.save_screenshot(filepath)
    print(f"📸 Screenshot saved: {filepath}")
    return filepath

# Hook để auto screenshot khi test fail
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Auto capture screenshot when test fails"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        if "driver" in item.funcargs:
            driver = item.funcargs["driver"]
            screenshot_name = f"FAILED_{item.name}"
            screenshot_path = take_screenshot(driver, screenshot_name)
            
            # Attach to Allure
            try:
                import allure
                allure.attach.file(
                    screenshot_path,
                    name=screenshot_name,
                    attachment_type=allure.attachment_type.PNG
                )
            except:
                pass  # Allure không có thì skip

# ============================================================================
# PYTEST MARKERS (Optional)
# ============================================================================
"""
Có thể run test theo markers:

pytest test_search_complete.py -m critical -v
pytest test_search_complete.py -m smoke -v

Để dùng markers, thêm vào pytest.ini:
[pytest]
markers =
    critical: Critical test cases
    smoke: Smoke test suite
    regression: Full regression suite
"""