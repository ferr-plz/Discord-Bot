import os
import threading
from flask import Flask
import discord
import google.generativeai as genai

# Servidor Flask para mantener activo Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# Variables de entorno
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
CHANNEL_ID = 1150505286109495449

genai.configure(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Función para obtener el modelo disponible dinámicamente
def get_working_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"Modelos disponibles en tu cuenta: {models}")
        for m in models:
            if 'flash' in m or 'pro' in m:
                return genai.GenerativeModel(m)
        if models:
            return genai.GenerativeModel(models[0])
    except Exception as e:
        print(f"Error listando modelos: {e}")
    # Fallback predeterminado
    return genai.GenerativeModel('models/gemini-1.5-flash')

@client.event
async def on_ready():
    print(f'Bot iniciado correctamente como {client.user}')

@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID or message.author.id == client.user.id:
        return

    prompt = message.content.strip()
    if not prompt:
        return

    try:
        async with message.channel.typing():
            model = get_working_model()
            response = model.generate_content(
                f"Eres un asistente dentro de un servidor de Minecraft Fabric 1.20.1. "
                f"Responde de forma muy breve para el chat del juego. Mensaje: {prompt}"
            )
            
            if response and hasattr(response, 'text') and response.text:
                await message.channel.send(response.text)
            else:
                await message.channel.send("No se pudo generar respuesta.")
    except Exception as e:
        print(f"Error con Gemini: {e}")
        await message.channel.send(f"Error con la API: {e}")

client.run(DISCORD_TOKEN)
