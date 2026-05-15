import base64
import json
import logging
import io
from PIL import Image
from core.google import openai_client, VISION_MODEL
from prompts.prompts import build_multimodal_audit_prompt
from core.langfuse_client import langfuse

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = ["png", "jpeg", "gif", "webp"]


class MultimodalAuditService:
    def __init__(self):
        self.client = openai_client
        self.model = VISION_MODEL

    def _detect_mime_type(self, image_bytes: bytes) -> str:
        # Detect the real MIME type of the image from its byte signature.
        if image_bytes.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
            return "image/gif"
        elif image_bytes.startswith(b"RIFF") and len(image_bytes) > 12 and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        return None

    def _convert_to_png(self, image_bytes: bytes) -> bytes:
        # Convert any image format to PNG for OpenAI vision compatibility.
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            output = io.BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error converting image to PNG: {e}")
            return image_bytes

    def audit_image(self, image_bytes: bytes, context: str) -> dict:
        # Send image + brand rules to OpenAI vision model for compliance audit.
        try:
            prompt = build_multimodal_audit_prompt(context)
            mime_type = self._detect_mime_type(image_bytes)
            if mime_type is None:
                logger.warning("Unrecognized format, trying to convert to PNG")
                image_bytes = self._convert_to_png(image_bytes)
                mime_type = "image/png"

            format_name = mime_type.split("/")[1]
            if format_name not in SUPPORTED_FORMATS:
                return {
                    "approved": False,
                    "score": 0.0,
                    "issues": [f"Unsupported image format: {format_name}"],
                    "strengths": [],
                    "explanation": f"System only accepts the following formats: {', '.join(SUPPORTED_FORMATS)}",
                    "recommendations": [f"Convert your image to one of these formats: {', '.join(SUPPORTED_FORMATS)}"],
                    "feedback": f"Unsupported format. Use: {', '.join(SUPPORTED_FORMATS)}",
                }
            
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            generation = langfuse.generation(
                name="openai_vision_audit",
                model=self.model,
                input={"prompt": prompt, "image_size": len(image_bytes), "format": format_name},
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.1,
                max_tokens=1024,
            )

            raw_text = response.choices[0].message.content.strip()
            clean_text = (
                raw_text.replace("```json", "")
                .replace("```", "")
                .strip()
            )

            try:
                parsed = json.loads(clean_text)
            except Exception:
                parsed = {
                    "approved": False,
                    "score": 0.0,
                    "issues": ["Invalid model response"],
                    "strengths": [],
                    "explanation": raw_text,
                    "recommendations": [
                        "Verify model output format"
                    ],
                }

            generation.end(output=parsed)
            logger.info(f"Audit completed: approved={parsed.get('approved')}, score={parsed.get('score')}")
            
            feedback_parts = []
            if parsed.get("explanation"):
                feedback_parts.append(parsed["explanation"])
            if parsed.get("issues"):
                feedback_parts.append("Problemas: " + "; ".join(parsed["issues"]))
            if parsed.get("recommendations"):
                feedback_parts.append("Recomendaciones: " + "; ".join(parsed["recommendations"]))
            
            parsed["feedback"] = " | ".join(feedback_parts) if feedback_parts else "Sin detalles disponibles"
            
            return parsed

        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return {
                "approved": False,
                "score": 0.0,
                "issues": [str(e)],
                "strengths": [],
                "explanation": "La auditoría falló por un error del sistema",
                "recommendations": ["Revisar los logs e intentar nuevamente"],
                "feedback": f"Error en la auditoría: {str(e)}",
            }
