import discord
from discord import app_commands
from discord.ext import commands
from typing import Dict, List
from utils.colors import get_embed_color
import json

class HelpView(discord.ui.View):
    def __init__(self, bot, categories, cog_categories):
        super().__init__(timeout=180)
        self.bot = bot
        self.categories = categories
        self.cog_categories = cog_categories
        self.current_category = None
        
        
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {"embed_colors": {}}
        
        
        for category_name, category_title in categories.items():
            button = discord.ui.Button(
                label=category_title,
                custom_id=f"help_{category_name}",
                style=discord.ButtonStyle.primary
            )
            button.callback = lambda interaction, cat=category_name: self.switch_category(interaction, cat)
            self.add_item(button)

    async def switch_category(self, interaction: discord.Interaction, category_name: str):
        if self.current_category == category_name:
            return await interaction.response.defer()
            
        self.current_category = category_name
        embed = await self.create_category_embed(category_name)
        await interaction.response.edit_message(embed=embed)

    async def create_category_embed(self, category_name: str) -> discord.Embed:
        
        color = self.config.get("embed_colors", {}).get(category_name, self.config.get("embed_colors", {}).get("default", 0xFFD700))
        
        embed = discord.Embed(
            title=f"📚 {self.categories[category_name]}",
            description="Voici les commandes disponibles dans cette catégorie :",
            color=discord.Color.from_str(color) if isinstance(color, str) else color
        )
        
        commands_list = []
        for cog_name, cog_category in self.cog_categories.items():
            if cog_category == category_name:
                cog = self.bot.get_cog(cog_name)
                if cog:
                    for cmd in cog.get_app_commands():
                        commands_list.append(f"`/{cmd.name}` • {cmd.description}")
        
        if commands_list:
            embed.add_field(
                name="Commandes",
                value="\n".join(commands_list),
                inline=False
            )
        else:
            embed.add_field(
                name="Information",
                value="Aucune commande disponible dans cette catégorie.",
                inline=False
            )
        
        embed.add_field(
            name="💡 Note",
            value="Utilisez `/` pour voir toutes les commandes disponibles dans Discord",
            inline=False
        )
        
        embed.set_footer(
            text=f"Skycy • {len(self.bot.cogs)} modules chargés",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        return embed

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.categories = {
            "administration": "🔨 Administration",
            "moderation": "🔨 Modération",
            "utilities": "🛠️ Utilitaires",
            "stats": "📊 Statistiques",
            "games": "🎮 Jeux",
            "welcome": "👋 Bienvenue"
        }
        
        
        self.cog_categories = {
            
            "InvitesConfigCommand": "administration",
            "LogsConfigCommand": "administration",
            "AutoClearSystem": "administration",
            "AntiSpamConfigCommand": "administration",
            "AntiLinksConfigCommand": "administration",

            
            "BanCommand": "moderation",
            "KickCommand": "moderation",
            "SoftbanCommand": "moderation",
            "ClearCommand": "moderation",
            
            
            "BotInfoCommand": "utilities",
            "VoiceManager": "utilities",
            "ServerInfoCommand": "utilities",
            "UserInfoCommand": "utilities",

            
            
            "StatsGraphs": "stats",
            
            
            "Hangman": "games",
            "TicTacToe": "games",
            "Scores": "games",
            
            
            "WelcomeConfig": "welcome",
            "WelcomeEvents": "welcome"
        }

    @app_commands.command(name="help", description="Affiche les commandes disponibles")
    async def help_command(self, interaction: discord.Interaction):
        view = HelpView(self.bot, self.categories, self.cog_categories)
        
        
        embed = await view.create_category_embed(list(self.categories.keys())[0])
        view.current_category = list(self.categories.keys())[0]
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
