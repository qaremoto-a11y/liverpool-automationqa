import pytest
from utils.driver_factory import DriverFactory
from utils.login_helper import LoginHelper
from liverpool_automation import LiverpoolAutomation
from config import Config
import time

class TestPositiveFlow:
    def setup_method(self):
        self.driver = DriverFactory.get_driver()
        self.login_helper = LoginHelper(self.driver)
        self.automation = LiverpoolAutomation(self.driver)
        
        # Intentar cargar sesión guardada
        if not DriverFactory.load_session(self.driver):
            # Si no hay sesión, pedimos login manual UNA SOLA VEZ
            print("\n" + "="*50)
            print("⚠️  No se encontró una sesión guardada.")
            print("🔓 Por favor, inicia sesión MANUALMENTE en el navegador que se abrirá.")
            print("   - Resuelve cualquier CAPTCHA si aparece.")
            print("   - Una vez que veas tu nombre de usuario o 'Mi cuenta', vuelve aquí.")
            print("="*50)
            input("👉 Presiona ENTER después de haber iniciado sesión correctamente...")
            
            # Guardar la sesión para futuras ejecuciones
            DriverFactory.save_session(self.driver)
            print("✅ Sesión guardada correctamente. Las próximas ejecuciones serán automáticas.\n")
    
    def teardown_method(self):
        # No guardamos sesión cada vez, ya está guardada
        self.driver.quit()
    
    def test_full_shopping_flow(self):
        """Flujo completo de compra"""
        results = self.automation.complete_shopping_flow()
        total_added = sum(1 for cat in results.values() for r in cat if r["agregado"])
        assert total_added > 0, "No se agregaron productos"
        print(f"\n✅ {total_added} productos agregados correctamente")
    
    def test_single_product_flow(self):
        """Compra de un solo producto"""
        product = "xbox"
        assert self.automation.search_product(product)
        assert self.automation.select_first_product()
        assert self.automation.add_to_cart()
        assert self.automation.go_to_cart()
        assert self.automation.proceed_to_checkout()
        print("✅ Flujo de producto único completado")