import os
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont

def download_font():
    font_path = "Roboto-Regular.ttf"
    font_bold_path = "Roboto-Bold.ttf"
    
    try:
        if not os.path.exists(font_path):
            print("Descargando fuente Roboto Regular...")
            r = requests.get("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf", timeout=10)
            with open(font_path, "wb") as f:
                f.write(r.content)
                
        if not os.path.exists(font_bold_path):
            print("Descargando fuente Roboto Bold...")
            r = requests.get("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf", timeout=10)
            with open(font_bold_path, "wb") as f:
                f.write(r.content)
    except Exception as e:
        print(f"Advertencia: No se pudo descargar la fuente online ({e})")
        
    return font_path, font_bold_path

def generate_infographic(text_content, output_path="infografia.png"):
    """
    Genera una imagen cuadrada corporativa premium solo con código Python (Pillow).
    """
    width, height = 1080, 1080
    bg_color = (13, 27, 42)    # Azul Navy Oscuro
    accent_color = (0, 229, 255) # Cyan brillante
    text_color = (255, 255, 255)
    
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Bordes y acentos geométricos
    draw.rectangle([(0, 0), (width, 20)], fill=accent_color)
    draw.rectangle([(0, height-20), (width, height)], fill=accent_color)
    draw.rectangle([(40, 40), (45, height-40)], fill=accent_color)
    
    try:
        font_path, font_bold_path = download_font()
        font = ImageFont.truetype(font_path, 50)
        title_font = ImageFont.truetype(font_bold_path, 75)
        footer_font = ImageFont.truetype(font_path, 32)
    except Exception as e:
        print("Usando fuente por defecto del sistema.")
        font = ImageFont.load_default()
        title_font = font
        footer_font = font
        
    # Título
    title = "ALERTA TRIBUTARIA"
    draw.text((100, 100), title, font=title_font, fill=accent_color)
    
    # Separador
    draw.line([(100, 200), (350, 200)], fill=(255, 255, 255), width=4)
    
    # Texto (Word wrap)
    lines = textwrap.wrap(text_content, width=37)
    
    y_text = 280
    for line in lines:
        draw.text((100, y_text), line, font=font, fill=text_color)
        y_text += 70
        
    # Footer
    footer = "Resumen automatizado desde el Diario Oficial El Peruano"
    draw.text((100, height - 90), footer, font=footer_font, fill=(150, 160, 170))
        
    img.save(output_path, quality=95)
    print(f"Infografía generada exitosamente en: {output_path}")
    return output_path

if __name__ == "__main__":
    t = "Se aprueba el nuevo cronograma de vencimientos para las obligaciones tributarias de SUNAT correspondientes al ejercicio fiscal 2026. Los principales contribuyentes tienen fechas adelantadas."
    generate_infographic(t)
