import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os
from utils.colors import get_embed_color

class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scores_file = "data/games/scores.json"
        self.load_scores()
        self.active_games = {}
        
    def load_scores(self):
        
        try:
            with open(self.scores_file, "r", encoding="utf-8") as f:
                self.scores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.scores = {}
            
    def save_scores(self):
        
        os.makedirs(os.path.dirname(self.scores_file), exist_ok=True)
        with open(self.scores_file, "w", encoding="utf-8") as f:
            json.dump(self.scores, f, indent=4)
            
    def get_player_score(self, guild_id, player_id):
        
        guild_id = str(guild_id)
        player_id = str(player_id)
        
        if guild_id not in self.scores:
            self.scores[guild_id] = {}
        if player_id not in self.scores[guild_id]:
            self.scores[guild_id][player_id] = 0
            
        return self.scores[guild_id][player_id]
        
    def add_points(self, guild_id, player_id, points):
        
        guild_id = str(guild_id)
        player_id = str(player_id)
        
        if guild_id not in self.scores:
            self.scores[guild_id] = {}
        if player_id not in self.scores[guild_id]:
            self.scores[guild_id][player_id] = 0
            
        self.scores[guild_id][player_id] += points
        self.save_scores()
        
    @app_commands.command(name="hangman", description="Jouer au pendu")
    async def hangman(self, interaction: discord.Interaction):
        
        channel_id = str(interaction.channel_id)
        if channel_id in self.active_games:
            await interaction.response.send_message("❌ Une partie est déjà en cours dans ce canal !", ephemeral=True)
            return
            
        
        words = ["python", "discord", "bot", "programmation", "jeu", "pendu", "skycy", "discord.py", "développeur", "code", "script", "fonction", "variable", "classe", "méthode", "objet", "interface", "api", "web", "internet", "serveur", "client", "base de données", "sql", "nosql", "json", "xml", "html", "css", "javascript", "typescript", "react", "vue", "angular", "node", "express", "django", "flask", "fastapi", "spring", "laravel", "symfony", "wordpress", "drupal", "joomla", "magento", "shopify", "woocommerce", "prestashop", "opencart", "oscommerce", "zen cart", "virtuemart", "x-cart", "abantecart", "loaded", "loaded commerce", "loaded 7", "loaded 8", "loaded 9", "loaded 10", "loaded 11", "loaded 12", "loaded 13", "loaded 14", "loaded 15", "loaded 16", "loaded 17", "loaded 18", "loaded 19", "loaded 20"]
        word = random.choice(words)
        
        
        self.active_games[channel_id] = {
            "word": word,
            "hidden_word": ["\_"] * len(word),
            "used_letters": [],
            "errors": 0,
            "player": interaction.user.id,
            "start_time": interaction.created_at.timestamp()
        }
        
        
        embed = discord.Embed(
            title="🎮 Jeu du Pendu",
            description=f"Bienvenue dans le jeu du pendu, {interaction.user.mention} !\nDevinez le mot lettre par lettre.",
            color=get_embed_color("games")
        )
        
        
        embed.add_field(
            name="Mot à deviner",
            value=" ".join(self.active_games[channel_id]["hidden_word"]),
            inline=False
        )
        
        
        embed.add_field(
            name="Lettres utilisées",
            value="Aucune",
            inline=False
        )
        
        
        embed.add_field(
            name="Erreurs",
            value="0/6",
            inline=True
        )
        
        
        hangman_stage = "```\n   +---+\n       |\n       |\n       |\n      ===```"
        embed.add_field(
            name="Pendu",
            value=hangman_stage,
            inline=False
        )
        
        
        embed.add_field(
            name="Comment jouer",
            value="Envoyez une lettre dans le chat pour deviner le mot. Vous avez 6 erreurs maximum.",
            inline=False
        )
        
        
        embed.set_footer(text=f"Partie démarrée par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
        
    @commands.Cog.listener()
    async def on_message(self, message):
        
        if message.author.bot:
            return
            
        channel_id = str(message.channel.id)
        if channel_id not in self.active_games:
            return
            
        game = self.active_games[channel_id]
        
        
        if message.author.id != game["player"]:
            return
            
        
        if not message.content.isalpha() or len(message.content) != 1:
            return
            
        
        if message.content.lower() in game["used_letters"]:
            await message.channel.send("❌ Cette lettre a déjà été utilisée !")
            return
            
        
        game["used_letters"].append(message.content.lower())
        
        
        if message.content.lower() in game["word"]:
            
            for i, letter in enumerate(game["word"]):
                if letter == message.content.lower():
                    game["hidden_word"][i] = letter
                    
            
            if "\_" not in game["hidden_word"]:
                
                time_spent = int(message.created_at.timestamp() - game["start_time"])
                minutes = time_spent // 60
                seconds = time_spent % 60
                
                
                victory_embed = discord.Embed(
                    title="🎉 Victoire !",
                    description=f"Félicitations {message.author.mention} ! Vous avez trouvé le mot !",
                    color=get_embed_color("games")
                )
                
                
                victory_embed.add_field(
                    name="Le mot était",
                    value=game["word"],
                    inline=False
                )
                
                
                victory_embed.add_field(
                    name="Temps de jeu",
                    value=f"{minutes} minute{'s' if minutes != 1 else ''} et {seconds} seconde{'s' if seconds != 1 else ''}",
                    inline=True
                )
                
                victory_embed.add_field(
                    name="Erreurs",
                    value=f"{game['errors']}/6",
                    inline=True
                )
                
                
                points = 10 - game["errors"]
                victory_embed.add_field(
                    name="Points gagnés",
                    value=f"+{points} points",
                    inline=True
                )
                
                
                victory_embed.set_footer(text=f"Partie terminée par {message.author.name}", icon_url=message.author.display_avatar.url)
                
                await message.channel.send(embed=victory_embed)
                self.add_points(message.guild.id, message.author.id, points)
                del self.active_games[channel_id]
                return
        else:
            
            game["errors"] += 1
            
            
            if game["errors"] >= 6:
                
                defeat_embed = discord.Embed(
                    title="💀 Game Over !",
                    description=f"Dommage {message.author.mention}, vous avez perdu !",
                    color=get_embed_color("games")
                )
                
                
                defeat_embed.add_field(
                    name="Le mot était",
                    value=game["word"],
                    inline=False
                )
                
                
                defeat_embed.add_field(
                    name="Lettres utilisées",
                    value=", ".join(sorted(game["used_letters"])),
                    inline=False
                )
                
                
                defeat_embed.set_footer(text=f"Partie terminée par {message.author.name}", icon_url=message.author.display_avatar.url)
                
                await message.channel.send(embed=defeat_embed)
                del self.active_games[channel_id]
                return
                
        
        await self.display_game(message.channel, game)
        
    async def display_game(self, channel, game):
        
        
        embed = discord.Embed(
            title="🎮 Jeu du Pendu",
            color=get_embed_color("games")
        )
        
        
        embed.add_field(
            name="Mot à deviner",
            value=" ".join(game["hidden_word"]),
            inline=False
        )
        
        
        embed.add_field(
            name="Lettres utilisées",
            value=", ".join(sorted(game["used_letters"])) or "Aucune",
            inline=False
        )
        
        
        embed.add_field(
            name="Erreurs",
            value=f"{game['errors']}/6",
            inline=True
        )
        
        
        hangman_stages = [
            "```\n   +---+\n       |\n       |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n       |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n   |   |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n  /|   |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n  /|\\  |\n       |\n      ===```",
            "```\n   +---+\n   O   |\n  /|\\  |\n  /    |\n      ===```",
            "```\n   +---+\n   O   |\n  /|\\  |\n  / \\  |\n      ===```"
        ]
        embed.add_field(
            name="Pendu",
            value=hangman_stages[game["errors"]],
            inline=False
        )
        
        
        embed.set_footer(text="Envoyez une lettre pour continuer à jouer")
        
        await channel.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(Hangman(bot)) 
