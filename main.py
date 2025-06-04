import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import logging

# ✅ Logging setup
logging.basicConfig(level=logging.INFO)

# ✅ Dependency imports
print("✅ Flask imported")
print("✅ stt.py import starting")
from stt import transcribe_audio
print("✅ stt.py imported")

print("✅ llm.py import starting")
from llm import query_llm
print("✅ llm.py imported")

print("✅ tts.py import starting")
from tts import generate_speech
print("✅ tts.py imported")

# ✅ Config
UPLOAD_FOLDER = "uploads"
TTS_FOLDER = "tts_output"
ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TTS_FOLDER"] = TTS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ✅ Routes

@app.route("/")
def index():
    return "🎤 Conversational Voice Agent is running!"

@app.route("/voice")
def voice_interface():
    return render_template("index.html")  # Make sure templates/index.html exists

@app.route("/chat", methods=["POST"])
def chat():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        logging.info(f"📥 File saved: {filepath}")

        # 1. Transcribe
        transcription = transcribe_audio(filepath)
        logging.info(f"📝 Transcription: {transcription}")

        # 2. Get response from LLM
        response_text = query_llm(transcription)
        logging.info(f"🤖 LLM Response: {response_text}")

        # 3. Generate speech
        tts_path = generate_speech(response_text)
        if tts_path is None:
            return jsonify({"error": "TTS generation failed"}), 500


        # ✅ Return everything
        return jsonify({
            "transcription": transcription,
            "response": response_text,
            "audio_reply_url": f"/audio/{os.path.basename(tts_path)}"
        })

    return jsonify({"error": "Unsupported file format"}), 400

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(app.config["TTS_FOLDER"], filename)

# ✅ Entry point
if __name__ == "__main__":
    print("🚀 Launching Flask app...")
    app.run(debug=True, host="0.0.0.0", port=5000)
