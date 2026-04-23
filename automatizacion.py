import pytest
from utils.driver_factory import DriverFactory
from config import Config
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from functools import wraps

# ============== CONFIGURACIÓN ==============
TIMEOUTS = {
    'page_load': 20,        # Aumentado a 30 segundos
    'element_wait': 15,     # Aumentado a 20 segundos
    'short_pause': 0.5,
    'medium_pause': 2.0,    # Aumentado
    'long_pause': 3.0,      # Aumentado
}

# ============== DECORADORES ==============
def log_step(step_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"\n{'='*50}")
            print(f"📌 {step_name}")
            print(f"{'='*50}")
            result = func(*args, **kwargs)
            print(f"✅ {step_name} completado")
            return result
        return wrapper
    return decorator

# ============== CLASE PRODUCTO ==============
@dataclass
class Producto:
    nombre: str
    url: str
    tallas_preferidas: Optional[List[str]] = None
    id_producto: Optional[str] = None
    sku: Optional[str] = None
    tipo: str = "normal"
    
    def __post_init__(self):
        if not self.id_producto and self.url:
            self.id_producto = self._extraer_id()
            self.sku = self._extraer_sku()
        if "zapato" in self.nombre.lower() or "mocasín" in self.nombre.lower():
            self.tipo = "zapato"
        elif "xbox" in self.nombre.lower() or "consola" in self.nombre.lower():
            self.tipo = "consola"
    
    def _extraer_id(self) -> Optional[str]:
        patrones_ruta = [
            r'/pdp/[^/]+/(\d+)',
            r'/pdp/(\d+)',
            r'/tienda/pdp/[^/]+/(\d+)',
        ]
        for patron in patrones_ruta:
            match = re.search(patron, self.url)
            if match:
                return match.group(1)
        sku_value = self._extraer_sku()
        return sku_value if sku_value else None
    
    def _extraer_sku(self) -> Optional[str]:
        patron_sku = r'[?&]skuid=(\d+)'
        match = re.search(patron_sku, self.url)
        return match.group(1) if match else self.id_producto

