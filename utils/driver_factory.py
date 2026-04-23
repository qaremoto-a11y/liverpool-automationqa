import os
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from config import Config

class DriverFactory:
    @staticmethod
    def get_driver(headless=False):
        """Configura el driver con opciones para evitar detección"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Aplicar técnicas anti-detección
        stealth(driver,
            languages=["es-MX", "es"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        driver.maximize_window()
        return driver
    
    @staticmethod
    def save_session(driver):
        """Guarda las cookies de la sesión para reutilizarlas"""
        with open("session_cookies.pkl", "wb") as f:
            pickle.dump(driver.get_cookies(), f)
        print("✅ Sesión guardada correctamente")
    
    @staticmethod
    def load_session(driver):
        """Carga una sesión guardada previamente (maneja archivo vacío/corrupto)"""
        if os.path.exists("session_cookies.pkl"):
            try:
                driver.get(Config.BASE_URL)
                with open("session_cookies.pkl", "rb") as f:
                    cookies = pickle.load(f)
                    if not cookies:
                        raise EOFError
                    for cookie in cookies:
                        try:
                            driver.add_cookie(cookie)
                        except Exception:
                            pass
                    driver.refresh()
                    return True
            except (EOFError, pickle.UnpicklingError, FileNotFoundError):
                os.remove("session_cookies.pkl")
                print("⚠️ Archivo de sesión corrupto eliminado. Se requerirá login manual.")
        return False