from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

os.makedirs("debug_login", exist_ok=True)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 15)

print("1. Abriendo Liverpool...")
driver.get("https://www.liverpool.com.mx/tienda/home")
time.sleep(3)
driver.save_screenshot("debug_login/01_home.png")

print("2. Buscando botón 'Iniciar sesión'...")
try:
    btn_login = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Iniciar sesión')]")))
    # Hacer clic con JavaScript para evitar interceptación
    driver.execute_script("arguments[0].click();", btn_login)
    print("   ✅ Click en botón login (vía JavaScript)")
    time.sleep(2)
    driver.save_screenshot("debug_login/02_modal_login.png")
except Exception as e:
    print(f"   ❌ Error: {e}")
    driver.save_screenshot("debug_login/error_boton.png")
    driver.quit()
    exit()

print("3. Esperando a que aparezca el formulario de login...")
time.sleep(2)

# Buscar campo email con múltiples selectores
email_input = None
selectores_email = [
    (By.ID, "email"),
    (By.NAME, "email"),
    (By.CSS_SELECTOR, "input[type='email']"),
    (By.XPATH, "//input[contains(@placeholder, 'Correo')]"),
    (By.XPATH, "//input[contains(@placeholder, 'Email')]")
]

for by, selector in selectores_email:
    try:
        email_input = wait.until(EC.presence_of_element_located((by, selector)))
        print(f"   ✅ Campo email encontrado con: {selector}")
        break
    except:
        continue

if not email_input:
    print("   ❌ No se pudo encontrar el campo de email. Revisa debug_modal.png")
    driver.save_screenshot("debug_error_email.png")
    driver.quit()
    exit()

email_input.send_keys("jesuszaratevallejo@gmail.com")

# Buscar campo password
password_input = None
selectores_pass = [
    (By.ID, "password"),
    (By.NAME, "password"),
    (By.CSS_SELECTOR, "input[type='password']")
]

for by, selector in selectores_pass:
    try:
        password_input = driver.find_element(by, selector)
        print(f"   ✅ Campo password encontrado con: {selector}")
        break
    except:
        continue

if not password_input:
    print("   ❌ No se pudo encontrar el campo de password")
    driver.quit()
    exit()

password_input.send_keys("Zarate23")
driver.save_screenshot("debug_login/03_credenciales_llenadas.png")

print("4. Enviando formulario...")
submit = driver.find_element(By.XPATH, "//button[@type='submit']")
driver.execute_script("arguments[0].click();", submit)
driver.save_screenshot("debug_login/04_formulario_enviado.png")

print("5. Esperando 10 segundos para ver resultado...")
time.sleep(10)
driver.save_screenshot("debug_login/05_resultado.png")

print("6. Verificando si el login fue exitoso...")
if "Mi cuenta" in driver.page_source:
    print("✅ LOGIN EXITOSO")
else:
    print("❌ LOGIN FALLIDO. Revisa los screenshots en la carpeta 'debug_login'")
    if "captcha" in driver.page_source.lower():
        print("   → Posible CAPTCHA bloqueando")
    if "contraseña" in driver.page_source.lower():
        print("   → Credenciales incorrectas")

input("Presiona Enter para cerrar el navegador...")
driver.quit()