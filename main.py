import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
import google.generativeai as genai

# Servidor HTTP para mantener activo Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

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
            # Modelo compatible y robusto
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                f"Eres un asistente dentro de un servidor de Minecraft. "
                f"Responde muy brevemente en una sola frase corta. "
                f"Mensaje del jugador: {prompt}"
            )
            
            if response and response.text:
                await message.channel.send(response.text)
            else:
                await message.channel.send("No pude procesar esa respuesta.")
    except Exception as e:
        print(f"Error con Gemini API: {e}")
        await message.channel.send("Ocurrió un error al consultar la IA.")

client.run(DISCORD_TOKEN)
