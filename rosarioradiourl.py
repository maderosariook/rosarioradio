import discord
import os
from discord.ext import commands

# Lee el token de la variable de entorno 'DISCORD_BOT_TOKEN'
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# Verifica si la variable de entorno está configurada
if TOKEN is None:
    print("Error: La variable de entorno DISCORD_BOT_TOKEN no está configurada.")
    exit()

# Define los intents (intenciones) que tu bot necesitará
intents = discord.Intents.default()
# Habilita intents privilegiados si tu bot los necesita (por ejemplo, miembros del servidor)
# intents.members = True

# Inicializa el bot con un prefijo de comando
bot = commands.Bot(command_prefix='!', intents=intents)

# Evento que se ejecuta cuando el bot está listo
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')
    await bot.change_presence(activity=discord.Streaming(name="Radio Rosario", url="tu_url_de_streaming_aqui")) # Reemplaza con tu URL

# Ejemplo de un comando (puedes agregar más)
@bot.command()
async def hola(ctx):
    await ctx.send('¡Hola!')

# Ejecuta el bot con el token de la variable de entorno
bot.run(TOKEN)