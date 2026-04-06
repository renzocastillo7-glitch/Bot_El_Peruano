import os
import io
import time
import base64
import requests
from playwright.sync_api import sync_playwright

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def generate_dalle_image(prompt, output_filename="temp_illustration.png"):
    if not HAS_OPENAI:
        print("[!] OpenAI no está instalado.")
        return None
        
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[!] OPENAI_API_KEY no encontrada.")
        return None
        
    try:
        client = OpenAI(api_key=api_key)
        print(f"Generando ilustración 3D con DALL-E 3... Prompt: {prompt[:50]}...")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt + " Clean white background, 3d isometric render, corporate clean style, high quality, soft shading, no text in image.",
            size="1024x1024",
            quality="hd",
            n=1
        )
        img_url = response.data[0].url
        img_data = requests.get(img_url, timeout=30).content
        
        with open(output_filename, "wb") as f:
            f.write(img_data)
            
        return output_filename
    except Exception as e:
        print(f"Error generando imagen DALL-E: {e}")
        return None

def generate_infographic(infographic_data, infographic_type="alerta", output_path="infografia.png"):
    print("Preparando renderizado HTML + CSS + Playwright...")
    
    # Colores corporativos basados en tipo
    t_lower = infographic_type.lower()
    bg_gradient = "linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%)"
    accent_color = "#102a43"
    primary_color = "#00e5ff" # Default cyan
    
    if 'guía' in t_lower:
        primary_color = "#f59e0b"
    elif 'comparativo' in t_lower:
        primary_color = "#3b82f6"
    elif 'cronograma' in t_lower:
        primary_color = "#10b981"
        
    # Obtener Ilustración 3D (DALL-E) si hay API
    ill_prompt = infographic_data.get("illustration_prompt", "3d isometric corporate tax document folder glowing")
    dalle_img_path = generate_dalle_image(ill_prompt)
    
    b64_image = ""
    if dalle_img_path and os.path.exists(dalle_img_path):
        b64_image = f"data:image/png;base64,{get_base64_image(dalle_img_path)}"
        os.remove(dalle_img_path)
    
    # Procesar bloques a tarjetas HTML
    blocks = infographic_data.get("blocks", [])
    
    # Construir las tarjetas directamente en dos columnas (Izquierda y Derecha)
    cards_html_left = ""
    cards_html_right = ""
    
    for idx, block in enumerate(blocks[:6]):
        c_title = block.get("title", "Dato Clave")
        c_text = block.get("content", "")
        c_icon = block.get("icon", "📌")

        block_html = f"""
        <div class="floating-block">
            <div class="block-header">
                <span class="icon">{c_icon}</span>
                <div class="block-title">{c_title}</div>
            </div>
            <div class="block-body">{c_text}</div>
        </div>
        """
        
        # Asignar pares a la izquierda, impares a la derecha
        if idx % 2 == 0:
            cards_html_left += block_html
        else:
            cards_html_right += block_html
        
    title = infographic_data.get("title", f"REPORTE: {infographic_type.upper()}")
    subtitle = infographic_data.get("subtitle", "")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&family=Roboto:wght@400;500&display=swap" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 50px 60px;
                font-family: 'Roboto', sans-serif;
                background: radial-gradient(circle at center, #ffffff 0%, #f1f5f9 100%);
                width: 1080px;
                min-height: 1080px;
                height: auto;
                color: #1e293b;
                display: flex;
                flex-direction: column;
                align-items: center;
                box-sizing: border-box;
                position: relative;
            }}
            .header {{
                text-align: center;
                margin-bottom: 50px;
                width: 100%;
                z-index: 10;
            }}
            .title {{
                font-family: 'Montserrat', sans-serif;
                font-size: 70px;
                font-weight: 900;
                color: #0f172a;
                line-height: 1.1;
                margin-bottom: 15px;
                text-transform: uppercase;
                letter-spacing: -1px;
            }}
            .subtitle {{
                font-family: 'Montserrat', sans-serif;
                font-size: 32px;
                font-weight: 700;
                color: {primary_color};
            }}
            
            .infographic-core {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
                position: relative;
                margin-top: 10px;
            }}
            
            /* The DALL-E Image integrated as a central orb/feature */
            .center-art {{
                width: 440px;
                height: 440px;
                background-image: url('{b64_image}');
                background-size: cover;
                background-position: center;
                border-radius: 50%;
                box-shadow: 0 30px 60px rgba(0,0,0,0.15), 0 0 0 15px rgba(255,255,255,0.6);
                z-index: 5;
                position: relative;
            }}
            
            .side-column {{
                display: flex;
                flex-direction: column;
                gap: 50px;
                width: 290px;
                z-index: 10;
            }}
            
            .floating-block {{
                background: transparent;
                border: none;
                box-shadow: none;
                padding: 0;
                position: relative;
            }}
            
            .block-header {{
                display: flex;
                align-items: center;
                margin-bottom: 10px;
            }}
            
            .icon {{
                font-size: 38px;
                margin-right: 12px;
                filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
            }}
            
            .block-title {{
                font-family: 'Montserrat', sans-serif;
                font-size: 26px;
                font-weight: 800;
                color: #0f172a;
                line-height: 1.2;
            }}
            
            .block-body {{
                font-size: 22px;
                color: #475569;
                line-height: 1.5;
                font-weight: 400;
            }}
            
            /* Decorative connecting lines in the background */
            .decorative-lines {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 800px;
                height: 2px;
                background: repeating-linear-gradient(90deg, #cbd5e1 0, #cbd5e1 10px, transparent 10px, transparent 20px);
                z-index: 1;
            }}
            .decorative-lines.vertical {{
                width: 2px;
                height: 600px;
                background: repeating-linear-gradient(0deg, #cbd5e1 0, #cbd5e1 10px, transparent 10px, transparent 20px);
            }}
            
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">{title}</div>
            <div class="subtitle">{subtitle}</div>
        </div>
        
        <div class="infographic-core">
            <div class="decorative-lines"></div>
            
            <!-- Izquierda -->
            <div class="side-column" id="left-col">
                {cards_html_left}
            </div>
            
            <!-- Centro: Imagen -->
            <div class="center-art"></div>
            
            <!-- Derecha -->
            <div class="side-column" id="right-col">
                {cards_html_right}
            </div>
        </div>
    </body>
    </html>
    """
    
    html_file = "temp_render.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("Renderizando HTML a PNG resolucion HD...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1080, 'height': 800}, device_scale_factor=2)
        # Load local HTML
        page.goto(f"file://{os.path.abspath(html_file)}", wait_until="networkidle")
        # Esperar a que carguen fuentes
        page.wait_for_timeout(2000)
        page.screenshot(path=output_path, full_page=True)
        browser.close()
        
    if os.path.exists(html_file):
        os.remove(html_file)
        
    print(f"[OK] Infografía Premium generada: {output_path}")
    return output_path

if __name__ == "__main__":
    # Test
    test_data = {
        "title": "NUEVO PEI WEB: MODERNIZACIÓN A SUNAT",
        "subtitle": "Obligaciones mensuales actualizadas para PRICOS",
        "illustration_prompt": "A clean elegant 3D isometric illustration of a digital folder syncing to the cloud, tax tech aesthetic, white background",
        "blocks": [
            {"title": "Adecuación", "content": "Obligatorio a partir de Agosto 2026", "icon": "📅"},
            {"title": "Impacto", "content": "Flujos de caja y conciliación web.", "icon": "💻"}
        ]
    }
    generate_infographic(test_data, "guía", "test_premium.png")
