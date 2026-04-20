import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def analyze_document(document_text, source_type):
    """
    Analiza un documento tributario individual, calcula su score 0-100, genera 
    el post para LinkedIn y crea la estructura JSON para la infografía.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: No se encontró la variable OPENAI_API_KEY en el archivo .env")
        return None
        
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
Eres un analista tributario senior de la SUNAT y creador de contenido B2B en LinkedIn.
Se te ha proporcionado el texto de un documento legal/tributario proveniente de '{source_type}'.
¡ATENCIÓN! Si el texto proporcionado contiene MÚLTIPLES resoluciones (como suele suceder en los cuadernillos de Casaciones o Informes masivos):
1. Debes analizar rápidamente todas las resoluciones incluidas.
2. Identifica y escoge ÚNICAMENTE la resolución que sea MÁS relevante según los criterios descritos abajo.
3. Evalúa, puntúa y redacta TODO el análisis basándote DE FORMA EXCLUSIVA en esa única resolución seleccionada, ignorando por completo el resto del contenido.

# OBJETIVO PRINCIPAL
Analizar el documento para determinar si es relevante publicarlo para profesionales contables, abogados y empresas en Perú. Si lo es, debes generar un post muy humano y redactar un layout estructurado para una infografía.

# CRITERIOS DE INCLUSIÓN Y EXCLUSIÓN
EXCLUIR INMEDIATAMENTE (Puntaje automático < 50):
- Tributación municipal, regional, predial, arbitrios, alcabala, tasas locales.
- Aduanas (A menos que esté intrínsecamente vinculado al IGV).
- Designaciones de personal, actos administrativos internos, renuncias, nombramientos.
- Resoluciones no vinculantes o de mero trámite.

INCLUIR Y PRIORIZAR (Aumenta el puntaje):
- IGV, Impuesto a la Renta, ITAN, ISC.
- Beneficios tributarios, inafectaciones y exoneraciones (¡incluso si están dirigidos a una entidad o sector específico, son altísimamente relevantes como casos de estudio!).
- Código Tributario, fiscalización, cobranza, sanciones y procedimientos vinculados a SUNAT.
- Comprobantes de pago electrónicos (SIRE).
- Informes SUNAT vinculantes o que aclaren casuísticas clave.
- Jurisprudencia (Resoluciones del Tribunal Fiscal, Casaciones de la Corte Suprema).

# SISTEMA DE SCORING (0 a 100)
Evalúa sobre 100 puntos basándote en:
- Relevancia tributaria (0-25): ¿Es el core de tributos internos SUNAT?
- Impacto práctico (0-25): ¿Afecta la liquidez, procesos diarios o genera contingencias a empresas?
- Novedad (0-15): ¿Es un cambio nuevo o ratifica algo ya conocido de manera importante?
- Alcance (0-15): ¿Afecta a muchos contribuyentes o es un precedente/caso de estudio replicable? (Las inafectaciones otorgan máximo puntaje aquí por su valor de análisis).
- Urgencia (0-10): ¿Entra en vigor mañana o tiene un vencimiento cercano?
- Utilidad comunicacional (0-10): ¿Es fácil y útil de explicar en LinkedIn?

SI EL PUNTAJE ES MENOR A 65: Setear "publish_decision": false.

# DIRECTRICES DE REDACCIÓN (Si publish_decision es true)
# DIRECTRICES DE REDACCIÓN (Si publish_decision es true)
# DIRECTRICES DE REDACCIÓN (Si publish_decision es true)
- TONO DEL POST: Fluido, conversacional pero altamente experto. Redacta como un socio de impuestos analizando calmadamente una norma. NO satures la información como si fuera un checklist rígido ni uses viñetas excesivas. Usa párrafos bien desarrollados (storytelling técnico) para explicar el impacto.
- ESTRUCTURA VISUAL: Entrelaza suavemente la información clave de manera natural en la prosa. DEBES extraer y mencionar (si los hay):
  * **Plazos exactos y fechas de vencimiento**.
  * **Nombres y números de formularios / sistemas**.
  * **Vigencia** (SOLO si está explícita).
  * **Contingencias**: Explica el impacto de no cumplir de forma reflexiva.
- APERTURA: Inicia con una reflexión o un contexto sobre el porqué de la norma antes de lanzar los datos técnicos.
- CIERRE: Termina OBLIGATORIAMENTE con exactamente este texto final (usando el placeholder '[URL_DOC]'):

📄 Descarga el documento oficial aquí: [URL_DOC]

#Tributario #SUNAT #Contadores

# DIRECTRICES PARA LA IMAGEN (SITUACIÓN)
- La publicación irá acompañada DIRECTAMENTE de una fotografía estéticamente seria, sobria y premium, ideal para el feed de un gerente, CFO o Socio de Impuestos.
- En tu JSON de respuesta debes incluir:
  1. `illustration_prompt`: Redacta en inglés un prompt detallado para DALL-E 3.
     - ESTILO TÉCNICO VITAL: "Premium corporate photography, macro shot, photorealistic, raw photography, taken with 85mm lens, cinematic lighting. ABSOLUTELY NO 3D, NO CGI, NO ILLUSTRATIONS, NO CARTOONS, NO HUMANS."
     - CONCEPTO: Enfócate en objetos corporativos elegantes que simbolicen la norma. (Ej. un escritorio de caoba con un documento formal, una pluma estilográfica, un mazo de juez, un maletín de cuero o una calculadora corporativa).
     - TEXTO: Si quieres poner texto en el documento/objeto, limítate a 1 o 2 PALABRAS CLAVE COMO MÁXIMO en español, indicadas entre comillas exactas. (Ej. a document folder with the word "SUNAT").
     - Ej: "Premium corporate photography, macro shot of a sleek silver fountain pen resting on a crisp tax document folder labeled 'RENTA AGRARIA' on a dark mahogany desk. Soft morning sunlight, sharp focus, highly professional, no humans, strictly photorealistic, no CGI."

# FORMATO DE SALIDA ESTRICTO JSON
Sin Markdown adicional, debes devolver un de JSON con las siguientes llaves exactas:
{{
  "publish_decision": <boolean>,
  "final_score": <number 0-100>,
  "discard_reason": <string, si es false, explicar brevemente porqué>,
  "source": <string, ej 'El Peruano', 'SUNAT', 'Tribunal Fiscal'>,
  "document_type": <string, ej 'Casacion', 'Informe', 'Ley', 'RS'>,
  "main_topic": <string>,
  "summary_internal": <string>,
  "linkedin_post": <string>,
  "illustration_prompt": <string>,
  "effective_date": <string, o null si no se especifica explícitamente>,
  "confidence_score": <number 0-10>
}}

TEXTO A ANALIZAR:
{document_text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.2,
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "Eres un estricto validador y analista JSON de datos tributarios de Perú. Tu única salida debe ser un objeto JSON puro."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        return data
        
    except Exception as e:
        print(f"Error en analyzer (OpenAI): {e}")
        return None

if __name__ == "__main__":
    t = "Resolución Ministerial N° 123-2026-MTC. Designan a director en el área de telecomunicaciones."
    res = analyze_document(t, "El Peruano")
    print(json.dumps(res, indent=2, ensure_ascii=False))
