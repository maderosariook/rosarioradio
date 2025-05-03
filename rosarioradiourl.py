import discord
from discord.ext import commands
from discord import ui
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("Error: La variable de entorno DISCORD_BOT_TOKEN no está configurada.")
    exit()

EMISORAS = {
    "LA MEGA": os.getenv('LA_MEGA_URL', "https://crystalout.surfernetwork.com:8001/WCHK-AM_MP3"),
    "LATINA 102.3 USA": os.getenv('LATINA_USA_URL', "https://sonos.norsanmedia.com/latinatriad"),
    "MEZCLA TROPICAL RD": os.getenv('MEZCLA_RD_URL', "https://stream.zeno.fm/esgo1lafgtstv"),
    "ROMANTICOS DEL AYER": os.getenv('ROMANTICOS_URL', "http://tropicalisima.org:8030/;"),
    "ALOFOKE FM": "http://radio5.domint.net:8222/stream",  # Reemplazamos "LATINURBANO" y su URL
    "RADIO CRISTIANA": os.getenv('CRISTIANA_URL', "https://audiopro.gob.re/637e6.mp3")
}

currently_playing = {}  # {guild_id: voice_client}
playing_station = {}   # {guild_id: emisora_nombre}

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

class RadioButton(ui.Button):
    def __init__(self, label, style, url=None, custom_id=None):
        super().__init__(label=label, style=style, custom_id=f"radio_button_{label.replace(' ', '_')}")
        self._url = url
        self.nombre_emisora = label

    async def callback(self, interaction: discord.Interaction):
        print(f"URL dentro de callback: {self._url}") # ¡Para debug!
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            if interaction.user.voice and interaction.user.voice.channel:
                try:
                    voice_client = await interaction.user.voice.channel.connect()
                    currently_playing[guild_id] = voice_client
                except discord.ClientException:
                    await interaction.response.send_message("Ya estoy conectado a un canal de voz en este servidor.", ephemeral=True)
                    return
                except Exception as e:
                    await interaction.response.send_message(f"Error al conectar al canal de voz: {e}", ephemeral=True)
                    return
            else:
                await interaction.response.send_message("Debes estar en un canal de voz para reproducir.", ephemeral=True)
                return

        try:
            voice_client.stop()
            source = discord.FFmpegPCMAudio(self._url, executable='ffmpeg', before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn -f s16le -ar 48000 -ac 2')
            voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
            playing_station[guild_id] = self.nombre_emisora
            await interaction.response.send_message(f"Reproduciendo: **{self.nombre_emisora}**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error al reproducir: {e}", ephemeral=True)
        # await interaction.response.defer()

class PlayPauseButton(ui.Button):
    def __init__(self, label, style, custom_id):
        super().__init__(label=label, style=style, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            if self.custom_id == "play_button":
                if voice_client.is_paused():
                    voice_client.resume()
                    await interaction.response.send_message("Reproducción reanudada.", ephemeral=True)
                else:
                    await interaction.response.send_message("Ya se está reproduciendo.", ephemeral=True)
            elif self.custom_id == "pause_button":
                if voice_client.is_playing():
                    voice_client.pause()
                    await interaction.response.send_message("Reproducción pausada.", ephemeral=True)
                else:
                    await interaction.response.send_message("No hay nada reproduciendo para pausar.", ephemeral=True)
        else:
            await interaction.response.send_message("No estoy conectado a ningún canal de voz.", ephemeral=True)

class RadioMenu(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        emisoras_actualizadas = EMISORAS.copy()
        self.clear_items() # Limpiamos los items existentes
        for nombre, url in emisoras_actualizadas.items():
            self.add_item(RadioButton(label=nombre, style=discord.ButtonStyle.primary, url=url))
        self.add_item(PlayPauseButton(label="Play", style=discord.ButtonStyle.green, custom_id="play_button"))
        self.add_item(PlayPauseButton(label="Pause", style=discord.ButtonStyle.red, custom_id="pause_button"))

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command(name="joinradio")
async def join_radio(ctx):
    """Une al bot al canal de voz del invocador y muestra el menú."""
    if ctx.author.voice and ctx.author.voice.channel:
        try:
            voice_client = await ctx.author.voice.channel.connect()
            currently_playing[ctx.guild.id] = voice_client
            # Re-enviamos el menú actualizado
            await ctx.send("¡Me he unido al canal de voz! Elige una emisora:", view=RadioMenu())
        except discord.ClientException:
            await ctx.send("Ya estoy conectado a un canal de voz en este servidor.")
        except Exception as e:
            await ctx.send(f"Error al conectar al canal de voz: {e}")
    else:
        await ctx.send("Debes estar en un canal de voz para que me una.")

@bot.command(name="leaveradio")
async def leave_radio(ctx):
    """Saca al bot del canal de voz."""
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        if ctx.guild.id in currently_playing:
            del currently_playing[ctx.guild.id]
        if ctx.guild.id in playing_station:
            del playing_station[ctx.guild.id]
        await ctx.send("¡Me he desconectado del canal de voz!")
    else:
        await ctx.send("No estoy conectado a ningún canal de voz.")

@bot.command(name="rosarioradio")
async def radio_menu(ctx):
    """Muestra el menú de selección de emisoras con controles de reproducción."""
    # Re-enviamos el menú actualizado
    await ctx.send("Elige una emisora y controla la reproducción:", view=RadioMenu())

@bot.command(name="playingradio")
async def playing_radio(ctx):
    """Muestra la emisora que se está reproduciendo actualmente."""
    guild_id = ctx.guild.id
    if guild_id in playing_station:
        await ctx.send(f"Actualmente reproduciendo: **{playing_station[guild_id]}**")
    else:
        await ctx.send("No se está reproduciendo ninguna emisora en este servidor.")

if __name__ == "__main__":
    bot.run(TOKEN)
