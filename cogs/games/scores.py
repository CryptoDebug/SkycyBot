import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from utils.colors import get_embed_color

class Scores(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scores_file = "data/games/scores.json"
        self.load_scores()
        
    def load_scores(self):
        
        try:
            with open(self.scores_file, "r", encoding="utf-8") as f:
                self.scores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.scores = {}
            
    @app_commands.command(name="scores", description="Afficher les scores des jeux")
    async def scores(self, interaction: discord.Interaction):
        
        
        self.load_scores()
        
        if not self.scores:
            await interaction.response.send_message("Aucun score n'a encore été enregistré!", ephemeral=True)
            return
            
        
        embed = discord.Embed(
            title="🏆 Scores des jeux",
            description="Voici les meilleurs scores des différents jeux:",
            color=get_embed_color("games")
        )
        
        
        for guild_id, guild_scores in self.scores.items():
            if not guild_scores:
                continue
                
            
            sorted_scores = sorted(guild_scores.items(), key=lambda x: x[1], reverse=True)
            
            
            top_scores = sorted_scores[:10]
            
            
            scores_text = ""
            for i, (user_id, score) in enumerate(top_scores):
                user = self.bot.get_user(int(user_id))
                username = user.name if user else f"Utilisateur {user_id}"
                scores_text += f"{i+1}. **{username}**: {score} points\n"
                
            
            guild = self.bot.get_guild(int(guild_id))
            guild_name = guild.name if guild else f"Serveur {guild_id}"
            
            embed.add_field(
                name=guild_name,
                value=scores_text or "Aucun score",
                inline=False
            )
            
        
        embed.set_footer(text=f"Demandé par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
        
async def setup(bot):
    await bot.add_cog(Scores(bot)) 
