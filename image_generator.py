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

def generate_banner(banner_data, illustration_prompt, output_path="banner_noticia.png"):
    print("Preparando renderizado HTML + CSS + Playwright para el Banner...")
    
    # Obtener Ilustración 3D (DALL-E) si hay API
    ill_prompt = illustration_prompt if illustration_prompt else "A conceptual 3D isometric illustration about legal documents and taxes, clean corporate minimalist style"
    dalle_img_path = generate_dalle_image(ill_prompt)
    
    b64_image = ""
    if dalle_img_path and os.path.exists(dalle_img_path):
        b64_image = f"data:image/png;base64,{get_base64_image(dalle_img_path)}"
        os.remove(dalle_img_path)
    
    titulo = banner_data.get("titulo_banner", "ACTUALIZACIÓN NORMATIVA")
    texto1 = banner_data.get("texto_destacado_1", "")
    texto2 = banner_data.get("texto_destacado_2", "")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                width: 1200px;
                height: 500px;
                color: #ffffff;
                display: flex;
                overflow: hidden;
            }}
            .text-container {{
                flex: 1.2;
                padding: 60px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                position: relative;
                z-index: 2;
            }}
            .image-container {{
                flex: 0.8;
                background-image: url('{b64_image}');
                background-size: cover;
                background-position: center;
                position: relative;
                box-shadow: -20px 0 50px rgba(0,0,0,0.5);
                border-left: 5px solid #00e5ff;
            }}
            
            /* Decoración en el texto */
            .badge {{
                display: inline-block;
                background: #00e5ff;
                color: #0f172a;
                font-size: 16px;
                font-weight: 700;
                padding: 8px 16px;
                border-radius: 4px;
                margin-bottom: 25px;
                text-transform: uppercase;
                letter-spacing: 2px;
                width: max-content;
            }}
            
            .title {{
                font-family: 'Montserrat', sans-serif;
                font-size: 55px;
                font-weight: 900;
                line-height: 1.1;
                margin-bottom: 35px;
                text-transform: uppercase;
                color: #ffffff;
                text-shadow: 2px 4px 10px rgba(0,0,0,0.3);
            }}
            
            .bullet-point {{
                display: flex;
                align-items: flex-start;
                margin-bottom: 20px;
                animation: slideIn 1s ease-out;
            }}
            
            .bullet-point i {{
                color: #00e5ff;
                font-size: 24px;
                margin-right: 15px;
                font-style: normal;
                line-height: 1.2;
            }}
            
            .bullet-text {{
                font-size: 24px;
                font-weight: 400;
                color: #cbd5e1;
                line-height: 1.4;
            }}
        </style>
    </head>
    <body>
        <div class="text-container">
            <div class="badge">ALERTA LEGAL</div>
            <div class="title">{titulo}</div>
            
            <div class="bullet-point">
                <i>✦</i>
                <div class="bullet-text">{texto1}</div>
            </div>
            
            <div class="bullet-point">
                <i>✦</i>
                <div class="bullet-text">{texto2}</div>
            </div>
        </div>
        
        <div class="image-container"></div>
    </body>
    </html>
    """
    
    html_file = "temp_render.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("Renderizando Banner HTML a PNG resolucion Wide...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1200, 'height': 500}, device_scale_factor=2)
        page.goto(f"file://{os.path.abspath(html_file)}", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=output_path)
        browser.close()
        
    if os.path.exists(html_file):
        os.remove(html_file)
        
    print(f"[OK] Banner Premium generado: {output_path}")
    return output_path

if __name__ == "__main__":
    test_data = {
        "titulo_banner": "INAFECTACIÓN DE IGV CULTURAL",
        "texto_destacado_1": "Beneficio no automático para asociaciones sin fines de lucro.",
        "texto_destacado_2": "Requiere resolución habilitante del Ministerio de Cultura."
    }
    generate_banner(test_data, "A 3D glowing museum column and tax document with neon cyan and blue lighting, dark background, corporate premium isometric style", "test_banner.png")

