from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 10)

driver.get("https://www.liverpool.com.mx/tienda/home")
time.sleep(3)

# Abrir modal de login con JavaScript
btn_login = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Iniciar sesión')]")))
driver.execute_script("arguments[0].click();", btn_login)
time.sleep(2)

# Esperar a que aparezca algún input dentro del modal
print("Buscando inputs dentro del modal...")
inputs = driver.find_elements(By.TAG_NAME, "input")
print(f"Total inputs en la página: {len(inputs)}")
for inp in inputs:
    print(f"  - type={inp.get_attribute('type')}, id={inp.get_attribute('id')}, name={inp.get_attribute('name')}, placeholder={inp.get_attribute('placeholder')}")

# También buscar posibles iframes
iframes = driver.find_elements(By.TAG_NAME, "iframe")
print(f"\nIframes encontrados: {len(iframes)}")
for iframe in iframes:
    print(f"  - src={iframe.get_attribute('src')}")

# Tomar screenshot
driver.save_screenshot("debug_modal.png")
print("\n✅ Screenshot guardado como 'debug_modal.png'. Revisa si el modal se abrió correctamente.")

input("Presiona Enter para cerrar...")
driver.quit()