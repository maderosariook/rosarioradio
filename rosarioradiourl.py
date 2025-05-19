import discord
from discord.ext import commands, tasks
from discord import ui
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("Error: La variable de entorno DISCORD_BOT_TOKEN no está configurada.")
    exit()

EMISORAS = {
    "LA MEGA 97.9": "https://liveaudio.lamusica.com/NY_WSKQ_icy?aw_0_1st.playerld=onlineradiobox",
    "AMOR 93.1 NY": "https://liveaudio.lamusica.com/NY_WPAT_icy?aw_0_1st.playerld=onlineradiobox",
    "LA MAGIA FM": "https://radio.hostlagarto.com/lamagiafm/stream",
    "ROMANTICOS DEL AYER": os.getenv('ROMANTICOS_URL', "http://tropicalisima.org:8030/;"),
    "LA MEGA 106.9 PR": "https://liveaudio.lamusica.com/PR_WMEG_icy?aw_0_1st.playerld=onlineradiobox",
    "RADIO CRISTIANA": os.getenv('CRISTIANA_URL', "https://audiopro.gob.re/637e6.mp3")
}

currently_playing = {}  # {guild_id: voice_client}
playing_station = {}    # {guild_id: emisora_nombre}
idle_timers = {}        # {guild_id: asyncio.Task}
FIRST_CHANNEL_ID = int(os.getenv('FIRST_CHANNEL_ID', 0)) # ID del canal específico para conexión automática
IDLE_TIMEOUT = 15 * 60    # 15 minutos en segundos
auto_connect_status = {} # {guild_id: bool} para rastrear si ya se conectó automáticamente

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def disconnect_after_inactivity(guild_id):
    await asyncio.sleep(IDLE_TIMEOUT)
    guild = bot.get_guild(guild_id)
    if guild:
        voice_client = guild.voice_client
        if voice_client and voice_client.is_connected() and not voice_client.channel.members or all(m.id == bot.user.id for m in voice_client.channel.members):
            await voice_client.disconnect()
            if guild_id in currently_playing:
                del currently_playing[guild_id]
            if guild_id in playing_station:
                del playing_station[guild_id]
            if guild_id in idle_timers:
                del idle_timers[guild_id]
            if guild_id in auto_connect_status:
                del auto_connect_status[guild_id]
            # Enviar mensaje al primer canal de texto disponible
            channel = discord.utils.get(guild.text_channels, position=0)
            if channel:
                await channel.send("Me he desconectado por inactividad.")

class RadioButton(ui.Button):
    def __init__(self, label, style, url=None, custom_id=None):
        super().__init__(label=label, style=style, custom_id=f"radio_button_{label.replace(' ', '_')}")
        self._url = url
        self.nombre_emisora = label

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            if interaction.user.voice and interaction.user.voice.channel:
                try:
                    voice_client = await interaction.user.voice.channel.connect()
                    currently_playing[guild_id] = voice_client
                    # Iniciar/reiniciar el temporizador de inactividad al unirse
                    if guild_id in idle_timers and not idle_timers[guild_id].done():
                        idle_timers[guild_id].cancel()
                    idle_timers[guild_id] = bot.loop.create_task(disconnect_after_inactivity(guild_id))
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
            # Reiniciar el temporizador de inactividad al cambiar de emisora
            if guild_id in idle_timers and not idle_timers[guild_id].done():
                idle_timers[guild_id].cancel()
            idle_timers[guild_id] = bot.loop.create_task(disconnect_after_inactivity(guild_id))
        except Exception as e:
            await interaction.response.send_message(f"Error al reproducir: {e}", ephemeral=True)

