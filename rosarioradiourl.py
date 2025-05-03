import discord
from discord.ext import commands
import os
from discord import ui

TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
VOICE_CHANNEL_ID_BOT_PRESENTE = 1360402590264725664  # ID del canal de voz donde el bot estará "silencioso"
EMISORAS = {
    "LA MEGA": "https://crystalout.surfernetwork.com:8001/WCHK-AM_MP3",
    "LATINA 102.3 USA": "https://sonos.norsanmedia.com/latinatriad",
    "MEZCLA TROPICAL RD": "https://stream.zeno.fm/esgo1lafgtstv",
    "ROMANTICOS DEL AYER": "http://tropicalisima.org:8030/;",
    "LATINURBANO": "https://stream.zeno.fm/cyku8zxvqg8uv",
    "RADIO CRISTIANA": "https://audiopro.gob.re/637e6.mp3"
}
currently_playing = {}
voice_clients = {}

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class RadioMenu(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(EmisoraSelect())

class EmisoraSelect(ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=nombre, value=url) for nombre, url in EMISORAS.items()]
        super().__init__(placeholder="Elige una emisora...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        url = self.values[0]
        nombre_emisora = [name for name, u in EMISORAS.items() if u == url][0]
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            if interaction.user.voice and interaction.user.voice.channel:
                voice_client = await interaction.user.voice.channel.connect()
                voice_clients[interaction.guild.id] = voice_client
            else:
                await interaction.response.send_message("Debes estar en un canal de voz para reproducir.", ephemeral=True)
                return

        try:
            voice_client.stop()  # Detener la reproducción anterior si existe
            source = discord.FFmpegPCMAudio(url, executable='ffmpeg', before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn -f s16le -ar 48000 -ac 2')
            voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
            currently_playing[interaction.guild.id] = nombre_emisora
            await interaction.response.send_message(f"Reproduciendo: **{nombre_emisora}**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error al reproducir: {e}", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    if VOICE_CHANNEL_ID_BOT_PRESENTE:
        voice_channel = bot.get_channel(VOICE_CHANNEL_ID_BOT_PRESENTE)
        if voice_channel and not any(vc.channel == voice_channel for vc in bot.voice_clients):
            try:
                await voice_channel.connect()
                print(f"Bot conectado silenciosamente a {voice_channel.name}")
            except Exception as e:
                print(f"Error al conectar al canal de voz silencioso: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        return

    voice_client = bot.voice_client
    if voice_client and member.guild == voice_client.guild:
        if after.channel == voice_client.channel and before.channel != after.channel:
            # Enviar el menú al chat del canal de voz
            await after.channel.send("¡Hola! Elige una emisora para reproducir:", view=RadioMenu())

        if voice_client.channel and not voice_client.channel.members:
            try:
                await voice_client.disconnect()
                if member.guild.id in voice_clients:
                    del voice_clients[member.guild.id]
                print(f"Bot desconectado de {voice_client.channel.name} por inactividad.")
            except Exception as e:
                print(f"Error al desconectar por inactividad: {e}")

@bot.command()
async def play(ctx, emisora_nombre: str = None):
    """Reproduce la emisora seleccionada."""
    if not emisora_nombre:
        await ctx.send("Elige una emisora usando el menú desplegable.")
        return

    if emisora_nombre not in EMISORAS:
        await ctx.send(f"Emisora '{emisora_nombre}' no encontrada. Usa el menú para elegir.")
        return

    url = EMISORAS[emisora_nombre]
    voice_client = ctx.guild.voice_client
    if voice_client is None:
        if ctx.author.voice and ctx.author.voice.channel:
            try:
                voice_client = await ctx.author.voice.channel.connect()
                voice_clients[ctx.guild.id] = voice_client
            except Exception as e:
                await ctx.send(f"Error al conectar al canal de voz: {e}")
                return
        else:
            await ctx.send("Debes estar en un canal de voz para reproducir.")
            return

    try:
        voice_client.stop()
        source = discord.FFmpegPCMAudio(url, executable='ffmpeg', before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn -f s16le -ar 48000 -ac 2')
        voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
        currently_playing[ctx.guild.id] = emisora_nombre
        await ctx.send(f"Reproduciendo: **{emisora_nombre}**")
    except Exception as e:
        await ctx.send(f"Error al reproducir: {e}")

@bot.command()
async def pause(ctx):
    """Pausa la reproducción."""
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Reproducción pausada.")
    else:
        await ctx.send("No hay nada reproduciendo para pausar.")

@bot.command()
async def resume(ctx):
    """Resume la reproducción."""
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Reproducción reanudada.")
    else:
        await ctx.send("No hay nada pausado para reanudar.")

@bot.command()
async def stop(ctx):
    """Detiene la reproducción y desconecta el bot."""
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        del currently_playing[ctx.guild.id]
        await ctx.send("Reproducción detenida.")
    else:
        await ctx.send("No hay nada reproduciendo para detener.")

@bot.command()
async def menu(ctx):
    """Muestra el menú de la radio."""
    await ctx.send("Elige una emisora para reproducir:", view=RadioMenu())

if __name__ == "__main__":
    bot.run(TOKEN)
