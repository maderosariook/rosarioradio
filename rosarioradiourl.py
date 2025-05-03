import discord
from discord.ext import commands
import os
import subprocess

# *** Lee el token desde la variable de entorno ***
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
# *** Reemplaza con el ID del canal de voz al que quieres que el bot se conecte ***
VOICE_CHANNEL_ID = 1360402590264725664
# *** Define los intents ***
intents = discord.Intents.default()
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    try:
        voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
        if voice_channel:
            vc = await voice_channel.connect()
            print(f"Conectado al canal de voz: {voice_channel.name}")
            try:
                # *** CÓDIGO DE PRUEBA DE FFMPEG ***
                try:
                    process = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
                    print(f"Versión de ffmpeg:\n{process.stdout}")
                except FileNotFoundError:
                    print("ffmpeg no se encontró en el sistema.")
                except subprocess.TimeoutExpired:
                    print("El comando ffmpeg tardó demasiado en responder.")
                except Exception as e:
                    print(f"Ocurrió un error al ejecutar ffmpeg: {e}")
                # *** FIN DEL CÓDIGO DE PRUEBA DE FFMPEG ***

                radio_url = 'http://icecast.BroadcastingWorld.net:8000/stream'
                vc.play(discord.FFmpegPCMAudio(f'-i {radio_url}', executable='ffmpeg', before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn -f s16le -ar 48000 -ac 2'))
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
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: La variable de entorno DISCORD_BOT_TOKEN no está configurada.")
