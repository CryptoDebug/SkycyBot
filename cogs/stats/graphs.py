import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
from utils.colors import get_embed_color

class StatsGraphs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_file = "data/stats/server_stats.json"
        self.load_stats()
        
    def load_stats(self):
        
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                self.stats = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.stats = {}
        return self.stats
            
    def get_guild_stats(self, guild_id):
        
        guild_id = str(guild_id)
        
        if guild_id not in self.stats:
            self.stats[guild_id] = {
                "messages": {},
                "voice_time": {},
                "joins": [],
                "leaves": [],
                "commands": {},
                "reactions": {}
            }
            
        return self.stats[guild_id]
        
    async def create_messages_graph(self, guild_stats):
        
        
        users = sorted(
            guild_stats["messages"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  
        
        if not users:
            return None
            
        
        plt.figure(figsize=(10, 6))
        plt.bar([u[0] for u in users], [u[1] for u in users])
        plt.title("Top 10 des utilisateurs par messages")
        plt.xlabel("Utilisateurs")
        plt.ylabel("Nombre de messages")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()
        
        return buffer

    async def create_voice_time_graph(self, guild_stats):
        
        
        users = sorted(
            guild_stats["voice_time"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  
        
        if not users:
            return None
            
        
        hours = [t/3600 for t in [u[1] for u in users]]
        
        
        plt.figure(figsize=(10, 6))
        plt.bar([u[0] for u in users], hours)
        plt.title("Top 10 des utilisateurs par temps en vocal")
        plt.xlabel("Utilisateurs")
        plt.ylabel("Temps (heures)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()
        
        return buffer

    async def create_commands_graph(self, guild_stats):
        
        
        users = sorted(
            guild_stats["commands"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  
        
        if not users:
            return None
            
        
        plt.figure(figsize=(10, 6))
        plt.bar([u[0] for u in users], [u[1] for u in users])
        plt.title("Top 10 des utilisateurs par commandes utilisées")
        plt.xlabel("Utilisateurs")
        plt.ylabel("Nombre de commandes")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()
        
        return buffer
        
    @app_commands.command(name="graphs", description="Afficher les graphiques de statistiques")
    async def graphs(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        if guild_id not in self.stats:
            await interaction.response.send_message("Aucune statistique n'est disponible pour ce serveur!", ephemeral=True)
            return

        await interaction.response.defer()

        
        messages_graph = await self.create_messages_graph(self.stats[guild_id])
        voice_time_graph = await self.create_voice_time_graph(self.stats[guild_id])
        commands_graph = await self.create_commands_graph(self.stats[guild_id])

        
        embed = discord.Embed(
            title="📊 Graphiques de statistiques",
            description="Voici les graphiques des statistiques du serveur:",
            color=get_embed_color("stats")
        )

        
        await interaction.followup.send(
            embed=embed,
            files=[
                discord.File(messages_graph, "messages.png"),
                discord.File(voice_time_graph, "voice_time.png"),
                discord.File(commands_graph, "commands.png")
            ]
        )
        
async def setup(bot):
    await bot.add_cog(StatsGraphs(bot)) 
