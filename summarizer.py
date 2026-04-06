import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

def analyze_document(document_text, source_type):
    """
    Analiza un documento tributario individual, calcula su score 0-100, genera 
    el post para LinkedIn y crea la estructura JSON para la infografía.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: No se encontró la variable ANTHROPIC_API_KEY en el archivo .env")
        return None
        
    client = anthropic.Anthropic(api_key=api_key)
    
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
- Código Tributario, fiscalización, cobranza, sanciones y procedimientos vinculados a SUNAT.
- Comprobantes de pago electrónicos (SIRE).
- Informes SUNAT vinculantes o que aclaren casuísticas clave.
- Jurisprudencia (Resoluciones del Tribunal Fiscal, Casaciones de la Corte Suprema).

# SISTEMA DE SCORING (0 a 100)
Evalúa sobre 100 puntos basándote en:
- Relevancia tributaria (0-25): ¿Es el core de tributos internos SUNAT?
- Impacto práctico (0-25): ¿Afecta la liquidez, procesos diarios o genera contingencias a empresas?
- Novedad (0-15): ¿Es un cambio nuevo o ratifica algo ya conocido de manera importante?
- Alcance (0-15): ¿Afecta a muchos contribuyentes o solo a un nicho mínimo?
- Urgencia (0-10): ¿Entra en vigor mañana o tiene un vencimiento cercano?
- Utilidad comunicacional (0-10): ¿Es fácil y útil de explicar en LinkedIn?

SI EL PUNTAJE ES MENOR A 65: Setear "publish_decision": false.

# DIRECTRICES DE REDACCIÓN (Si publish_decision es true)
- TONO DEL POST: Humano, analítico, directo y profesional. NADA de frases típicas de IA ("En conclusión", "En el panorama actual", "¡Hola red!").
- ESTRUCTURA VISUAL: Párrafos cortos (2 a 3 líneas máximo). NO uses listas con viñetas ni enumeraciones robóticas.
- APERTURA: Empieza indicando directamente la acción y el nombre completo de la norma (ej. "Publican la Ley N° 31xxx que establece...", "Se aprueba la Resolución N° 123...").
- CUERPO: Explica el impacto práctico o los antecedentes de forma fluida.
- VIGENCIA: Antes de finalizar, añade expresamente un párrafo indicando la fecha o momento en que entra en vigencia (ej. "Esta norma entra en vigencia el...").
- CIERRE: Termina OBLIGATORIAMENTE con exactamente este texto final (usando el placeholder '[URL_DOC]'):

📄 Descarga el documento oficial aquí: [URL_DOC]

#Tributario #SUNAT #Contadores

# DIRECTRICES DE INFOGRAFÍA E ILUSTRACIÓN 3D
- Types permitidos para "infographic_type": 'alerta', 'guía', 'comparativo', 'cronograma', 'criterio jurisprudencial'.
- Layout limit de 6 bloques, preferir conceptos cortos (2-5 palabras).
- Además, redacta un "illustration_prompt" en inglés (máx 50 palabras) extremadamente detallado para que un modelo generador de imágenes (DALL-E) cree una ilustración 3D corporativa que acompañará tu análisis. Ejemplo: "A high quality 3D isometric illustration of a modern laptop with glowing neon outlines, tax documents flying out, floating shield icon, corporate blue and cyan color palette, clean light background, premium B2B style"

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
  "infographic_type": <string>,
  "infographic_layout_json": {{
      "title": <string>,
      "subtitle": <string>,
      "blocks": [
           {{"title": <str>, "content": <str>, "icon": <str_basico_tipo_emoji>}}
      ]
  }},
  "illustration_prompt": <string>,
  "effective_date": <string, o null si no aplica>,
  "confidence_score": <number 0-10>
}}

TEXTO A ANALIZAR:
{document_text}
"""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            temperature=0.2,
            system="Eres un estricto validador y analista JSON de datos tributarios de Perú.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = response.content[0].text.strip()
        
        # Parse JSON
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        data = json.loads(content)
        return data
        
    except Exception as e:
        print(f"Error en analyzer (Claude): {e}")
        return None

if __name__ == "__main__":
    t = "Resolución Ministerial N° 123-2026-MTC. Designan a director en el área de telecomunicaciones."
    res = analyze_document(t, "El Peruano")
    print(json.dumps(res, indent=2, ensure_ascii=False))
