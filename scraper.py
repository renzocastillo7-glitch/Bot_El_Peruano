import os
import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

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
                a_tag = texto_div.find("a")
                if a_tag and a_tag.has_attr("href"):
                    enlace = a_tag["href"]
                    
                norms_list.append({
                    "text": texto,
                    "url": enlace
                })
                
            if not articles:
                print("Advertencia: No se encontraron artículos con la clase 'edicionesoficiales_articulos'.")
                
        except Exception as e:
            print(f"Error durante el web scraping: {e}")
            
        finally:
            browser.close()
            
    # Convertir a JSON string formateado, tomando solo los primeros 15000 caracteres de JSON 
    # (El Peruano puede tener cientos, cortamos para no exceder tokens, aunque Claude soporta mucho más)
    json_result = json.dumps(norms_list, ensure_ascii=False, indent=2)
    return json_result[:30000]

if __name__ == "__main__":
    t = scrape_el_peruano_norms()
    print("Muestra extraída (JSON):\n", "-"*40)
    print(t[:1000])
    print("-"*40)
    print(f"Total de caracteres extraídos: {len(t)}")
