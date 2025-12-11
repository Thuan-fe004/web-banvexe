import os
class Config:
    """Cấu hình chung cho test automation"""
    
    # URL
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
    
    # Browser
    BROWSER = os.getenv("BROWSER", "chrome")  # chrome, firefox
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    
    # Timeouts (seconds)
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 20
    PAGE_LOAD_TIMEOUT = 30
    
    # Paths
    SCREENSHOTS_PATH = "tests/reports/screenshots"
    LOGS_PATH = "tests/reports/logs"
    ALLURE_RESULTS_PATH = "tests/reports/allure-results"
    
    # Test Data
    TEST_DATA_PATH = "tests/test_data"
    
    @classmethod
    def get_url(cls, path=""):
        """Lấy full URL"""
        return f"{cls.BASE_URL}{path}"