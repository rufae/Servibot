Antes de continuar, respuesta a tu pregunta sobre costes (resumen):

APIs que pueden costar:

OpenAI (GPT / embeddings / Whisper API): pago por uso. Evitar si quieres cero coste.
ElevenLabs (TTS): servicio con planes; puede tener cuota gratuita limitada.
HuggingFace Inference API (si la usas): pago por uso salvo modelos con cuota gratuita limitada.
Google APIs (Calendar, Gmail): necesitan proyecto en Google Cloud; la API tiene cuotas gratuitas para muchas operaciones, pero puede requerir facturación para uso extendido.
Hosted vector DBs / Llama-hosting / managed LLMs: normalmente pagos.
Dependencias y librerías:

sentence-transformers, chromadb, pypdf, pymupdf, pillow, pytesseract, etc. — son gratuitas (OSS).
Tesseract OCR binary: gratuito, pero instalación local (no coste monetario).
Hosting (Vercel, Render): tienen planes gratuitos con límites; producción puede costar.
Compute / storage:

Si ejecutas modelos locales grandes (Llama, etc.) necesitarás GPU/CPU time (coste si usas cloud).
Embeddings via local sentence-transformers run on CPU — slower but free.
Chroma local uses disk space only.
Recomendación para MVP barato:

Usar sentence-transformers local (embeddings gratuitos), chromadb local, and local Whisper (or avoid Whisper and use text input). Use mocks for Google/ElevenLabs. This keeps monetary cost near zero.