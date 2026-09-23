import os
import threading
from flask import Flask
import discord
import google.generativeai as genai

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
CHANNEL_ID = 1150505286109495449

genai.configure(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

PREFIX = "!bot"

# Lista de modelos a probar en orden por si uno agota la cuota
MODELS_TO_TRY = [
    'gemini-3.6-flash',
    'gemini-2.5-flash',
    'gemini-1.5-flash',
    'gemini-1.5-pro'
]

def generate_with_fallback(prompt_text):
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                f"Eres un asistente dentro de un servidor de Minecraft Fabric 1.20.1. "
                f"Responde de forma muy breve y concisa en un solo párrafo para el chat del juego. "
                f"Mensaje: {prompt_text}"
            )
            if response and hasattr(response, 'text') and response.text:
                return response.text
        except Exception as e:
            # Si el error es de cuota (429), continúa probando el siguiente modelo
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"Cuota agotada en {model_name}, intentando siguiente modelo...")
                continue
            else:
                print(f"Error inesperado en {model_name}: {e}")
                continue
    return None

@client.event
async def on_ready():
    print(f'Bot iniciado correctamente como {client.user}')

@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID or message.author.id == client.user.id:
        return

    content = message.content
    content_lower = content.lower()

    if PREFIX not in content_lower:
        return

    split_index = content_lower.find(PREFIX) + len(PREFIX)
    prompt = content[split_index:].strip()

    if not prompt:
        await message.channel.send("¿Dime? Escribe tu consulta después de `!bot`.")
        return

    try:
        async with message.channel.typing():
            reply = generate_with_fallback(prompt)
            
            if reply:
                await message.channel.send(reply)
            else:
                await message.channel.send("Llegué al límite diario de consultas de la API gratuita. Intenta de nuevo más tarde.")
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        await message.channel.send("Ocurrió un problema temporal al procesar la respuesta.")

client.run(DISCORD_TOKEN)
