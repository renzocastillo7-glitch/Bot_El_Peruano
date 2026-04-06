import os
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

def scrape_el_peruano_norms():
    """
    Usa Playwright y BeautifulSoup para extraer las normas del día
    y sus respectivos enlaces permanentes (URLs de El Peruano).
    """
    print("Iniciando extracción de Normas Legales desde El Peruano...")
    norms_list = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("https://diariooficial.elperuano.pe/Normas", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000) 
            
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Buscar el contenedor principal o directamente los artículos
            articles = soup.find_all("article", class_="edicionesoficiales_articulos")
            
            for art in articles:
                texto_div = art.find("div", class_="ediciones_texto")
                if not texto_div:
                    continue
                    
                texto = texto_div.get_text(separator=" ", strip=True)
                
                enlace = ""
                botones_div = art.find("div", class_="ediciones_botones")
                if botones_div:
                    btn_descarga = botones_div.find("input", attrs={"data-tipo": "DiNl"})
                    if btn_descarga and btn_descarga.has_attr("data-url"):
                        enlace = btn_descarga["data-url"]
                        
                if not enlace:
                    a_tag = texto_div.find("a")
                    if a_tag and a_tag.has_attr("href"):
                        enlace = a_tag["href"]
                    
                norms_list.append({
                    "text": texto,
                    "url": enlace,
                    "source": "El Peruano - Normas Legales",
                    "type": "norma"
                })
                
            if not articles:
                print("Advertencia: No se encontraron artículos con la clase 'edicionesoficiales_articulos'.")
                
        except Exception as e:
            print(f"Error durante el web scraping (Normas): {e}")
            
        finally:
            browser.close()
            
    return norms_list

def scrape_informes_sunat():
    """
    Extrae Informes de SUNAT de hoy o ayer.
    """
    print("Iniciando extracción de Informes SUNAT...")
    year = datetime.now().year
    url = f"https://www.sunat.gob.pe/legislacion/oficios/{year}/indcor.htm"
    informes_list = []
    
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            print(f"Error HTTP {response.status_code} al acceder a Informes SUNAT.")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Hoy y ayer en formato string para buscar en HTML (ej. 15/05/2026)
        hoy = datetime.now()
        ayer = hoy - timedelta(days=1)
        fechas_validas = [hoy.strftime("%d/%m/%Y"), hoy.strftime("%d/%m/%y"), ayer.strftime("%d/%m/%Y"), ayer.strftime("%d/%m/%y")]
        
        # Normalmente los informes están en tablas
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    text_row = row.get_text(separator=" ", strip=True)
                    # Verificar si la fila contiene alguna de las fechas válidas
                    if any(fecha in text_row for fecha in fechas_validas):
                        link_tag = row.find("a")
                        enlace = ""
                        if link_tag and link_tag.has_attr("href"):
                            href = link_tag["href"]
                            if href.startswith("http"): enlace = href
                            else: enlace = f"https://www.sunat.gob.pe/legislacion/oficios/{year}/" + href
                        
                        informes_list.append({
                            "text": text_row,
                            "url": enlace,
                            "source": "Informes SUNAT",
                            "type": "informe"
                        })
    except Exception as e:
        print(f"Error durante scraping Informes SUNAT: {e}")
        
    return informes_list

def extract_pdf_texto(pdf_path):
    """
    Extrae texto de un PDF enfocándose en resoluciones del Tribunal Fiscal.
    """
    if not HAS_FITZ:
        print("Advertencia: PyMuPDF no está instalado.")
        return ""
        
    texto_relevante = ""
    try:
        doc = fitz.open(pdf_path)
        for num_pagina in range(len(doc)):
            page = doc.load_page(num_pagina)
            texto = page.get_text("text")
            # Extraemos todo, el LLM filtrará o podemos filtrar
            texto_relevante += texto + "\n"
        doc.close()
        
        # Limitar longitud para no colapsar tokens
        return texto_relevante[:50000] 
        
    except Exception as e:
        print(f"Error extrayendo texto del PDF: {e}")
        return ""

def scrape_cuadernillos(tipo="Casaciones"):
    """
    Busca el último cuadernillo publicado (Casaciones o Precedentes).
    Si hay un PDF nuevo, lo descarga y extrae texto.
    """
    print(f"Iniciando búsqueda de cuadernillo: {tipo}...")
    url = f"https://diariooficial.elperuano.pe/{tipo}"
    resultados = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Buscar enlaces a PDF
            enlaces_pdf = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if ".pdf" in href.lower():
                    if href.startswith("http"): enlaces_pdf.append(href)
                    else: enlaces_pdf.append("https://diariooficial.elperuano.pe" + href)
            
            # También buscar inputs o botones con data-url a .pdf
            for tag in soup.find_all(attrs={"data-url": True}):
                d_url = tag["data-url"]
                if ".pdf" in d_url.lower():
                    if d_url.startswith("http"): enlaces_pdf.append(d_url)
                    else: enlaces_pdf.append("https://diariooficial.elperuano.pe" + d_url)
            
            if enlaces_pdf:
                # Tomar solo el primero asumiendo que es el más actual
                url_pdf = enlaces_pdf[0]
                
                # Descargar PDF a temporal
                pdf_path = "temp_cuadernillo.pdf"
                r = requests.get(url_pdf, timeout=30)
                if r.status_code == 200:
                    with open(pdf_path, "wb") as f:
                        f.write(r.content)
                        
                    texto = extract_pdf_texto(pdf_path)
                    
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                        
                    if texto.strip():
                        resultados.append({
                            "text": f"Cuadernillo {tipo} Reciente:\n{texto}",
                            "url": url_pdf,
                            "source": f"El Peruano - {tipo}",
                            "type": "cuadernillo"
                        })
            
        except Exception as e:
            print(f"Error durante web scraping de {tipo}: {e}")
        finally:
            browser.close()
            
    return resultados

if __name__ == "__main__":
    t = scrape_el_peruano_norms()
    print("Muestra extrada:", len(t))
