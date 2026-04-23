from utils.driver_factory import DriverFactory
from config import Config
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("🔍 DIAGNÓSTICO COMPLETO")
print("=" * 50)

driver = DriverFactory.get_driver()
wait = WebDriverWait(driver, 20)

# 1. Verificar sesión
print("\n1. Verificando sesión guardada...")
from utils.driver_factory import DriverFactory as DF
if DF.load_session(driver):
    print("   ✅ Sesión cargada correctamente")
else:
    print("   ❌ No se pudo cargar la sesión")

# 2. Navegar a la URL de productos
url_zapatos = "https://www.liverpool.com.mx/tienda?s=zapatos+para+hombre+botas+mocacine"
print(f"\n2. Navegando a: {url_zapatos}")
driver.get(url_zapatos)
time.sleep(5)

print(f"   URL actual: {driver.current_url}")
print(f"   Título: {driver.title}")

# 3. Verificar si hay CAPTCHA
print("\n3. Verificando bloqueos...")
if "captcha" in driver.page_source.lower():
    print("   ⚠️ SE DETECTÓ UN CAPTCHA - Debes resolverlo manualmente")
    driver.save_screenshot("captcha_detectado.png")
    print("   📸 Screenshot guardado: captcha_detectado.png")

# 4. Buscar cualquier contenido
print("\n4. Analizando contenido de la página...")

# Buscar texto que indique no resultados
no_resultados = driver.find_elements(By.XPATH, "//*[contains(text(), 'no encontr') or contains(text(), 'resultados')]")
if no_resultados:
    print(f"   Mensaje encontrado: {no_resultados[0].text}")

# Contar enlaces totales
total_links = len(driver.find_elements(By.TAG_NAME, "a"))
print(f"   Total de enlaces en la página: {total_links}")

# Buscar productos por diferentes métodos
metodos = [
    ("XPath //a[contains(@href, '/p/')]", By.XPATH, "//a[contains(@href, '/p/')]"),
    ("CSS a[href*='/p/']", By.CSS_SELECTOR, "a[href*='/p/']"),
    ("XPath //div[contains(@class, 'product')]", By.XPATH, "//div[contains(@class, 'product')]"),
    ("CSS .product-card", By.CSS_SELECTOR, ".product-card"),
]

for nombre, by, selector in metodos:
    elementos = driver.find_elements(by, selector)
    print(f"   {nombre}: {len(elementos)} elementos")

# 5. Tomar screenshot
driver.save_screenshot("diagnostico_final.png")
print(f"\n📸 Screenshot guardado: diagnostico_final.png")

# 6. Mostrar parte del HTML
print("\n5. Primeros 500 caracteres del body:")
print(driver.find_element(By.TAG_NAME, "body").text[:500])

input("\n👉 Presiona Enter para cerrar...")
driver.quit()