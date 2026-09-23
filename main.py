import os
import threading
from flask import Flask
import discord
from google import genai

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

# Cliente de Gemini SDK actualizado
ai_client = genai.Client(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

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
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Eres un asistente dentro de un servidor de Minecraft Fabric 1.20.1. Responde de forma muy breve y concisa en un solo párrafo corto para el chat del juego. Mensaje: {prompt}"
            )
            
            if response and response.text:
                await message.channel.send(response.text)
            else:
                await message.channel.send("No se pudo generar texto.")
    except Exception as e:
        print(f"Error detallado con Gemini: {e}")
        await message.channel.send(f"Error con la API: {e}")

client.run(DISCORD_TOKEN)
