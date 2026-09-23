import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
import google.generativeai as genai

# Servidor HTTP para Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Iniciar servidor en hilo secundario
threading.Thread(target=run_web_server, daemon=True).start()

# Claves de acceso
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
CHANNEL_ID = 1150505286109495449

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot iniciado correctamente como {client.user}')

@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return

    if message.author.id == client.user.id:
        return

    prompt = ""

    # Capturar webhook de Minecraft (Admin Log) o mensajes normales
    if message.webhook_id is not None or message.author.bot:
        if ":" in message.content:
            prompt = message.content.split(":", 1)[-1].strip()
        else:
            prompt = message.content.strip()
    else:
        prompt = message.content.strip()

    if not prompt:
        return

    try:
        async with message.channel.typing():
            response = model.generate_content(
                f"Eres un asistente dentro de un servidor de Minecraft Fabric 1.20.1. "
                f"Responde de forma breve y concisa en un solo párrafo corto para el chat del juego. "
                f"Mensaje: {prompt}"
            )
            if response.text:
                await message.channel.send(response.text)
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

client.run(DISCORD_TOKEN)