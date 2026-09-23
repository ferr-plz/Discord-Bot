import os
import threading
import re
from flask import Flask
import discord
import google.generativeai as genai
import cubiomes

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

# === REEMPLAZA CON LA SEED NUMÉRICA DE TU SERVIDOR ===
WORLD_SEED = 2193550371840698949  # Pon aquí tu número de seed (ejemplo: 123456789)

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

# Diccionario de traducción de estructuras
STRUCTURE_MAP = {
    'aldea': cubiomes.Village,
    'village': cubiomes.Village,
    'fortaleza': cubiomes.Fortress,
    'fortress': cubiomes.Fortress,
    'mansión': cubiomes.Mansion,
    'mansion': cubiomes.Mansion,
    'monumento': cubiomes.Ocean_Monument,
    'ciudad antigua': cubiomes.Ancient_City,
    'ancient city': cubiomes.Ancient_City,
    'templo': cubiomes.Jungle_Pyramid
}

def find_nearest_structure_exact(prompt_text):
    """Busca en el texto si el usuario pide una estructura y coordenadas"""
    prompt_lower = prompt_text.lower()
    
    # Extraer coordenadas del mensaje (ejemplo: -1500 500 o X: 200 Z: 300)
    numbers = [int(n) for n in re.findall(r'-?\d+', prompt_text)]
    
    if len(numbers) >= 2:
        player_x = numbers[0]
        player_z = numbers[1] if len(numbers) == 2 else numbers[2]
    else:
        player_x, player_z = 0, 0  # Por defecto busca desde el origen

    # Identificar estructura solicitada
    found_struct_type = None
    struct_name = ""
    for name, struct_type in STRUCTURE_MAP.items():
        if name in prompt_lower:
            found_struct_type = struct_type
            struct_name = name
            break

    if found_struct_type:
        try:
            # Cálculo matemático exacto estilo Chunkbase usando la seed
            generator = cubiomes.Generator(cubiomes.MC_1_20, WORLD_SEED)
            pos = generator.find_structure(found_struct_type, player_x, player_z)
            if pos:
                return f"COORDENADAS EXACTAS CALCULADAS (Chunkbase Engine): La {struct_name} más cercana a ({player_x}, {player_z}) está en X: {pos.x}, Z: {pos.z}."
        except Exception as e:
            print(f"Error calculando estructura: {e}")
            
    return None

def generate_with_fallback(prompt_text, calculated_data):
    info_context = f"\n[DATOS TÉCNICOS VERIFICADOS DEL MAPA]: {calculated_data}" if calculated_data else ""
    
    full_prompt = (
        f"Eres un asistente dentro de un servidor de Minecraft Fabric 1.20.1. "
        f"La SEED del mundo es: {WORLD_SEED}. {info_context} "
        f"Usa los datos técnicos verificados si están disponibles para responder con precisión absoluta. "
        f"Responde de forma muy breve y directa en un solo párrafo corto para el chat del juego. "
        f"Mensaje del jugador: {prompt_text}"
    )
    
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt)
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
            # 1. Calcular coordenadas exactas con cubiomes
            exact_data = find_nearest_structure_exact(prompt)
            
            # 2. Generar respuesta con Gemini usando la coordenada calculada
            reply = generate_with_fallback(prompt, exact_data)
            
            if reply:
                await message.channel.send(reply)
            else:
                await message.channel.send("Se agotó la cuota de la API Key temporalmente.")
    except Exception as e:
        print(f"Error interno: {e}")
        await message.channel.send("Ocurrió un problema temporal al procesar la respuesta.")

client.run(DISCORD_TOKEN)
