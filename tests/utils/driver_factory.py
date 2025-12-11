from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from tests.config.config import Config

class DriverFactory:
    """Factory để tạo WebDriver"""
    
    @staticmethod
    def get_driver():
        """Tạo và trả về WebDriver instance"""
        if Config.BROWSER.lower() == "chrome":
            return DriverFactory._get_chrome_driver()
        else:
            raise ValueError(f"Browser '{Config.BROWSER}' không được hỗ trợ")
    
    @staticmethod
    def _get_chrome_driver():
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as ChromeService
        import os
        import glob

        # Tải chromedriver (webdriver-manager sẽ tạo thư mục kiểu này)
        driver_path = ChromeDriverManager().install()
        
        # Tìm đúng file .exe (tránh nhầm THIRD_PARTY_NOTICES)
        driver_dir = os.path.dirname(driver_path)
        possible_exe = [
            os.path.join(driver_dir, "chromedriver.exe"),
            os.path.join(driver_dir, "..", "chromedriver.exe"),
            os.path.join(driver_dir, "..", "chromedriver-win32", "chromedriver.exe"),
            os.path.join(driver_dir, "..", "chromedriver-win64", "chromedriver.exe")
        ]
        
        chromedriver_exe = None
        for path in possible_exe:
            full_path = os.path.abspath(path)
            if os.path.exists(full_path):
                chromedriver_exe = full_path
                break
        
        if not chromedriver_exe:
            # Cuối cùng dùng glob tìm tất cả file .exe
            candidates = glob.glob(os.path.join(driver_dir, "**", "chromedriver*.exe"), recursive=True)
            if candidates:
                chromedriver_exe = candidates[0]

        if not chromedriver_exe:
            raise FileNotFoundError("Không tìm thấy chromedriver.exe! Kiểm tra lại .wdm")

        print(f"Đã tìm thấy ChromeDriver: {chromedriver_exe}")

        service = ChromeService(chromedriver_exe)

        chrome_options = ChromeOptions()
        if Config.HEADLESS:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(Config.IMPLICIT_WAIT)
        driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
        return driver