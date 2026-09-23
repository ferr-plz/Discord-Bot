import os
import threading
import json
import urllib.request
import urllib.parse
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
CHAT_CHANNEL_ID = 1150505286109495449

# === COLOCA AQUÍ LA SEED DE TU SERVIDOR ===
WORLD_SEED = "PEGA_AQUI_LA_SEED_DE_TU_SERVER"

genai.configure(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

PREFIX = "!bot"

MODELS_TO_TRY = [
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'gemini-2.5-flash',
    'gemini-3.6-flash'
]

def generate_with_fallback(prompt_text):
    system_instruction = (
        f"Eres un asistente dentro de un servidor de Minecraft Fabric 1.20.1. "
        f"La SEED del mundo es: {WORLD_SEED}. "
        f"Si el jugador pregunta por estructuras o ubicaciones, ayúdalo a entender cómo encontrarlas "
        f"o interpreta sus coordenadas. Responde de forma muy breve y concisa en un solo párrafo corto."
    )
    
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt_text)
            if response and hasattr(response, 'text') and response.text:
                return response.text
        except Exception as e:
            print(f"Error en {model_name}: {e}")
            continue
    return None

@client.event
async def on_ready():
    print(f'Bot iniciado correctamente como {client.user}')

@client.event
async def on_message(message):
    if message.channel.id != CHAT_CHANNEL_ID or message.author.id == client.user.id:
        return

    content = message.content
    content_lower = content.lower()

    if "server executed command" in content_lower or "server stopped!" in content_lower:
        return

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
                await message.channel.send("No pude procesar la respuesta en este momento.")
    except Exception as e:
        print(f"Error: {e}")
        await message.channel.send("Error al procesar la respuesta.")

client.run(DISCORD_TOKEN)
