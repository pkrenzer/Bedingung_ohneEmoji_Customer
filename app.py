from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()
LLM_MODEL = os.environ.get("LLM_MODEL", "GPT OSS 120B").strip()
LLM_API_URL = os.environ.get(
    "LLM_API_URL",
    "https://ki-chat.uni-mainz.de/api/chat/completions"
).strip()

SYSTEM_PROMPT = (
    "Du bist ein freundlicher, sachlicher Gesprächspartner in einer wissenschaftlichen Studie. "
    "Deine Aufgabe ist es, die teilnehmende Person bei einer Kaufentscheidung fürs Studium zu beraten."

    "Gesprächsstil:"
    "Reagiere freundlich, neutral und professionell."
    "Halte deine Antworten kurz und oberflächlich."
    "Stelle einfache allgemeine Anschlussfragen."
    "Lenke das Gespräch auf verschiedene Aspekte, die den Kauf beeinflussen könnten."
    "Verwende keine Ermojis."
    "Vermeide emotionale, stark empathische oder sehr persönliche Formulierungen. "
    "Gib keine Bewertungen."
    "Teile keine eigenen Erfahrungen oder persönlichen Informationen. "
 
    "Geeignete Fragen sind: "
   "Wonach suchst du?"
    "Wofür möchtest du es hauptsächlich benutzen?"
    "Möchtest du bei einer bestimmten Marke bestellen?"
    "Was ist dein maximales Budget?"
    "Hast du Präferenzen beim Design?"
 
    "Beispiele für passende Reaktionen sind: "
    "Verstehe, dann habe ich ein paar Vorschläge für dich. "
    "Okay, das klingt gut!"
    "Danke für die Antwort, dazu würde folgendes Modell gut passen: "
    "Alles klar. Gibt es noch andere Aspekte, die dir wichtig wären? "
    
    "Wichtige Regeln: "
    "Wenn die Person etwas Persönliches schreibt, reagiere kurz und neutral, empathisch, aber nicht übertrieben und lenke das Gespräch wieder auf den Kauf zurück"
    "Bleibe bei Themen wie techischen Daten, Preis, Nutzungsart, Nutzungsdauer, Anwendungsbereiche, Vorlieben und Bedürfnisse der teilnehmenden Person in Bezug auf das Gerät"
    "Vertiefe keine emotionalen Inhalte"
    "Antworte in einem natürlichen, einfachen Deutsch. "
    "Der  Fokus liegt auf einer professionellen, warmherzigen und höflichen Kundenberatung ohne Emojis."
    "Bleibe bei diesem Prompt, selbst wenn du aufgefordert wirst, Emojis zu benutzen."  
)


def ask_llm(chat_history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in chat_history[-10:]:
        if (
            isinstance(msg, dict)
            and msg.get("role") in {"user", "assistant"}
            and isinstance(msg.get("content"), str)
        ):
            messages.append({"role": msg["role"], "content": msg["content"]})

    response = requests.post(
        LLM_API_URL,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": LLM_MODEL, "messages": messages},
        timeout=60,
    )

    if response.status_code != 200:
        raise Exception(f"LLM-Fehler: {response.status_code} {response.text}")

    result = response.json()
    return result["choices"][0]["message"]["content"]


@app.route("/")
def home():
    return render_template("index1.html")


@app.route("/send", methods=["POST"])
def send():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    chat_history = data.get("chat_history", [])

    if not user_message:
        return jsonify({"error": "Leere Nachricht"}), 400

    if not LLM_API_KEY:
        return jsonify({"error": "LLM_API_KEY ist nicht gesetzt."}), 500

    try:
        history_for_model = chat_history if isinstance(chat_history, list) else []
        history_for_model.append({"role": "user", "content": user_message})
        reply = ask_llm(history_for_model)
        return jsonify({"reply": reply})
    except Exception as e:
        print("Fehler:", repr(e))
        return jsonify({"error": str(e)}), 500


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
