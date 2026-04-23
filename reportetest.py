import pytest
from utils.driver_factory import DriverFactory
from config import Config
import time
import re
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Callable
from functools import wraps

# ============== CONFIGURACIÓN ==============
TIMEOUTS = {
    'page_load': 20,
    'element_wait': 15,
    'short_pause': 0.5,
    'medium_pause': 2.0,
    'long_pause': 3.0,
}

# ============== CONFIGURACIÓN DE EVIDENCIAS ==============
EVIDENCIAS_DIR = "evidencias_pruebas/funcional"

def ensure_evidencias_dir():
    """Asegura que exista el directorio de evidencias"""
    if not os.path.exists(EVIDENCIAS_DIR):
        os.makedirs(EVIDENCIAS_DIR)
        print(f"📁 Creado directorio de evidencias: {EVIDENCIAS_DIR}")

def tomar_screenshot(driver, nombre: str, timestamp: bool = True):
    """Toma una captura de pantalla y la guarda en la carpeta de evidencias"""
    if driver is None:
        print(f"⚠️ No se pudo tomar screenshot '{nombre}': driver no disponible")
        return None
    
    ensure_evidencias_dir()
    
    if timestamp:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{nombre}_{timestamp_str}.png"
    else:
        nombre_archivo = f"{nombre}.png"
    
    # Limpiar nombre de archivo (quitar caracteres inválidos)
    nombre_archivo = re.sub(r'[<>:"/\\|?*]', '_', nombre_archivo)
    ruta_completa = os.path.join(EVIDENCIAS_DIR, nombre_archivo)
    
    try:
        driver.save_screenshot(ruta_completa)
        print(f"📸 Screenshot guardado: {ruta_completa}")
        return ruta_completa
    except Exception as e:
        print(f"❌ Error al guardar screenshot '{nombre}': {str(e)}")
        return None

