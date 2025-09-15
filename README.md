
### Chatbot Gemini API Web
Este proyecto es una aplicación web en Python 3 que levanta un servidor con Flask para interactuar con el modelo Gemini de Google AI.
La interfaz permite mantener un chat sencillo desde el navegador, con soporte para respuestas en Markdown (listas, encabezados, código, tablas, etc.).

### 🚀 Características
- Servidor web con Flask en el puerto 8080 (por defecto).
- Chat en tiempo real con interfaz limpia en HTML/CSS/JS.
- Respuestas formateadas en Markdown (renderizadas en el cliente).
- Historial de conversación básico (guardado en memoria del navegador).
- Completamente configurable con parámetros (--api-token, --model, --port, etc.).
- Compatible con el SDK oficial google-genai.

### 📦 Requisitos
- Python 3.9+
- Dependencias:
 - flask
 - google-genai

### Instalacion
```
python3 -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install flask google-genai
```
### How to run
Ejecuta el servidor con:

```
$python3 app.py --api-token API_TOKEN
```