# ============== CLASE PRINCIPAL ==============
class TestFlujoCompleto:
    SELECTORES = {
        'tallas': [
            "//button[contains(@class, 'size-option')]",
            "//div[contains(@class, 'size-selector')]//button",
            "//button[@data-size]",
            "//span[contains(@class, 'talla-value')]",
            "//button[contains(@class, 'size')]",
            "//div[contains(@class, 'variation')]//button",
            "//li[contains(@class, 'size')]//button",
            "//button[contains(text(), '27')]",  # Directo para talla 27
            "//span[contains(text(), '27')]",
        ],
        'agregar_carrito': [
            "//button[contains(text(), 'Agregar a mi bolsa')]",
            "//button[contains(text(), 'Agregar al carrito')]",
            "//button[@data-testid='add-to-cart']",
            "//button[contains(@class, 'add-to-cart')]",
            "//button[contains(text(), 'Agregar')]",
        ],
        'items_carrito': [
            "//div[contains(@class, 'cart-item')]",
            "//li[contains(@class, 'cart-item')]",
            "//div[contains(@class, 'product-item')]",
        ]
    }
    
    def setup_method(self):
        """Inicialización"""
        print("\n🚀 Inicializando el navegador...")
        self.driver = DriverFactory.get_driver()
        self.driver.set_page_load_timeout(TIMEOUTS['page_load'])
        self.driver.set_script_timeout(TIMEOUTS['page_load'])
        self.wait = WebDriverWait(self.driver, TIMEOUTS['element_wait'])
        self.actions = ActionChains(self.driver)
        self.productos: List[Producto] = []
        self._configurar_driver()
        self._cargar_sesion()
    
    def _configurar_driver(self):
        """Configuración del driver"""
        try:
            self.driver.execute_script("""
                var style = document.createElement('style');
                style.innerHTML = '* { transition: none !important; animation: none !important; }';
                document.head.appendChild(style);
                document.body.style.zoom = '100%';
            """)
        except:
            pass
    
    def _cargar_sesion(self):
        """Carga la sesión - ignorando errores de timeout"""
        from utils.driver_factory import DriverFactory as DF
        
        print("\n🔐 Verificando sesión...")
        
        try:
            # Intentar cargar la página principal con manejo de timeout
            self.driver.get(Config.BASE_URL)
            time.sleep(3)
        except:
            print("⚠️ Timeout al cargar página principal, continuando...")
        
        try:
            if not DF.load_session(self.driver):
                print("\n⚠️ No hay sesión guardada.")
                print("👉 Por favor, inicia sesión MANUALMENTE en el navegador")
                input("   Presiona ENTER cuando hayas iniciado sesión")
                DF.save_session(self.driver)
                print("✅ Sesión guardada")
        except Exception as e:
            print(f"⚠️ Error al cargar sesión: {str(e)[:100]}")
            print("👉 Por favor, asegúrate de haber iniciado sesión manualmente")
            input("   Presiona ENTER para continuar...")
    
    def teardown_method(self):
        """Limpieza final"""
        print("\n📌 El navegador se mantiene abierto")
    
    def _click_seguro(self, elemento):
        """Click seguro"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'auto'});", elemento)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", elemento)
            return True
        except:
            try:
                elemento.click()
                return True
            except:
                return False
    
    def _cargar_pagina_segura(self, url: str, intentos: int = 2) -> bool:
        """Carga una página con reintentos"""
        for i in range(intentos):
            try:
                print(f"   🌐 Cargando página (intento {i+1}/{intentos})...")
                self.driver.get(url)
                time.sleep(TIMEOUTS['medium_pause'])
                return True
            except TimeoutException:
                print(f"   ⚠️ Timeout en intento {i+1}")
                if i == intentos - 1:
                    return False
                continue
            except Exception as e:
                print(f"   ⚠️ Error: {str(e)[:50]}")
                return False
        return False
    
    def seleccionar_talla_27(self) -> bool:
        """Selecciona la talla 27 específicamente"""
        print("   🎯 Buscando talla 27...")
        
        time.sleep(TIMEOUTS['medium_pause'])
        
        # Buscar específicamente talla 27
        xpaths = [
            "//button[text()='27']",
            "//button[contains(text(), '27')]",
            "//span[text()='27']",
            "//span[contains(text(), '27')]",
            "//div[contains(text(), '27')]//button",
            "//li[contains(text(), '27')]",
        ]
        
        for xpath in xpaths:
            try:
                elementos = self.driver.find_elements(By.XPATH, xpath)
                for elem in elementos:
                    if elem.is_displayed():
                        print(f"   ✅ Encontrada talla 27")
                        if self._click_seguro(elem):
                            print(f"   ✅ Talla 27 seleccionada")
                            time.sleep(1)
                            return True
            except:
                continue
        
        # Si no encuentra, buscar cualquier talla
        print("   🔍 Buscando cualquier talla disponible...")
        try:
            for selector in self.SELECTORES['tallas']:
                elementos = self.driver.find_elements(By.XPATH, selector)
                for elem in elementos:
                    texto = elem.text.strip()
                    if texto and texto.isdigit() and 25 <= int(texto) <= 28:
                        print(f"   ✅ Talla {texto} encontrada")
                        if self._click_seguro(elem):
                            print(f"   ✅ Talla {texto} seleccionada")
                            return True
        except:
            pass
        
        print("   ⚠️ No se encontró ninguna talla")
        return False
    
    @log_step("Agregando producto")
    def agregar_producto_al_carrito(self, producto: Producto) -> bool:
        """Agrega producto al carrito"""
        print(f"📦 {producto.nombre}")
        print(f"   Tipo: {producto.tipo}")
        
        # Cargar página del producto
        if not self._cargar_pagina_segura(producto.url):
            print(f"   ❌ No se pudo cargar la página")
            return False
        
        # Para zapatos, seleccionar talla
        if producto.tipo == "zapato":
            print(f"   👟 Seleccionando talla...")
            if not self.seleccionar_talla_27():
                print(f"   ⚠️ No se pudo seleccionar talla")
                return False
        
        # Buscar botón de agregar
        print(f"   🛒 Buscando botón de agregar...")
        time.sleep(TIMEOUTS['short_pause'])
        
        agregar_btn = None
        for selector in self.SELECTORES['agregar_carrito']:
            try:
                agregar_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if agregar_btn:
                    print(f"   🔘 Botón encontrado: {agregar_btn.text}")
                    break
            except:
                continue
        
        if agregar_btn:
            if self._click_seguro(agregar_btn):
                time.sleep(TIMEOUTS['medium_pause'])
                print(f"   ✅ AGREGADO EXITOSAMENTE")
                return True
        
        print(f"   ❌ No se encontró botón de agregar")
        return False
    
    @log_step("Verificando carrito")
    def verificar_carrito(self):
        """Verifica el carrito"""
        url_carrito = "https://www.liverpool.com.mx/tienda/cart"
        
        print(f"🔗 Navegando al carrito...")
        if not self._cargar_pagina_segura(url_carrito):
            print("❌ No se pudo cargar el carrito")
            return
        
        self.driver.save_screenshot("carrito_final.png")
        print("📸 Screenshot guardado: carrito_final.png")
        
        # Buscar items
        items = []
        for selector in self.SELECTORES['items_carrito']:
            try:
                items = self.driver.find_elements(By.XPATH, selector)
                if items:
                    print(f"\n🛍️  Encontrados {len(items)} items en el carrito")
                    break
            except:
                continue
        
        if not items:
            print("\n⚠️ NO SE ENCONTRARON PRODUCTOS EN EL CARRITO")
            return
        
        print("\n📋 PRODUCTOS EN EL CARRITO:")
        for i, item in enumerate(items, 1):
            texto = item.text.strip()
            if texto:
                lineas = texto.split('\n')[:4]
                print(f"\n🛒 Producto {i}:")
                for linea in lineas:
                    if linea.strip():
                        print(f"   📝 {linea[:80]}")
    
    @log_step("Flujo completo")
    def test_flujo_completo_compra(self):
        """Flujo completo"""
        
        # Solo probar zapato y Xbox primero para depuración
        productos_a_comprar = [
            Producto(
                nombre="MOCASÍN LOB - Zapato para hombre",
                url="https://www.liverpool.com.mx/tienda/pdp/mocas%C3%ADn-lob-para-hombre/99984403436?skuid=1176440151",
                tallas_preferidas=["27"]
            ),
            Producto(
                nombre="Xbox Series X 1TB",
                url="https://www.liverpool.com.mx/tienda/pdp/consola-fija-xbox-one-series-x-de-1-tb-microsoft/1100132318"
            ),
            Producto(
                nombre="Perfume Azzaro The Most Wanted Intense",
                url="https://www.liverpool.com.mx/tienda/pdp/set-eau-de-parfum-azzaro-the-most-wanted-intense-para-hombre/1186100251"
            ),
            Producto(
                nombre="Laptop Lenovo 15.6\" Core i3",
                url="https://www.liverpool.com.mx/tienda/pdp/laptop-lenovo-82xb00c2us-15.6-pulgadas-full-hd-intel-core-i3-intel-uhd-graphics-8-gb-ram-128-gb-ssd/1187427513"
            ),
            Producto(
                nombre="Pantalla Sony OLED 65\" 4K Bravia",
                url="https://www.liverpool.com.mx/tienda/pdp/pantalla-smart-tv-sony-oled-de-65-pulgadas-4k-bravia-8mk2-k-65xr80m2-con-google-tv/1179253441"
            )
        ]
        
        print("\n" + "="*60)
        print("🚀 INICIANDO FLUJO DE COMPRA")
        print("="*60)
        
        # Agregar productos
        productos_ok = []
        for producto in productos_a_comprar:
            print(f"\n--- Procesando: {producto.nombre[:40]} ---")
            if self.agregar_producto_al_carrito(producto):
                self.productos.append(producto)
                productos_ok.append(producto.nombre)
                print(f"   ✅ {producto.nombre[:40]} - AGREGADO")
                time.sleep(TIMEOUTS['medium_pause'])
            else:
                print(f"   ❌ {producto.nombre[:40]} - ERROR")
        
        # Verificar carrito
        if self.productos:
            self.verificar_carrito()
            
            print("\n" + "-"*40)
            print("📊 RESUMEN FINAL:")
            print(f"   Productos agregados exitosamente: {len(self.productos)}")
            for prod in self.productos:
                print(f"      ✅ {prod.nombre[:50]}")
        else:
            print("\n❌ No se pudo agregar ningún producto")
        
        print("\n" + "="*60)
        print("🎉 FLUJO COMPLETADO")
        print("="*60)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])