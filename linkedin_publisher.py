import os
import requests
from dotenv import load_dotenv

load_dotenv()

def post_to_linkedin(text_content, image_path=None):
    """
    Publica un texto (y opcionalmente una imagen) en el perfil de LinkedIn del usuario.
    """
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.getenv("LINKEDIN_PERSON_URN")
    
    if not access_token or not person_urn:
        print("Error: Faltan credenciales de LinkedIn en .env")
        return False
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    asset_urn = None
    
    # 1. Subir imagen si existe
    if image_path and os.path.exists(image_path):
        print("Registrando imagen en LinkedIn...")
        register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
        register_payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": person_urn,
                "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
            }
        }
        
        try:
            resp = requests.post(register_url, headers=headers, json=register_payload)
            resp.raise_for_status()
            upload_data = resp.json()
            upload_url = upload_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset_urn = upload_data["value"]["asset"]
            
            print(f"Subiendo archivo binario {image_path}...")
            with open(image_path, "rb") as img_file:
                img_bytes = img_file.read()
            
            headers_img = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/octet-stream"}
            upload_resp = requests.put(upload_url, headers=headers_img, data=img_bytes)
            upload_resp.raise_for_status()
            print("Imagen subida correctamente.")
            
        except requests.exceptions.HTTPError as e:
            print(f"Error subiendo imagen a LinkedIn: {e}")
            asset_urn = None # Fallback a solo texto si falla la imagen

    # 2. Crear el Post interactivo
    print("Configurando el post en LinkedIn...")
    url = "https://api.linkedin.com/v2/ugcPosts"
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text_content},
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    
    if asset_urn:
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
            {"status": "READY", "media": asset_urn}
        ]
    else:
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "NONE"

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"-> Post publicado exitosamente en LinkedIn. URN: {response.json().get('id')}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP publicando en LinkedIn: {e.response.text}")
        return False
    except Exception as e:
        print(f"Error al publicar el post: {e}")
        return False
