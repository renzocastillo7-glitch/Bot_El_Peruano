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
    cards_html = ""
    for block in blocks[:6]:
        icon = block.get("icon", "🔹")
        btitle = block.get("title", "")
        bcontent = block.get("content", "")
        cards_html += f"""
        <div class="card">
            <div class="card-header">
                <span class="icon">{icon}</span>
                <span class="card-title">{btitle}</span>
            </div>
            <div class="card-body">{bcontent}</div>
        </div>
        """
        
    title = infographic_data.get("title", f"REPORTE: {infographic_type.upper()}")
    subtitle = infographic_data.get("subtitle", "")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 60px 80px;
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #f8faff 0%, #e6effa 100%);
                width: 1080px;
                min-height: 1080px;
                height: auto;
                color: #1e293b;
                display: flex;
                flex-direction: column;
                align-items: center;
                box-sizing: border-box;
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
                width: 100%;
            }}
            .title {{
                font-size: 80px;
                font-weight: 900;
                color: #0f172a;
                line-height: 1.1;
                margin-bottom: 25px;
                text-wrap: balance;
            }}
            .subtitle {{
                font-size: 42px;
                font-weight: 600;
                color: #475569;
                text-wrap: balance;
            }}
            .illustration-container {{
                width: 100%;
                display: flex;
                justify-content: center;
                margin-bottom: 60px;
            }}
            .illustration {{
                width: 800px;
                height: 600px;
                background-image: url('{b64_image}');
                background-size: cover;
                background-position: center;
                border-radius: 40px;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
                border: 8px solid white;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 40px;
                width: 100%;
                margin-bottom: 40px;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.95);
                border-radius: 25px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(15, 23, 42, 0.05);
                border-left: 12px solid {primary_color};
                display: flex;
                flex-direction: column;
            }}
            .card-header {{
                display: flex;
                align-items: center;
                margin-bottom: 20px;
            }}
            .icon {{
                font-size: 55px;
                margin-right: 20px;
            }}
            .card-title {{
                font-size: 40px;
                font-weight: 800;
                color: #0f172a;
            }}
            .card-body {{
                font-size: 32px;
                color: #334155;
                line-height: 1.5;
                font-weight: 500;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">{title}</div>
            <div class="subtitle">{subtitle}</div>
        </div>
        
        {'<div class="illustration-container"><div class="illustration"></div></div>' if b64_image else ''}
        
        <div class="grid">
            {cards_html}
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
