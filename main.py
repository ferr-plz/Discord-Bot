import os
import discord
import google.generativeai as genai

# Obtener claves de acceso desde Koyeb
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# ID de tu canal de Discord
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
    # Solo escuchar en el canal de Minecraft
    if message.channel.id != CHANNEL_ID:
        return

    # No responderse a sí mismo
    if message.author.id == client.user.id:
        return

    prompt = ""

    # Si viene del webhook de Minecraft (Admin Log)
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