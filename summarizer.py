import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

def summarize_norms(norms_text):
    """
    Usa Claude para filtrar normas tributarias de la SUNAT y generar un JSON
    con el post y el texto de la infografía.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: No se encontró la variable ANTHROPIC_API_KEY en el archivo .env")
        return None
        
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""
Eres un experto tributario (contador o abogado) en Perú, dirigiéndote a colegas y dueños de negocios en LinkedIn.

REGLAS DE FILTRADO:
1. Filtra las normas y busca ÚNICAMENTE las relacionadas con tributos internos administrados por SUNAT (Impuesto a la Renta, IGV, ISC, ITAN, etc.).
2. Incluye Leyes, Decretos Legislativos, Decretos Supremos, Resoluciones de Superintendencia y Casaciones relevantes.
3. EXCLUYE tributación municipal, regional y temas de Aduanas (salvo que afecten a procesos de tributos internos como Percepciones, RUC o Devoluciones).
4. IGNORA cualquier norma administrativa, militar, política, nombramientos, etc.
5. Si HOY NO HAY NINGUNA NORMA QUE CUMPLA ESTOS REQUISITOS, tu respuesta debe ser ÚNICA y EXACTAMENTE esta palabra (sin nada más):
NO_RELEVANT_NORMS

REGLAS DE REDACCIÓN (Si hay normas relevantes):
- Tono serio, analítico y directo. Lenguaje humano, en prosa y explicativo.
- NO uses listas estructuradas, ni viñetas, que parezcan generadas por una IA.
- Varía la frase de apertura en cada post, manteniendo la sobriedad.
- NO uses logos ni menciones a marcas.
- Emojis de forma mínima y estratégica (máximo 2 o 3 en todo el post).
- Estructura obligatoria en bloques fluidos de texto (párrafos):
  1. Resumen: Una explicación en prosa de 2 a 3 líneas sobre el contexto de la norma.
  2. Análisis: Puntos clave redactados de forma fluida (sin viñetas robóticas).
  3. Impacto: Un párrafo final que responda directamente: '¿Cómo afecta esto a los profesionales tributarios y contribuyentes?'
  4. Cierra con un último párrafo que diga EXACTAMENTE: "📄 Descarga el documento oficial aquí: [Inserta aquí la URL de la norma que elegiste]"
  5. Abajo de la URL, incluye estos Hashtags: #TributoContable #SUNAT #ContadoresPeru #NormasLegales

INFOGRAFÍA:
Bajo ese mismo análisis, redacta también un texto ultrarresumido (4 o 5 líneas muy cortas) que servirá de concepto para generar una imagen o ilustración sobre el tema.

FORMATO DE SALIDA:
Devuelve un JSON estrictamente válido, con dos propiedades: "linkedin_post" e "image_text". Sin markdown extra.

Lista JSON de normas extraídas (cada una con su texto y url):
{norms_text}
"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            temperature=0.3,
            system="Eres un experto tributario de SUNAT. Devuelve solo un JSON válido o la palabra NO_RELEVANT_NORMS si no hay normas.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = response.content[0].text.strip()
        
        if content == "NO_RELEVANT_NORMS" or "NO_RELEVANT_NORMS" in content:
            return "NO_RELEVANT_NORMS"
            
        # Parse JSON en caso que el modelo agregue los backticks
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        data = json.loads(content)
        return dict(
            post=data.get("linkedin_post", ""),
            image=data.get("image_text", "")
        )
    except Exception as e:
        print(f"Error en summarize_norms: {e}")
        return None

if __name__ == "__main__":
    t = "Resolución de Superintendencia N° 000042-2024/SUNAT: Modifican plazo de atraso de Registro de Ventas e Ingresos Electrónico."
    res = summarize_norms(t)
    print(res)
