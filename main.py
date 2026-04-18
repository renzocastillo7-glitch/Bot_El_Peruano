import sys
import os
import hashlib
import argparse
from datetime import datetime

from scraper import scrape_el_peruano_norms, scrape_informes_sunat, scrape_cuadernillos
from summarizer import analyze_document
from image_generator import generate_dalle_image
from linkedin_publisher import post_to_linkedin
from database import db

def get_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def process_documents(docs, block_name):
    """
    Procesa lista de documentos, guarda en BD, analiza con LLM
    y devuelve los candidatos aprobados para publicación.
    """
    candidates = []
    
    for doc in docs:
        url = doc.get("url", "")
        text = doc.get("text", "")
        source = doc.get("source", "Unknown")
        doc_type = doc.get("type", "desconocido")
        doc_hash = get_hash(text)
        
        # 1. Deduplicación
        if db.is_duplicate(url=url if url else None, hash_content=doc_hash):
            db.log_event("INFO", "Documento duplicado saltado", f"Fuente: {source}, Hash: {doc_hash}")
            continue
            
        # 2. Guardar Raw Document
        doc_id = db.insert_document({
            "source": source,
            "document_type": doc_type,
            "url": url,
            "hash_content": doc_hash,
            "extracted_text": text
        })
        
        if not doc_id:
            db.log_event("ERROR", "No se pudo insertar documento en BD", f"Hash: {doc_hash}")
            continue
            
        print(f"\n[Analizando] {source}...")
        
        # 3. LLM Analysis
        analysis_result = analyze_document(text, source)
        if not analysis_result:
            db.log_event("WARNING", "Error en análisis de Claude", f"DocID: {doc_id}")
            continue
            
        # 4. Guardar Analysis
        db.insert_analysis({
            "document_id": doc_id,
            "publish_decision": analysis_result.get("publish_decision", False),
            "final_score": analysis_result.get("final_score", 0),
            "discard_reason": analysis_result.get("discard_reason", ""),
            "main_topic": analysis_result.get("main_topic", ""),
            "summary_internal": analysis_result.get("summary_internal", ""),
            "effective_date": analysis_result.get("effective_date", "")
        })
        
        decision = analysis_result.get("publish_decision", False)
        score = analysis_result.get("final_score", 0)
        
        if decision and score >= 65:
            candidates.append({
                "doc_id": doc_id,
                "score": score,
                "analysis": analysis_result,
                "source": source,
                "url": url
            })
            
    return candidates

def publish_top_candidate(candidates, block_name):
    if not candidates:
        print(f"[{block_name}] Ningún documento alcanzó el umbral para ser publicado.")
        return
        
    # Orden temporal de prioridad: Normas > Casaciones > Informes (si hay empate, ver score)
    # Ordenamos por score descendente
    candidates.sort(key=lambda x: x["score"], reverse=True)
    winner = candidates[0]
    score = winner["score"]
    an_res = winner["analysis"]
    doc_url = winner.get("url", "")
    
    print(f"\n[!] GANADOR para el bloque {block_name}: Score {score} - Tema: {an_res.get('main_topic')}")
    
    # Generar Imagen Situacional DALL-E
    ill_prompt = an_res.get("illustration_prompt", "")
    img_path = ""
    if ill_prompt:
        img_path = generate_dalle_image(ill_prompt, f"dalle_{block_name}.png")
        if not img_path:
            img_path = ""
            
    text_post = an_res.get("linkedin_post", "")
    
    # Reemplazar placeholder [URL_DOC] si está
    if doc_url:
        text_post = text_post.replace("[URL_DOC]", doc_url)
    
    # DB - Insert Post
    post_id = db.insert_post({
        "text_content": text_post,
        "image_path": img_path
    })
    
    # Publicar
    print("\nPublicando en LinkedIn...")
    try:
        success = post_to_linkedin(text_content=text_post, image_path=img_path)
    except Exception as e:
        success = False
        print("Error al publicar:", e)
        
    db.insert_publication({
        "post_id": post_id,
        "platform": "LinkedIn",
        "status": "SUCCESS" if success else "FAILED",
        "published_at": datetime.now().isoformat() if success else None
    })
    
    if success:
        print("[OK] Publicado exitosamente.")
        # Limpiar img
        if img_path and os.path.exists(img_path):
            os.remove(img_path)
    else:
         print("[X] Falló la publicación.")

def main():
    parser = argparse.ArgumentParser(description="Bot Tributario Automático")
    parser.add_argument("--time", choices=["morning", "afternoon"], default="morning", 
                        help="Bloque de ejecución (morning o afternoon)")
    
    args = parser.parse_args()
    block = args.time
    
    print("="*50)
    print(f"   BOT TRIBUTARIO - BLOQUE: {block.upper()}")
    print("="*50)
    
    db.log_event("INFO", f"Iniciando ejecución bloque {block}", "")
    
    all_docs = []
    
    # Lógica de scraping según el bloque
    if block == "morning":
        docs_normas = scrape_el_peruano_norms()
        docs_cas = scrape_cuadernillos("Casaciones")
        docs_prec = scrape_cuadernillos("Jurisprudencia")
        all_docs.extend(docs_normas)
        all_docs.extend(docs_cas)
        all_docs.extend(docs_prec)
    
    elif block == "afternoon":
        docs_inf = scrape_informes_sunat()
        docs_cas = scrape_cuadernillos("Casaciones") # Se revisa de nuevo si hay algo fresco
        docs_prec = scrape_cuadernillos("Jurisprudencia")
        all_docs.extend(docs_inf)
        all_docs.extend(docs_cas)
        all_docs.extend(docs_prec)
        
    if not all_docs:
        print("No se extrajeron documentos nuevos.")
        sys.exit(0)
        
    # Procesamiento y Scoring
    candidates = process_documents(all_docs, block)
    
    # Publicar el top
    publish_top_candidate(candidates, block)

if __name__ == "__main__":
    main()
