import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
RADIO_STREAM_URL = 'https://playerservices.streamtheworld.com/api/livestream-redirect/LOS40_URBANAAC.aac'
VOICE_CHANNEL_ID = 1360402590264725664

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
    if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
        try:
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(RADIO_STREAM_URL, executable='ffmpeg'))
            print(f'Conectado a {voice_channel.name} y transmitiendo radio.')
        except discord.ClientException:
            print("Ya estoy conectado a un canal de voz.")
        except ValueError:
            print("La URL del stream no es válida.")
        except Exception as e:
            print(f"Error al conectar o reproducir (on_ready): {e}")
    else:
        print(f"No se encontró el canal de voz con ID {VOICE_CHANNEL_ID}")

@bot.command()
async def joinradio(ctx):
    print(f"Comando joinradio recibido por {ctx.author.name}")
    voice_channel = ctx.author.voice.channel
    if voice_channel:
        try:
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(RADIO_STREAM_URL, executable='ffmpeg'))
            await ctx.send(f'Conectado a {voice_channel.name} y transmitiendo la radio.')
        except discord.ClientException:
            await ctx.send("Ya estoy conectado a un canal de voz.")
        except ValueError:
            await ctx.send("La URL del stream no es válida.")
        except Exception as e:
            await ctx.send(f"Error al conectar o reproducir (joinradio): {e}")
    else:
        await ctx.send("Debes estar en un canal de voz para que pueda unirme.")

@bot.command()
async def leaveradio(ctx):
    vc = ctx.guild.voice_client
    if vc and vc.is_connected():
        await vc.disconnect()
        await ctx.send("Desconectado del canal de voz.")
    else:
        await ctx.send("No estoy conectado a ningún canal de voz.")

bot.run(TOKEN)
