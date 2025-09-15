#!/usr/bin/env python3
import argparse
import os
from flask import Flask, request, jsonify, Response

# --- Gemini (Google GenAI SDK) ---
# pip install google-genai
from google import genai
from google.genai import types

HTML_PAGE = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Chatbot Gemini • Demo</title>
  <style>
    body { font-family: system-ui,-apple-system,Segoe UI,Roboto,Inter,Arial; margin: 0; background: #0b1020; color: #e7f1ff; }
    header { padding: 16px 20px; background: #0f172a; border-bottom: 1px solid #1e293b; }
    main { max-width: 900px; margin: 0 auto; padding: 20px; }
    .chat { background: #0f172a; border: 1px solid #1e293b; border-radius: 16px; padding: 16px; min-height: 360px; }
    .msg { padding: 10px 12px; margin: 8px 0; border-radius: 12px; line-height: 1.45 }
    .user { background: #1f2937; align-self: flex-end; }
    .bot  { background: #111827; border: 1px solid #1f2937; }
    .row { display: flex; gap: 8px; margin-top: 12px; }
    textarea { flex: 1; height: 70px; border-radius: 12px; padding: 10px; border: 1px solid #1e293b; background: #0f172a; color: #e7f1ff; resize: vertical;}
    button { background: #2563eb; color: white; border: 0; padding: 10px 16px; border-radius: 10px; cursor: pointer; }
    button:disabled { opacity: .5; cursor: not-allowed; }
    .system { font-size: 12px; opacity:.7; margin-bottom:8px }
    .footer { opacity:.6; font-size:12px; margin-top:10px }
  </style>
</head>
<body>
  <header><strong>Chatbot Gemini • Demo</strong></header>
  <main>
    <div class="system">Modelo: <code id="modelName">gemini-2.5-flash</code></div>
    <div id="chat" class="chat"></div>
    <div class="row">
      <textarea id="input" placeholder="Escribe tu mensaje... (Shift+Enter para salto de línea)"></textarea>
      <button id="sendBtn">Enviar</button>
    </div>
    <div class="footer">Demo sin persistencia ni autenticación. No introducir secretos reales.</div>
  </main>

<script>
  const chatEl = document.getElementById('chat');
  const inputEl = document.getElementById('input');
  const sendBtn = document.getElementById('sendBtn');

  // Guardamos historial en el cliente y se envía en cada turno
  const messages = [];

  function addMsg(role, content) {
    const div = document.createElement('div');
    div.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
    div.textContent = content;
    chatEl.appendChild(div);
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    addMsg('user', text);
    messages.push({ role: 'user', content: text });
    inputEl.value = '';
    sendBtn.disabled = true;

    try {
      const r = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages })
      });
      if (!r.ok) {
        const err = await r.text();
        addMsg('bot', 'Error: ' + err);
      } else {
        const data = await r.json();
        const reply = data.reply || '(sin respuesta)';
        addMsg('bot', reply);
        messages.push({ role: 'assistant', content: reply });
      }
    } catch (e) {
      addMsg('bot', 'Error de red: ' + String(e));
    } finally {
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
</script>
</body>
</html>"""

def build_client(api_key: str) -> genai.Client:
    # Pasamos el API key explícitamente para evitar confusiones de variable de entorno.
    return genai.Client(api_key=api_key)

def make_app(client: genai.Client, model_name: str = "gemini-2.5-flash") -> Flask:
    app = Flask(__name__)
    app.config["MODEL_NAME"] = model_name
    app.config["CLIENT"] = client

    @app.get("/")
    def index():
        return Response(HTML_PAGE, mimetype="text/html")

    @app.post("/api/chat")
    def chat():
        """
        Espera JSON:
        {
          "messages": [
            {"role":"user"|"assistant", "content":"..."},
            ...
          ]
        }
        """
        data = request.get_json(silent=True) or {}
        msgs = data.get("messages", [])

        # Construimos "contents" con historial (usuario/asistente) para dar contexto.
        # El SDK acepta strings o Content/Part; aquí mapeamos manualmente.
        contents = []
        for m in msgs:
            role = (m.get("role") or "").strip().lower()
            text = (m.get("content") or "").strip()
            if not text:
                continue
            if role == "assistant":
                contents.append(types.ModelContent(parts=[types.Part.from_text(text=text)]))
            else:
                contents.append(types.UserContent(parts=[types.Part.from_text(text=text)]))

        # Si no hay prompt en la solicitud, devolvemos 400
        if not contents:
            return ("missing messages", 400)

        try:
            # Llamada síncrona simple (no streaming) para mantener el ejemplo claro.
            resp = app.config["CLIENT"].models.generate_content(
                model=app.config["MODEL_NAME"],
                contents=contents,
                # Opcional: desactivar "thinking" si se desea máxima velocidad/costo mínimo:
                # config=types.GenerateContentConfig(
                #     thinking_config=types.ThinkingConfig(thinking_budget=0)
                # )
            )
            return jsonify({"reply": resp.text})
        except Exception as e:
            # No exponemos trazas internas en producción
            return (f"Gemini API error: {e}", 500)

    return app

def main():
    parser = argparse.ArgumentParser(description="Chatbot Gemini web demo")
    parser.add_argument("--api-token", required=True, help="Gemini API key (AI Studio)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--model", default="gemini-2.5-flash", help="Nombre del modelo Gemini")
    args = parser.parse_args()

    client = build_client(args.api_token)
    app = make_app(client, model_name=args.model)
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == "__main__":
    main()
