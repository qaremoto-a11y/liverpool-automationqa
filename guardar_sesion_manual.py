from utils.driver_factory import DriverFactory
from config import Config
import time

print("🔐 Iniciando sesión manual en Liverpool...")
driver = DriverFactory.get_driver()
driver.get(Config.BASE_URL)
time.sleep(3)

print("\n" + "="*60)
print("⚠️  AHORA DEBES INICIAR SESIÓN MANUALMENTE")
print("   - Ingresa tu email y contraseña")
print("   - Resuelve cualquier CAPTCHA")
print("   - Espera a que cargue tu cuenta (debes ver 'Mi cuenta' o tu nombre)")
print("="*60)
input("\n👉 Presiona ENTER después de haber iniciado sesión correctamente...")

# Guardar cookies
DriverFactory.save_session(driver)
print("✅ Sesión guardada exitosamente")

print("\n🚀 Ahora puedes ejecutar las pruebas automáticas")
driver.quit()