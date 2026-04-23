import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # URL base del sitio
    BASE_URL = "https://www.liverpool.com.mx/tienda/home"
    
    # Credenciales seguras
    EMAIL = os.getenv("LIVERPOOL_EMAIL", "jesuszaratevallejo@gmail.com")
    PASSWORD = os.getenv("LIVERPOOL_PASSWORD", "")
    
    # Configuración de tiempos de espera
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 20
    PAGE_LOAD_TIMEOUT = 30
    
    # Lista de productos a probar
    PRODUCTS = {
        "zapatos_hombre": ["botas hombre", "mocasines hombre"],
        "perfumes": ["perfume"],
        "electronicos": ["laptop lenovo", "pantalla sony", "xbox"]
    }