class PlayPauseButton(ui.Button):
    def __init__(self, label, style, custom_id):
        super().__init__(label=label, style=style, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            # Reiniciar el temporizador de inactividad al interactuar con los controles
            if guild_id in idle_timers and not idle_timers[guild_id].done():
                idle_timers[guild_id].cancel()
            idle_timers[guild_id] = bot.loop.create_task(disconnect_after_inactivity(guild_id))

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

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    voice_client = guild.voice_client

    # Función para reiniciar el temporizador de inactividad
    async def reset_idle_timer(guild_id):
        if guild_id in idle_timers and not idle_timers[guild_id].done():
            idle_timers[guild_id].cancel()
        idle_timers[guild_id] = bot.loop.create_task(disconnect_after_inactivity(guild_id))

    # Si un usuario se une o cambia de canal
    if after.channel and (before.channel is None or before.channel != after.channel) and member != bot.user:
        # Conexión automática al canal específico la primera vez que un usuario entra
        if after.channel.id == FIRST_CHANNEL_ID and (guild.id not in auto_connect_status or not auto_connect_status[guild.id]):
            try:
                if voice_client and voice_client.is_connected():
                    await voice_client.move_to(after.channel)
                else:
                    voice_client = await after.channel.connect()
                    currently_playing[guild.id] = voice_client
                    # Enviar el menú al primer canal de texto disponible al unirse automáticamente
                    channel = discord.utils.get(guild.text_channels, position=0)
                    if channel:
                        await channel.send("¡Me he unido al canal de voz! Elige una emisora:", view=RadioMenu())
                    auto_connect_status[guild.id] = True # Marcar que ya se conectó automáticamente
                # Iniciar el temporizador de inactividad
                await reset_idle_timer(guild.id)
            except discord.ClientException:
                pass # Ya está conectado
            except Exception as e:
                print(f"Error al conectar automáticamente: {e}")
                pass
        # Reiniciar el temporizador si el bot ya está conectado y hay cambios de usuarios en su canal
        elif voice_client and voice_client.channel == after.channel:
            await reset_idle_timer(guild.id)

    # Si un usuario se va de un canal de voz donde está el bot
    if before.channel and (after.channel is None or after.channel != before.channel) and voice_client and voice_client.channel == before.channel:
        # Reiniciar el temporizador de inactividad si el canal ahora está vacío (excepto el bot)
        if not before.channel.members or all(m.id == bot.user.id for m in before.channel.members):
            await reset_idle_timer(guild.id)
        elif before.channel.members and any(m.id != bot.user.id for m in before.channel.members):
            # Si todavía hay usuarios (aparte del bot) en el canal del que *se fue* alguien,
            # y el bot sigue en ese canal, también reiniciamos el temporizador.
            # Esto es importante si alguien se va pero aún quedan otros.
            await reset_idle_timer(guild.id)

@bot.command(name="joinradio")
async def join_radio(ctx):
    """Une al bot al canal de voz del invocador y muestra el menú."""
    if ctx.author.voice and ctx.author.voice.channel:
        try:
            voice_client = await ctx.author.voice.channel.connect()
            currently_playing[ctx.guild.id] = voice_client
            # Iniciar el temporizador de inactividad al unirse por comando
            if ctx.guild.id in idle_timers and not idle_timers[ctx.guild.id].done():
                idle_timers[ctx.guild.id].cancel()
            idle_timers[ctx.guild.id] = bot.loop.create_task(disconnect_after_inactivity(ctx.guild.id))
            await ctx.send("¡Me he unido al canal de voz! Elige una emisora:", view=RadioMenu())
            # Resetear el estado de conexión automática si se usa el comando manualmente
            if ctx.guild.id in auto_connect_status:
                del auto_connect_status[ctx.guild.id]
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
        if ctx.guild.id in idle_timers:
            idle_timers[ctx.guild.id].cancel()
            del idle_timers[ctx.guild.id]
        if ctx.guild.id in auto_connect_status:
            del auto_connect_status[ctx.guild.id]
        await ctx.send("¡Me he desconectado del canal de voz!")
    else:
        await ctx.send("No estoy conectado a ningún canal de voz.")

@bot.command(name="rosarioradio")
async def radio_menu(ctx):
    """Muestra el menú de selección de emisoras con controles de reproducción."""
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
