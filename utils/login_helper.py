from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os

class LoginHelper:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
    
    def login(self, email, password):
        """Intenta iniciar sesión con logs detallados y screenshots"""
        try:
            # Crear carpeta para screenshots si no existe
            os.makedirs("logs_login", exist_ok=True)
            
            print("🌐 Navegando a la página principal...")
            self.driver.get("https://www.liverpool.com.mx/tienda/home")
            self.driver.save_screenshot("logs_login/1_home.png")
            print("   Screenshot guardado: logs_login/1_home.png")
            time.sleep(3)
            
            print("🔍 Buscando botón 'Iniciar sesión'...")
            try:
                login_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Iniciar sesión')]"))
                )
                print("   ✅ Botón encontrado")
            except TimeoutException:
                print("   ❌ No se encontró el botón. Revisa el screenshot.")
                self.driver.save_screenshot("logs_login/error_boton_login.png")
                return False
            
            self.driver.execute_script("arguments[0].click();", login_btn)
            print("   ✅ Botón clickeado")
            self.driver.save_screenshot("logs_login/2_modal_abierto.png")
            time.sleep(2)
            
            print("📧 Buscando campo de email...")
            email_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_input.clear()
            email_input.send_keys(email)
            print(f"   ✅ Email ingresado: {email}")
            self.driver.save_screenshot("logs_login/3_email_ingresado.png")
            
            print("🔑 Buscando campo de contraseña...")
            password_input = self.driver.find_element(By.ID, "password")
            password_input.clear()
            password_input.send_keys(password)
            print("   ✅ Contraseña ingresada (oculta)")
            
            print("🚀 Buscando botón de envío...")
            submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_btn.click()
            print("   ✅ Formulario enviado")
            self.driver.save_screenshot("logs_login/4_envio_formulario.png")
            
            print("⏳ Esperando resultado del login...")
            time.sleep(5)
            self.driver.save_screenshot("logs_login/5_despues_login.png")
            
            # Verificar si apareció un CAPTCHA o mensaje de error
            if "captcha" in self.driver.page_source.lower():
                print("⚠️ Se detectó un CAPTCHA. El login automático fallará.")
                return False
            
            # Verificar login exitoso (buscar elemento de "Mi cuenta")
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Mi cuenta')]"))
                )
                print("✅ Login exitoso. Se encontró 'Mi cuenta'.")
                return True
            except TimeoutException:
                print("❌ No se encontró 'Mi cuenta' después del login.")
                return False
                
        except Exception as e:
            print(f"❌ Error general en login: {e}")
            self.driver.save_screenshot("logs_login/error_general.png")
            return False