import os
import discord
import google.generativeai as genai
from flask import Flask
from threading import Thread

# 1. Servidor web para mantener activo en Render
app = Flask('')

@app.route('/')
def home():
    return "Bot activo 24/7"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Configuración de API Keys y Cliente
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 3. Manejo del archivo de reglas persistentes
RULES_FILE = "custom_rules.txt"

def load_custom_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "No menciones ni incluyas la semilla en tus saludos o respuestas a menos que el usuario te la pida explícitamente."

def save_custom_rules(new_rules):
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        f.write(new_rules)

# 4. Eventos del Bot
@client.event
async def on_ready():
    print(f'Bot conectado exitosamente como {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Comando para cambiar las reglas dinámicamente desde Discord
    if message.content.startswith("!bot config "):
        new_instructions = message.content[12:].strip()
        save_custom_rules(new_instructions)
        await message.channel.send(f"✅ **Instrucciones actualizadas:**\n> {new_instructions}")
        return

    # Comando principal del bot
    if message.content.startswith("!bot "):
        user_prompt = message.content[5:].strip()
        
        # Cargar las instrucciones configuradas desde Discord
        custom_rules = load_custom_rules()
        
        # Contexto completo con la Seed del servidor
        full_prompt = f"""
        [CONTEXTO DEL SERVIDOR]
        Juego: Minecraft Fabric 1.20.1
        Semilla (Seed): 2193550371840698949

        [INSTRUCCIONES Y REGLAS DE COMPORTAMIENTO]
        - Eres el asistente oficial del servidor de Minecraft.
        - Reglas adicionales del administrador: {custom_rules}

        [PREGUNTA DEL USUARIO]
        {user_prompt}
        """

        try:
            response = model.generate_content(full_prompt)
            await message.channel.send(response.text)
        except Exception as e:
            print(f"Error en Gemini API: {e}")
            await message.channel.send("Ocurrió un error al procesar la respuesta.")

keep_alive()
client.run(DISCORD_TOKEN)
