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
            # Usamos gemini-1.5-flash que tiene disponibilidad garantizada
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                f"Eres un asistente dentro de un servidor de Minecraft Fabric 1.20.1. Responde de forma muy breve y concisa en un solo párrafo corto para el chat del juego. Mensaje: {prompt}"
            )
            
            if response and hasattr(response, 'text') and response.text:
                await message.channel.send(response.text)
            else:
                await message.channel.send("No se pudo generar texto.")
    except Exception as e:
        print(f"Error con Gemini: {e}")
        await message.channel.send(f"Error con la API: {e}")

client.run(DISCORD_TOKEN)
