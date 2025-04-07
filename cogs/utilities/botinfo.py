import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color
from datetime import datetime
import platform
import psutil
import os

class BotInfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="botinfo", description="Affiche les informations détaillées sur le bot")
    async def botinfo(self, interaction: discord.Interaction):
        
        total_members = sum(g.member_count for g in self.bot.guilds)
        total_channels = sum(len(g.channels) for g in self.bot.guilds)
        total_roles = sum(len(g.roles) for g in self.bot.guilds)
        total_emojis = sum(len(g.emojis) for g in self.bot.guilds)
        
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        
        embed = discord.Embed(
            title="🤖 Skycy",
            description=f"```Manager automatisé du serveur discord de Skycy.```\n"
                       f"ID: `{self.bot.user.id}`",
            color=get_embed_color("utilities")
        )
        
        
        embed.add_field(
            name="📊 Statistiques",
            value=f"🏰 Serveurs: **{len(self.bot.guilds):,}**\n"
                  f"👥 Utilisateurs: **{total_members:,}**\n"
                  f"📺 Salons: **{total_channels:,}**\n"
                  f"👑 Rôles: **{total_roles:,}**\n"
                  f"😀 Emojis: **{total_emojis:,}**",
            inline=True
        )
        
        
        embed.add_field(
            name="⚡ Performance",
            value=f"📡 Latence: **{round(self.bot.latency * 1000)}ms**\n"
                  f"💻 CPU: **{cpu_percent}%**\n"
                  f"💾 RAM: **{memory.percent}%**\n"
                  f"💿 Disque: **{disk.percent}%**",
            inline=True
        )
        
        
        embed.add_field(
            name="💻 Système",
            value=f"🐍 Python: **{platform.python_version()}**\n"
                  f"📦 Discord.py: **{discord.__version__}**\n"
                  f"🖥️ OS: **{platform.system()} {platform.release()}**",
            inline=True
        )
        
        if hasattr(self.bot, 'start_time'):
            uptime = datetime.now() - self.bot.start_time
            hours = uptime.total_seconds() / 3600
            days = hours / 24
            minutes = (hours % 1) * 60
            seconds = (minutes % 1) * 60
            
            embed.add_field(
                name="⏰ Temps de fonctionnement",
                value=f"📅 Depuis: <t:{int(self.bot.start_time.timestamp())}:F>\n"
                      f"⏱️ Uptime: **{int(days)}j {int(hours % 24)}h {int(minutes)}m {int(seconds)}s**",
                inline=True
            )
        
        
        total_commands = len(self.bot.tree.get_commands())
        embed.add_field(
            name="📝 Commandes",
            value=f"📋 Total: **{total_commands:,}**\n"
                  f"📦 Modules: **{len(self.bot.cogs):,}**",
            inline=True
        )
        
        
        embed.add_field(
            name="💬 Support",
            value="[Discord](https://discord.gg/ug9WcY6fj4)\n"
                  "[GitHub](https://github.com/skycy_bot)",
            inline=True
        )
        
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        if self.bot.user.banner:
            embed.set_image(url=self.bot.user.banner.url)
            
        
        embed.set_footer(
            text=f"Demandé par {interaction.user.name} • {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
            
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BotInfoCommand(bot)) 
