import time
import re
import os
import json
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# ============== CONFIGURACIÓN ==============
TIMEOUTS = {
    'page_load': 30,
    'element_wait': 20,
    'short_pause': 0.5,
    'medium_pause': 1.5,
    'long_pause': 2.5,
}

# ============== CONFIGURACIÓN DEL DRIVER ==============
def get_driver():
    """Configura y retorna el driver de Chrome con opciones anti-detección"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    chrome_options = Options()
    
    # Opciones para evitar detección
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    
    # User agent realista
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36")
    
    # Opciones experimentales
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Deshabilitar logs innecesarios
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Ejecutar script para ocultar webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Aumentar tiempos de carga
    driver.set_page_load_timeout(TIMEOUTS['page_load'])
    driver.set_script_timeout(TIMEOUTS['page_load'])
    
    return driver

# ============== SISTEMA DE EVIDENCIAS ==============
class EvidenciaManager:
    """Gestor de capturas de pantalla y evidencias"""
    
    def __init__(self, nombre_prueba: str, tipo_prueba: str = "funcional"):
        self.nombre_prueba = nombre_prueba
        self.tipo_prueba = tipo_prueba
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.evidencias = []
        
        # Crear estructura de carpetas
        self.carpeta_base = Path("evidencias_pruebas")
        self.carpeta_tipo = self.carpeta_base / tipo_prueba
        self.carpeta_sesion = self.carpeta_tipo / f"{nombre_prueba}_{self.timestamp}"
        
        # Subcarpetas
        self.carpeta_screenshots = self.carpeta_sesion / "screenshots"
        self.carpeta_logs = self.carpeta_sesion / "logs"
        self.carpeta_datos = self.carpeta_sesion / "datos"
        
        # Crear todas las carpetas
        for carpeta in [self.carpeta_screenshots, self.carpeta_logs, self.carpeta_datos]:
            carpeta.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📁 Sistema de evidencias inicializado:")
        print(f"   📂 Carpeta: {self.carpeta_sesion}")
        
        self._guardar_metadata()
    
    def _guardar_metadata(self):
        metadata = {
            "nombre_prueba": self.nombre_prueba,
            "tipo_prueba": self.tipo_prueba,
            "fecha_hora": self.timestamp,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
            "framework": "Selenium + Python",
            "estado": "en_ejecucion"
        }
        
        with open(self.carpeta_sesion / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def tomar_screenshot(self, driver, nombre_paso: str, descripcion: str = "") -> str:
        nombre_limpio = re.sub(r'[^\w\-_\.]', '_', nombre_paso)
        timestamp_detalle = datetime.now().strftime("%H%M%S_%f")[:-3]
        nombre_archivo = f"{nombre_limpio}_{timestamp_detalle}.png"
        ruta_completa = self.carpeta_screenshots / nombre_archivo
        
        try:
            driver.save_screenshot(str(ruta_completa))
            evidencia = {
                "paso": nombre_paso,
                "descripcion": descripcion,
                "archivo": nombre_archivo,
                "ruta": str(ruta_completa),
                "timestamp": datetime.now().isoformat()
            }
            self.evidencias.append(evidencia)
            print(f"   📸 Screenshot: {nombre_paso}")
            return str(ruta_completa)
        except Exception as e:
            print(f"   ❌ Error al tomar screenshot: {e}")
            return ""
    
    def guardar_log(self, mensaje: str, nivel: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] [{nivel}] {mensaje}"
        print(log_line)
        
        with open(self.carpeta_logs / "ejecucion.log", "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    
    def guardar_datos(self, nombre: str, datos: Any):
        ruta_json = self.carpeta_datos / f"{nombre}.json"
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
    
    def generar_reporte_html(self):
        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de Evidencias - {self.nombre_prueba}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        .metadata {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .evidencia {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .evidencia img {{ max-width: 100%; border: 1px solid #ccc; margin-top: 10px; }}
        .paso {{ font-weight: bold; color: #007bff; }}
        .descripcion {{ color: #666; margin: 5px 0; }}
        .timestamp {{ color: #999; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📸 Reporte de Evidencias - {self.nombre_prueba}</h1>
        <div class="metadata">
            <h3>Metadata de la Prueba</h3>
            <p><strong>Tipo:</strong> {self.tipo_prueba}</p>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Screenshots:</strong> {len(self.evidencias)}</p>
        </div>
        <h2>📷 Evidencias Capturadas</h2>
"""
        for ev in self.evidencias:
            html_content += f"""
        <div class="evidencia">
            <div class="paso">📌 {ev['paso']}</div>
            <div class="descripcion">{ev.get('descripcion', 'Sin descripción')}</div>
            <div class="timestamp">{ev['timestamp']}</div>
            <img src="screenshots/{ev['archivo']}" alt="{ev['paso']}" loading="lazy">
        </div>
"""
        html_content += """
    </div>
</body>
</html>"""
        
        with open(self.carpeta_sesion / "reporte_evidencias.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"\n📊 Reporte HTML generado: {self.carpeta_sesion / 'reporte_evidencias.html'}")
    
    def finalizar(self, estado: str = "completado"):
        with open(self.carpeta_sesion / "metadata.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        metadata["estado"] = estado
        metadata["total_evidencias"] = len(self.evidencias)
        metadata["fin"] = datetime.now().isoformat()
        
        with open(self.carpeta_sesion / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.guardar_datos("resumen_evidencias", self.evidencias)
        self.generar_reporte_html()
        
        print(f"\n✅ Evidencias guardadas en: {self.carpeta_sesion}")
        print(f"   📸 Screenshots: {len(self.evidencias)}")

# ============== CLASE PRODUCTO ==============
@dataclass
class Producto:
    nombre: str
    url: str
    tallas_preferidas: Optional[List[str]] = None
    tipo: str = "normal"

# ============== CLASE PRINCIPAL ==============
class AutomatizacionLiverpool:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.actions = None
        self.evidencias = None
        self.productos_agregados = []
        
    def iniciar(self):
        """Inicializa el navegador y las evidencias"""
        print("\n" + "="*60)
        print("🚀 INICIANDO AUTOMATIZACIÓN DE LIVERPOOL")
        print("="*60)
        
        # Inicializar evidencias
        self.evidencias = EvidenciaManager("flujo_completo_compra", "funcional")
        self.evidencias.guardar_log("Inicio de automatización", "INFO")
        
        # Inicializar driver
        print("\n🌐 Inicializando navegador...")
        try:
            self.driver = get_driver()
            self.wait = WebDriverWait(self.driver, TIMEOUTS['element_wait'])
            self.actions = ActionChains(self.driver)
            
            self.evidencias.tomar_screenshot(self.driver, "inicio_navegador", "Navegador iniciado")
        except Exception as e:
            self.evidencias.guardar_log(f"Error inicializando driver: {e}", "ERROR")
            raise
        
        # Manejar sesión
        self._manejar_sesion()
        
        self.evidencias.tomar_screenshot(self.driver, "sesion_iniciada", "Sesión lista")
        
    def _manejar_sesion(self):
        """Maneja el inicio de sesión con manejo de errores"""
        print("\n🔐 Verificando sesión...")
        self.evidencias.guardar_log("Verificando sesión", "INFO")
        
        try:
            # Intentar cargar la página con manejo de timeout
            print("   Cargando página principal...")
            self.driver.get("https://www.liverpool.com.mx")
            time.sleep(5)  # Espera adicional para que cargue completamente
            
            # Verificar si la página cargó
            if "liverpool" not in self.driver.title.lower():
                print("   ⚠️ La página no cargó completamente")
                self.evidencias.tomar_screenshot(self.driver, "carga_parcial", "Página no cargó completamente")
            
        except TimeoutException:
            print("   ⚠️ Timeout cargando la página, pero continuamos...")
            self.evidencias.tomar_screenshot(self.driver, "timeout_carga", "Timeout al cargar página")
        except Exception as e:
            print(f"   ⚠️ Error cargando página: {e}")
            self.evidencias.tomar_screenshot(self.driver, "error_carga", str(e))
        
        # Preguntar si ya tiene sesión
        respuesta = input("\n¿Ya has iniciado sesión en el navegador? (s/n): ")
        
        if respuesta.lower() != 's':
            print("\n👉 Por favor, inicia sesión MANUALMENTE en el navegador")
            print("   1. Busca 'Iniciar sesión' en la parte superior")
            print("   2. Ingresa tu correo y contraseña")
            print("   3. Completa la verificación si es necesario")
            self.evidencias.tomar_screenshot(self.driver, "esperando_login", "Esperando login manual")
            input("\n   Presiona ENTER cuando hayas iniciado sesión")
            
        self.evidencias.tomar_screenshot(self.driver, "login_completado", "Login verificado")
        print("✅ Sesión verificada")
        
    def _click_seguro(self, elemento):
        """Click seguro con múltiples métodos"""
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
                try:
                    self.actions.move_to_element(elemento).click().perform()
                    return True
                except:
                    return False
    
    def _esperar_elemento(self, by, selector, timeout=10):
        """Espera a que un elemento esté presente"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except:
            return None
    
    def _buscar_boton_agregar(self):
        """Busca el botón de agregar al carrito con múltiples selectores"""
        selectores = [
            "//button[contains(text(), 'Agregar al carrito')]",
            "//button[contains(text(), 'Agregar')]",
            "//button[@data-testid='add-to-cart']",
            "//button[contains(@class, 'add-to-cart')]",
            "//button[contains(@class, 'buy-button')]",
            "//button[contains(@id, 'add-to-cart')]",
            "//a[contains(text(), 'Agregar')]",
        ]
        
        for selector in selectores:
            try:
                boton = self.driver.find_element(By.XPATH, selector)
                if boton and boton.is_displayed():
                    return boton
            except:
                continue
        
        # Buscar cualquier botón que contenga palabras clave
        try:
            botones = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in botones:
                texto = btn.text.lower()
                if any(palabra in texto for palabra in ["agregar", "add", "comprar", "carrito"]):
                    if btn.is_displayed():
                        return btn
        except:
            pass
        
        return None
    
    def _seleccionar_talla(self, talla_deseada="27"):
        """Selecciona una talla específica"""
        print(f"   🎯 Buscando talla {talla_deseada}...")
        
        # Esperar a que los selectores de talla estén presentes
        time.sleep(2)
        
        # Buscar botón de la talla
        xpaths = [
            f"//button[contains(text(), '{talla_deseada}')]",
            f"//span[contains(text(), '{talla_deseada}')]",
            f"//button[@data-size='{talla_deseada}']",
            f"//label[contains(text(), '{talla_deseada}')]",
            f"//div[contains(@class, 'size')]//button[contains(text(), '{talla_deseada}')]",
        ]
        
        for xpath in xpaths:
            try:
                elementos = self.driver.find_elements(By.XPATH, xpath)
                for elem in elementos:
                    if elem.is_displayed() and elem.is_enabled():
                        if self._click_seguro(elem):
                            print(f"   ✅ Talla {talla_deseada} seleccionada")
                            time.sleep(1)
                            return True
            except:
                continue
        
        # Buscar cualquier talla disponible
        try:
            # Buscar contenedor de tallas
            contenedores = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'size')] | //div[contains(@class, 'talla')]")
            for contenedor in contenedores:
                botones = contenedor.find_elements(By.TAG_NAME, "button")
                for btn in botones:
                    texto = btn.text.strip()
                    if texto and (texto.isdigit() or '.' in texto):
                        if btn.is_displayed() and btn.is_enabled():
                            if self._click_seguro(btn):
                                print(f"   ✅ Talla {texto} seleccionada")
                                time.sleep(1)
                                return True
        except:
            pass
        
        print(f"   ⚠️ No se encontró talla disponible")
        return False
    
    def agregar_producto(self, producto: Producto) -> bool:
        """Agrega un producto al carrito"""
        print(f"\n📦 Procesando: {producto.nombre}")
        
        try:
            # Navegar al producto
            print(f"   🌐 Cargando página...")
            self.driver.get(producto.url)
            time.sleep(4)  # Esperar a que cargue completamente
            
            self.evidencias.tomar_screenshot(
                self.driver, 
                f"producto_{producto.nombre[:30]}", 
                f"Página: {producto.nombre}"
            )
            
            # Si es zapato, seleccionar talla
            if producto.tipo == "zapato":
                if not self._seleccionar_talla("27"):
                    print("   ⚠️ No se pudo seleccionar talla, intentando de todas formas...")
                    self.evidencias.guardar_log(f"No se encontró talla para {producto.nombre}", "WARNING")
            
            # Buscar y hacer clic en agregar
            print(f"   🛒 Buscando botón de agregar...")
            time.sleep(2)  # Esperar a que el botón esté disponible
            
            boton_agregar = self._buscar_boton_agregar()
            
            if boton_agregar:
                print(f"   🔘 Botón encontrado: '{boton_agregar.text[:30] if boton_agregar.text else 'Sin texto'}'")
                if self._click_seguro(boton_agregar):
                    time.sleep(3)  # Esperar a que se agregue
                    print(f"   ✅ PRODUCTO AGREGADO EXITOSAMENTE")
                    
                    self.evidencias.tomar_screenshot(
                        self.driver, 
                        f"agregado_{producto.nombre[:30]}", 
                        f"Producto agregado: {producto.nombre}"
                    )
                    
                    self.evidencias.guardar_log(f"Agregado: {producto.nombre}", "INFO")
                    return True
            
            print(f"   ❌ No se encontró botón de agregar")
            self.evidencias.guardar_log(f"No se encontró botón para {producto.nombre}", "ERROR")
            return False
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            self.evidencias.guardar_log(f"Error con {producto.nombre}: {e}", "ERROR")
            self.evidencias.tomar_screenshot(self.driver, f"error_{producto.nombre[:30]}", str(e))
            return False
    
    def verificar_carrito(self):
        """Verifica el contenido del carrito"""
        print("\n" + "="*50)
        print("🛒 VERIFICANDO CARRITO DE COMPRAS")
        print("="*50)
        
        try:
            # Ir al carrito
            print("   Navegando al carrito...")
            self.driver.get("https://www.liverpool.com.mx/tienda/cart")
            time.sleep(3)
            
            self.evidencias.tomar_screenshot(self.driver, "carrito_final", "Vista del carrito")
            
            # Buscar items en el carrito
            selectores_items = [
                "//div[contains(@class, 'cart-item')]",
                "//li[contains(@class, 'cart-item')]",
                "//div[contains(@class, 'product-item')]",
                "//div[contains(@class, 'item')]",
                "//tr[contains(@class, 'item')]"
            ]
            
            items = []
            for selector in selectores_items:
                try:
                    items = self.driver.find_elements(By.XPATH, selector)
                    if items:
                        print(f"   Encontrados {len(items)} items usando selector: {selector[:50]}")
                        break
                except:
                    continue
            
            print(f"\n📊 RESULTADOS:")
            print(f"   Productos intentados: {len(self.productos_agregados)}")
            print(f"   Items encontrados en carrito: {len(items)}")
            
            if items:
                print(f"\n   ✅ Productos en el carrito:")
                for i, prod in enumerate(self.productos_agregados, 1):
                    print(f"      {i}. {prod[:50]}")
            else:
                print(f"\n   ⚠️ No se encontraron productos en el carrito")
                # Mostrar texto de la página para debug
                body_text = self.driver.find_element(By.TAG_NAME, "body").text[:500]
                print(f"   Texto de la página: {body_text[:200]}...")
            
            return len(items)
            
        except Exception as e:
            print(f"   ❌ Error verificando carrito: {e}")
            self.evidencias.guardar_log(f"Error verificando carrito: {e}", "ERROR")
            return 0
    
    def ejecutar_flujo(self):
        """Ejecuta el flujo completo de compra"""
        try:
            # Iniciar
            self.iniciar()
            
            # Lista de productos a comprar
            productos = [
                Producto(
                    nombre="BOTÍN DOCKERS DE PIEL PARA HOMBRE",
                    url="https://www.liverpool.com.mx/tienda/pdp/bot%C3%ADn-dockers-de-piel-para-hombre/1179271907?skuid=1179272004",
                    tallas_preferidas=["27", "26", "28"],
                    tipo="zapato"
                ),
                Producto(
                    nombre="Perfume Azzaro The Most Wanted Intense",
                    url="https://www.liverpool.com.mx/tienda/pdp/set-eau-de-parfum-azzaro-the-most-wanted-intense-para-hombre/1186100251",
                    tipo="normal"
                ),
                Producto(
                    nombre="Laptop Lenovo 15.6\" Core i3",
                    url="https://www.liverpool.com.mx/tienda/pdp/laptop-lenovo-82xb00c2us-15.6-pulgadas-full-hd-intel-core-i3-intel-uhd-graphics-8-gb-ram-128-gb-ssd/1187427513",
                    tipo="normal"
                ),
                Producto(
                    nombre="Pantalla Sony OLED 65\" 4K Bravia",
                    url="https://www.liverpool.com.mx/tienda/pdp/pantalla-smart-tv-sony-oled-de-65-pulgadas-4k-bravia-8mk2-k-65xr80m2-con-google-tv/1179253441",
                    tipo="normal"
                ),
                Producto(
                    nombre="Xbox Series X 1TB",
                    url="https://www.liverpool.com.mx/tienda/pdp/consola-fija-xbox-one-series-x-de-1-tb-microsoft/1100132318",
                    tipo="normal"
                )
            ]
            
            # Agregar cada producto
            print("\n" + "="*60)
            print("🛍️  AGREGANDO PRODUCTOS AL CARRITO")
            print("="*60)
            
            for i, producto in enumerate(productos, 1):
                print(f"\n--- Producto {i} de {len(productos)} ---")
                
                if self.agregar_producto(producto):
                    self.productos_agregados.append(producto.nombre)
                else:
                    print(f"   ❌ No se pudo agregar: {producto.nombre}")
                
                time.sleep(2)  # Pausa entre productos
            
            # Verificar carrito
            total_items = self.verificar_carrito()
            
            # Mostrar resumen final
            print("\n" + "="*60)
            print("📊 RESUMEN FINAL DE LA PRUEBA")
            print("="*60)
            print(f"   ✅ Productos agregados: {len(self.productos_agregados)}/{len(productos)}")
            print(f"   🛒 Items en carrito: {total_items}")
            
            if len(self.productos_agregados) == len(productos):
                print(f"\n   🎉 ¡TODOS LOS PRODUCTOS FUERON AGREGADOS EXITOSAMENTE!")
            else:
                print(f"\n   ⚠️ Algunos productos no se pudieron agregar")
                print(f"   Productos exitosos: {len(self.productos_agregados)}")
                print(f"   Productos fallidos: {len(productos) - len(self.productos_agregados)}")
            
            # Preguntar si quiere ver el carrito
            ver_carrito = input(f"\n¿Quieres ver el carrito en el navegador? (s/n): ")
            if ver_carrito.lower() == 's':
                self.driver.get("https://www.liverpool.com.mx/tienda/cart")
                print("\n🔍 Revisa el carrito en el navegador...")
                input("\nPresiona ENTER para finalizar...")
            
        except Exception as e:
            print(f"\n❌ Error en la ejecución: {e}")
            if self.evidencias:
                self.evidencias.tomar_screenshot(self.driver, "error_general", str(e))
        
        finally:
            # Finalizar evidencias
            if self.evidencias:
                estado = "completado" if len(self.productos_agregados) > 0 else "fallido"
                self.evidencias.finalizar(estado)
            
            # Preguntar si cerrar navegador
            cerrar = input(f"\n¿Deseas cerrar el navegador? (s/n): ")
            if cerrar.lower() == 's' and self.driver:
                self.driver.quit()
                print("👋 Navegador cerrado")
            else:
                print("\n📌 El navegador permanece abierto para revisión manual")
            
            print("\n" + "="*60)
            print("🏁 AUTOMATIZACIÓN FINALIZADA")
            print("="*60)
            print(f"📁 Evidencias guardadas en: evidencias_pruebas/")

# ============== PUNTO DE ENTRADA PRINCIPAL ==============
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     AUTOMATIZACIÓN DE COMPRAS - LIVERPOOL                ║
    ║     Versión 1.0 - Selenium Python                        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Ejecutar automatización
    automator = AutomatizacionLiverpool()
    automator.ejecutar_flujo()