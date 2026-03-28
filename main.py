import sys
import os
from scraper import scrape_el_peruano_norms
from summarizer import summarize_norms
from image_generator import generate_infographic
from linkedin_publisher import post_to_linkedin

def main():
    print("="*50)
    print("   BOT TRIBUTARIO: EL PERUANO -> CLAUDE -> LINKEDIN")
    print("="*50)
    
    # 1. Scrape
    print("\n[Fase 1] Extrayendo normas legales...")
    norms_text = scrape_el_peruano_norms()
    if not norms_text or norms_text.strip() in ["", "[]"]:
        print("[!] No se encontraron normas publicadas hoy en El Peruano (o el array esta vacio).")
        print("El bot se detendra felizmente y no publicara nada hoy.")
        sys.exit(0)
        
    # 2. Resumir con IA
    print("\n[Fase 2] Generando análisis tributario con Claude...")
    result = summarize_norms(norms_text)
    
    if not result:
        print("[!] Error de IA. Revisa tu clave de Anthropic (Claude) en .env.")
        sys.exit(1)
        
    if result == "NO_RELEVANT_NORMS":
        print("[!] Claude analizo las normas y no hallo nada de tributos internos relevantes (SUNAT).")
        print("El bot se detendra felizmente y no publicara nada hoy.")
        sys.exit(0)
        
    post_text = result.get("post", "")
    image_text = result.get("image", "")
    
    print("\n--- POST GENERADO ---")
    print(post_text[:100] + "... (oculto por brevedad)")
    print("--- TEXTO INFOGRAFIA ---")
    print(image_text)
    
    # 3. Generar Imagen
    print("\n[Fase 3] Generando infografía...")
    img_path = generate_infographic(image_text, "infografia.png")
        
    # 4. Publicar en LinkedIn
    print("\n[Fase 4] Publicando en LinkedIn...")
    success = post_to_linkedin(text_content=post_text, image_path=img_path)
    
    if success:
        print("\n[OK] === PROCESO FINALIZADO CON EXITO ===")
        # Opcional: limpiar la imagen
        if os.path.exists(img_path):
            os.remove(img_path)
    else:
        print("\n[!] Error publicando en LinkedIn.")
        sys.exit(1)

if __name__ == "__main__":
    main()