# ============== DECORADORES ==============
def log_step(step_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            print(f"\n{'='*50}")
            print(f"📌 {step_name}")
            print(f"{'='*50}")
            
            # Tomar screenshot antes del paso
            if hasattr(self, 'driver'):
                tomar_screenshot(self.driver, f"antes_{step_name.lower().replace(' ', '_')}")
            
            result = func(self, *args, **kwargs)
            
            # Tomar screenshot después del paso
            if hasattr(self, 'driver'):
                tomar_screenshot(self.driver, f"despues_{step_name.lower().replace(' ', '_')}")
            
            print(f"✅ {step_name} completado")
            return result
        return wrapper
    return decorator

def screenshot_on_error(func):
    """Decorador para tomar screenshot cuando ocurre un error"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # Tomar screenshot del error
            if hasattr(self, 'driver'):
                nombre_error = f"error_{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                tomar_screenshot(self.driver, nombre_error, timestamp=False)
            print(f"❌ Error en {func.__name__}: {str(e)}")
            raise
    return wrapper

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
            "//button[contains(text(), '27')]",
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
        ensure_evidencias_dir()
        
        self.driver = DriverFactory.get_driver()
        self.driver.set_page_load_timeout(TIMEOUTS['page_load'])
        self.driver.set_script_timeout(TIMEOUTS['page_load'])
        self.wait = WebDriverWait(self.driver, TIMEOUTS['element_wait'])
        self.actions = ActionChains(self.driver)
        self.productos: List[Producto] = []
        self._configurar_driver()
        self._cargar_sesion()
        
        # Screenshot de inicio
        tomar_screenshot(self.driver, "inicio_prueba")
    
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
        tomar_screenshot(self.driver, "verificando_sesion")
        
        try:
            self.driver.get(Config.BASE_URL)
            time.sleep(3)
            tomar_screenshot(self.driver, "pagina_principal_cargada")
        except:
            print("⚠️ Timeout al cargar página principal, continuando...")
            tomar_screenshot(self.driver, "timeout_pagina_principal")
        
        try:
            if not DF.load_session(self.driver):
                print("\n⚠️ No hay sesión guardada.")
                print("👉 Por favor, inicia sesión MANUALMENTE en el navegador")
                tomar_screenshot(self.driver, "sesion_no_guardada")
                input("   Presiona ENTER cuando hayas iniciado sesión")
                DF.save_session(self.driver)
                print("✅ Sesión guardada")
                tomar_screenshot(self.driver, "sesion_guardada")
        except Exception as e:
            print(f"⚠️ Error al cargar sesión: {str(e)[:100]}")
            print("👉 Por favor, asegúrate de haber iniciado sesión manualmente")
            tomar_screenshot(self.driver, "error_sesion")
            input("   Presiona ENTER para continuar...")
    
    def teardown_method(self):
        """Limpieza final"""
        print("\n📌 El navegador se mantiene abierto")
        if hasattr(self, 'driver'):
            tomar_screenshot(self.driver, "fin_prueba")
    
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
                tomar_screenshot(self.driver, f"pagina_cargada_{i+1}")
                return True
            except TimeoutException:
                print(f"   ⚠️ Timeout en intento {i+1}")
                tomar_screenshot(self.driver, f"timeout_intento_{i+1}")
                if i == intentos - 1:
                    return False
                continue
            except Exception as e:
                print(f"   ⚠️ Error: {str(e)[:50]}")
                tomar_screenshot(self.driver, f"error_carga_pagina")
                return False
        return False
    
    @screenshot_on_error
    def seleccionar_talla_27(self) -> bool:
        """Selecciona la talla 27 específicamente"""
        print("   🎯 Buscando talla 27...")
        
        time.sleep(TIMEOUTS['medium_pause'])
        tomar_screenshot(self.driver, "buscando_talla")
        
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
                        tomar_screenshot(self.driver, "talla_27_encontrada")
                        if self._click_seguro(elem):
                            print(f"   ✅ Talla 27 seleccionada")
                            time.sleep(1)
                            tomar_screenshot(self.driver, "talla_27_seleccionada")
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
                        tomar_screenshot(self.driver, f"talla_{texto}_encontrada")
                        if self._click_seguro(elem):
                            print(f"   ✅ Talla {texto} seleccionada")
                            tomar_screenshot(self.driver, f"talla_{texto}_seleccionada")
                            return True
        except:
            pass
        
        print("   ⚠️ No se encontró ninguna talla")
        tomar_screenshot(self.driver, "talla_no_encontrada")
        return False
    
    @log_step("Agregando producto")
    @screenshot_on_error
    def agregar_producto_al_carrito(self, producto: Producto) -> bool:
        """Agrega producto al carrito"""
        print(f"📦 {producto.nombre}")
        print(f"   Tipo: {producto.tipo}")
        
        # Tomar screenshot del producto antes de procesar
        nombre_limpio = re.sub(r'[^\w\s-]', '', producto.nombre)[:50]
        tomar_screenshot(self.driver, f"inicio_agregar_{nombre_limpio}")
        
        # Cargar página del producto
        if not self._cargar_pagina_segura(producto.url):
            print(f"   ❌ No se pudo cargar la página")
            tomar_screenshot(self.driver, f"error_carga_{nombre_limpio}")
            return False
        
        # Para zapatos, seleccionar talla
        if producto.tipo == "zapato":
            print(f"   👟 Seleccionando talla...")
            tomar_screenshot(self.driver, f"antes_seleccion_talla_{nombre_limpio}")
            if not self.seleccionar_talla_27():
                print(f"   ⚠️ No se pudo seleccionar talla")
                tomar_screenshot(self.driver, f"error_talla_{nombre_limpio}")
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
                    tomar_screenshot(self.driver, f"boton_agregar_encontrado_{nombre_limpio}")
                    break
            except:
                continue
        
        if agregar_btn:
            tomar_screenshot(self.driver, f"antes_click_agregar_{nombre_limpio}")
            if self._click_seguro(agregar_btn):
                time.sleep(TIMEOUTS['medium_pause'])
                print(f"   ✅ AGREGADO EXITOSAMENTE")
                tomar_screenshot(self.driver, f"producto_agregado_{nombre_limpio}")
                return True
        
        print(f"   ❌ No se encontró botón de agregar")
        tomar_screenshot(self.driver, f"error_boton_no_encontrado_{nombre_limpio}")
        return False
    
    @log_step("Verificando carrito")
    @screenshot_on_error
    def verificar_carrito(self):
        """Verifica el carrito"""
        url_carrito = "https://www.liverpool.com.mx/tienda/cart"
        
        print(f"🔗 Navegando al carrito...")
        tomar_screenshot(self.driver, "antes_ir_carrito")
        
        if not self._cargar_pagina_segura(url_carrito):
            print("❌ No se pudo cargar el carrito")
            tomar_screenshot(self.driver, "error_carga_carrito")
            return
        
        tomar_screenshot(self.driver, "carrito_cargado")
        
        # Buscar items
        items = []
        for selector in self.SELECTORES['items_carrito']:
            try:
                items = self.driver.find_elements(By.XPATH, selector)
                if items:
                    print(f"\n🛍️  Encontrados {len(items)} items en el carrito")
                    tomar_screenshot(self.driver, f"carrito_con_{len(items)}_items")
                    break
            except:
                continue
        
        if not items:
            print("\n⚠️ NO SE ENCONTRARON PRODUCTOS EN EL CARRITO")
            tomar_screenshot(self.driver, "carrito_vacio")
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
        
        tomar_screenshot(self.driver, "verificacion_carrito_final")
    
    @log_step("Flujo completo")
    @screenshot_on_error
    def test_flujo_completo_compra(self):
        """Flujo completo"""
        
        # Productos a comprar
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
        tomar_screenshot(self.driver, "inicio_flujo_completo")
        
        # Agregar productos
        productos_ok = []
        for idx, producto in enumerate(productos_a_comprar, 1):
            print(f"\n--- Procesando ({idx}/{len(productos_a_comprar)}): {producto.nombre[:40]} ---")
            tomar_screenshot(self.driver, f"inicio_producto_{idx}")
            
            if self.agregar_producto_al_carrito(producto):
                self.productos.append(producto)
                productos_ok.append(producto.nombre)
                print(f"   ✅ {producto.nombre[:40]} - AGREGADO")
                tomar_screenshot(self.driver, f"producto_{idx}_agregado_exitoso")
                time.sleep(TIMEOUTS['medium_pause'])
            else:
                print(f"   ❌ {producto.nombre[:40]} - ERROR")
                tomar_screenshot(self.driver, f"producto_{idx}_error")
        
        # Verificar carrito
        if self.productos:
            self.verificar_carrito()
            
            print("\n" + "-"*40)
            print("📊 RESUMEN FINAL:")
            print(f"   Productos agregados exitosamente: {len(self.productos)}")
            for prod in self.productos:
                print(f"      ✅ {prod.nombre[:50]}")
            
            tomar_screenshot(self.driver, "resumen_final_exitoso")
        else:
            print("\n❌ No se pudo agregar ningún producto")
            tomar_screenshot(self.driver, "resumen_final_sin_productos")
        
        print("\n" + "="*60)
        print("🎉 FLUJO COMPLETADO")
        print("="*60)
        tomar_screenshot(self.driver, "flujo_completo_finalizado")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])