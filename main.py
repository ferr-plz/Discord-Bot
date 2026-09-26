import os
import discord
import google.generativeai as genai
from flask import Flask
from threading import Thread

# 1. Configuración de Servidor Web para mantener vivo en Render
app = Flask('')

@app.route('/')
def home():
    return "Bot activo 24/7"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Configuración de Gemini y Discord
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

genai.configure(api_key=GENAI_API_KEY)
# Usamos el modelo más rápido y actualizado
model = genai.GenerativeModel('gemini-1.5-flash')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 3. Manejo de Instrucciones Personalizadas (System Prompt)
RULES_FILE = "custom_rules.txt"

def load_custom_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "No menciones la semilla a menos que te la pregunten explícitamente."

def save_custom_rules(new_rules):
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        f.write(new_rules)

# 4. Eventos de Discord
@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Comando para cambiar las instrucciones desde Discord
    if message.content.startswith("!bot config "):
        new_instructions = message.content[12:].strip()
        save_custom_rules(new_instructions)
        await message.channel.send(f"✅ **Instrucciones actualizadas:**\n> {new_instructions}")
        return

    # Comando principal para hablar con la IA
    if message.content.startswith("!bot "):
        user_prompt = message.content[5:].strip()
        
        # Cargar las instrucciones actuales
        custom_rules = load_custom_rules()
        
        # Unir las instrucciones del sistema con el mensaje del usuario
        full_prompt = f"""
        [INSTRUCCIONES DEL SISTEMA]
        Eres un asistente útil para un servidor de Minecraft Fabric 1.20.1.
        Sigue estrictamente estas reglas de comportamiento: {custom_rules}
        
        [MENSAJE DEL USUARIO]
        {user_prompt}
        """

        try:
            response = model.generate_content(full_prompt)
            await message.channel.send(response.text)
        except Exception as e:
            print(f"Error con la API de Gemini: {e}")
            await message.channel.send("Ocurrió un error al procesar tu solicitud.")

# Iniciar servidor web y bot
keep_alive()
client.run(DISCORD_TOKEN)
