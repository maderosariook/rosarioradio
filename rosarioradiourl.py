import discord
from discord.ext import commands

# *** IMPORTANTE: Reemplaza 'TU_TOKEN_DE_BOT' con el token real de tu bot de Discord ***
TOKEN = 'MTM2Njg5MDYyMDQyMTAxNzczMw.GnfQBd.cuYFVE6-gtsNKQwI1vAtkCl61J0KTAMtti3yDw'
# *** Reemplaza con el ID del canal de voz al que quieres que el bot se conecte ***
VOICE_CHANNEL_ID = 1360402590264725664  # Ejemplo de ID, debes obtener el tuyo

# *** 1. Define los intents ***
intents = discord.Intents.default()
intents.voice_states = True  # Necesario para conectar y escuchar en canales de voz

# *** 2. Pasa los intents al crear la instancia del bot ***
bot = commands.Bot(command_prefix='!', intents=intents)  # Incluye 'intents=intents'

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    try:
        voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
        if voice_channel:
            vc = await voice_channel.connect()
            print(f"Conectado al canal de voz: {voice_channel.name}")

            # *** Aquí debes agregar la lógica para iniciar la reproducción de tu radio en vivo
            # *** utilizando vc.play(discord.FFmpegPCMAudio(...))
            # *** Asegúrate de capturar cualquier excepción que pueda ocurrir durante este proceso

            # Ejemplo (debes adaptarlo a tu implementación):
            try:
                radio_url = 'https://sonos.norsanmedia.com/latinatriad'  # Reemplaza con la URL de tu radio
                vc.play(discord.FFmpegPCMAudio(radio_url, executable='ffmpeg'))
                print(f"Iniciando la reproducción desde: {radio_url}")
            except Exception as e:
                print(f"Error al iniciar la reproducción: {e}")

        else:
            print(f"No se encontró el canal de voz con ID: {VOICE_CHANNEL_ID}")

    except Exception as e:
        print(f"Error en on_ready al conectar o iniciar la reproducción: {e}")

@bot.command()
async def desconectar(ctx):
    """Desconecta el bot del canal de voz."""
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        await ctx.send("¡Me he desconectado del canal de voz!")
    else:
        await ctx.send("No estoy conectado a ningún canal de voz.")

if __name__ == "__main__":
    bot.run(TOKEN)
