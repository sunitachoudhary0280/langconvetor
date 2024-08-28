from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from groq import Groq
import requests
import io
import base64

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
# Groq API key
groq_api_key = os.environ.get("GROQ_API_KEY", "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")
client = Groq(api_key=groq_api_key)

# ElevenLabs API key and voice ID
#elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY", "f10cdaecf1315d58b5da5ddc14d91529")
#elevenlabs_voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "jbU2N9qfPMHku9fZuJDQ")
ELEVENLABS_API_KEY = "f10cdaecf1315d58b5da5ddc14d91529"
ELEVENLABS_VOICE_ID = "jbU2N9qfPMHku9fZuJDQ"

LANGUAGES = {
    "Afrikaans": "af", "Albanian": "sq", "Amharic": "am", "Arabic": "ar", "Armenian": "hy",
    "Azerbaijani": "az", "Basque": "eu", "Belarusian": "be", "Bengali": "bn", "Bosnian": "bs",
    "Bulgarian": "bg", "Catalan": "ca", "Cebuano": "ceb", "Chinese (Simplified)": "zh-CN",
    "Chinese (Traditional)": "zh-TW", "Corsican": "co", "Croatian": "hr", "Czech": "cs",
    "Danish": "da", "Dutch": "nl", "English": "en", "Esperanto": "eo", "Estonian": "et",
    "Finnish": "fi", "French": "fr", "Frisian": "fy", "Galician": "gl", "Georgian": "ka",
    "German": "de", "Greek": "el", "Gujarati": "gu", "Haitian Creole": "ht", "Hausa": "ha",
    "Hawaiian": "haw", "Hebrew": "he", "Hindi": "hi", "Hmong": "hmn", "Hungarian": "hu",
    "Icelandic": "is", "Igbo": "ig", "Indonesian": "id", "Irish": "ga", "Italian": "it",
    "Japanese": "ja", "Javanese": "jv", "Kannada": "kn", "Kazakh": "kk", "Khmer": "km",
    "Kinyarwanda": "rw", "Korean": "ko", "Kurdish": "ku", "Kyrgyz": "ky", "Lao": "lo",
    "Latin": "la", "Latvian": "lv", "Lithuanian": "lt", "Luxembourgish": "lb", "Macedonian": "mk",
    "Malagasy": "mg", "Malay": "ms", "Malayalam": "ml", "Maltese": "mt", "Maori": "mi",
    "Marathi": "mr", "Mongolian": "mn", "Myanmar (Burmese)": "my", "Nepali": "ne", "Norwegian": "no",
    "Nyanja (Chichewa)": "ny", "Odia (Oriya)": "or", "Pashto": "ps", "Persian": "fa", "Polish": "pl",
    "Portuguese": "pt", "Punjabi": "pa", "Romanian": "ro", "Russian": "ru", "Samoan": "sm",
    "Scots Gaelic": "gd", "Serbian": "sr", "Sesotho": "st", "Shona": "sn", "Sindhi": "sd",
    "Sinhala (Sinhalese)": "si", "Slovak": "sk", "Slovenian": "sl", "Somali": "so", "Spanish": "es",
    "Sundanese": "su", "Swahili": "sw", "Swedish": "sv", "Tagalog (Filipino)": "tl", "Tajik": "tg",
    "Tamil": "ta", "Tatar": "tt", "Telugu": "te", "Thai": "th", "Turkish": "tr", "Turkmen": "tk",
    "Ukrainian": "uk", "Urdu": "ur", "Uyghur": "ug", "Uzbek": "uz", "Vietnamese": "vi",
    "Welsh": "cy", "Xhosa": "xh", "Yiddish": "yi", "Yoruba": "yo", "Zulu": "zu"
}

@app.route('/')
def index():
    return render_template('index.html', languages=LANGUAGES)

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data['text']
        source_lang = data['source_lang']
        target_lang = data['target_lang']
        
        translated = translate_with_groq(text, source_lang, target_lang)
        audio_data = generate_speech(translated, target_lang)
        
        return jsonify({
            'translated_text': translated,
            'audio_data': base64.b64encode(audio_data.getvalue()).decode('utf-8')
        })
    except Exception as e:
        logging.error(f"Error in translation: {str(e)}")
        return jsonify({'error': str(e)}), 500

def translate_with_groq(text, source_lang, target_lang):
    source_code = next((code for lang, code in LANGUAGES.items() if lang.lower() == source_lang.lower()), source_lang)
    target_code = next((code for lang, code in LANGUAGES.items() if lang.lower() == target_lang.lower()), target_lang)
    
    system_prompt = f"""You are a highly accurate translation system. Translate the given text from the language with ISO 639-1 code: {source_code} to the language with ISO 639-1 code: {target_code}.
Rules:
1. Translate ONLY into the specified target language. Do not use any other language.
2. Provide ONLY the translation, without any additional notes, explanations, or original text.
3. Maintain the original meaning, tone, and style as closely as possible.
4. If you're unsure about a translation, use the most common or neutral form of the word/phrase.

Now, translate the following text:"""

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error in Groq API call: {str(e)}")
        raise

def generate_speech(text, language):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return io.BytesIO(response.content)
        else:
            raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error in speech generation: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(debug=True)