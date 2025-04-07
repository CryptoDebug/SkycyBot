import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
import random
from utils.colors import get_embed_color

class TicTacToe(commands.Cog):
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
        
    def create_board(self):
        
        return [["⬜" for _ in range(3)] for _ in range(3)]
        
    def format_board(self, board):
        
        return "\n".join(" ".join(row) for row in board)
        
    def check_win(self, board, player):
        
        
        for row in board:
            if all(cell == player for cell in row):
                return True
                
        
        for col in range(3):
            if all(board[row][col] == player for row in range(3)):
                return True
                
        
        if all(board[i][i] == player for i in range(3)):
            return True
        if all(board[i][2-i] == player for i in range(3)):
            return True
            
        return False
        
    def check_draw(self, board):
        
        return all(cell != "⬜" for row in board for cell in row)
        
    @app_commands.command(name="tictactoe", description="Jouer au morpion")
    async def tictactoe(self, interaction: discord.Interaction, adversaire: discord.Member = None):
        
        
        if adversaire is None:
            adversaire = self.bot.user
            is_bot_game = True
        else:
            is_bot_game = False
            
        if interaction.user == adversaire:
            await interaction.response.send_message("❌ Vous ne pouvez pas jouer contre vous-même !", ephemeral=True)
            return
            
        
        for game in self.active_games.values():
            if interaction.user.id in [game["player1"], game["player2"]] or adversaire.id in [game["player1"], game["player2"]]:
                await interaction.response.send_message("❌ Un des joueurs est déjà dans une partie !", ephemeral=True)
                return
                
        
        board = [["⬜" for _ in range(3)] for _ in range(3)]
        
        
        game_id = str(interaction.channel_id)
        self.active_games[game_id] = {
            "player1": interaction.user.id,
            "player2": adversaire.id,
            "current_player": interaction.user.id,
            "board": board,
            "message": None,
            "is_bot_game": is_bot_game,
            "guild_id": interaction.guild_id
        }
        
        
        embed = discord.Embed(
            title="⭕ Morpion",
            description=f"{interaction.user.mention} vs {adversaire.mention}\n\nC'est au tour de {interaction.user.mention} de jouer !",
            color=get_embed_color("games")
        )
        
        
        board_text = ""
        for row in board:
            board_text += "".join(row) + "\n"
            
        embed.add_field(name="Plateau", value=board_text, inline=False)
        
        
        embed.add_field(
            name="Comment jouer",
            value="Utilisez les boutons ci-dessous pour placer votre symbole (X ou O).",
            inline=False
        )
        
        
        embed.set_footer(text=f"Partie démarrée par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        
        view = TicTacToeView(self, game_id)
        
        
        await interaction.response.send_message(embed=embed, view=view)
        
        message = await interaction.original_response()
        self.active_games[game_id]["message"] = message
        
        
        
        
    async def bot_play(self, game_id):
        
        game = self.active_games[game_id]
        board = game["board"]
        
        
        await asyncio.sleep(1)
        
        
        if game_id not in self.active_games:
            return
            
        
        valid_moves = []
        for i in range(3):
            for j in range(3):
                if board[i][j] == "⬜":
                    valid_moves.append((i, j))
                    
        if not valid_moves:
            return
            
        
        
        for i, j in valid_moves:
            board[i][j] = "⭕"
            if self.check_win(board, "⭕"):
                
                await self.update_game(game_id, i, j)
                return
            board[i][j] = "⬜"
            
        
        for i, j in valid_moves:
            board[i][j] = "❌"
            if self.check_win(board, "❌"):
                
                board[i][j] = "⭕"
                await self.update_game(game_id, i, j)
                return
            board[i][j] = "⬜"
            
        
        if board[1][1] == "⬜":
            await self.update_game(game_id, 1, 1)
            return
            
        
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for i, j in corners:
            if board[i][j] == "⬜":
                await self.update_game(game_id, i, j)
                return
                
        
        i, j = valid_moves[0]
        await self.update_game(game_id, i, j)
        
    async def update_game(self, game_id, row, col):
        
        game = self.active_games[game_id]
        board = game["board"]
        
        
        symbol = "❌" if game["current_player"] == game["player1"] else "⭕"
        board[row][col] = symbol
        
        
        if self.check_win(board, symbol):
            
            winner_id = game["current_player"]
            winner = self.bot.get_user(winner_id)
            
            
            embed = discord.Embed(
                title="⭕ Morpion - Fin de partie",
                description=f"🎉 {winner.mention} a gagné la partie !",
                color=get_embed_color("games")
            )
            
            
            board_text = ""
            for row in board:
                board_text += "".join(row) + "\n"
                
            embed.add_field(name="Plateau final", value=board_text, inline=False)
            
            
            embed.set_footer(text=f"Partie terminée", icon_url=winner.display_avatar.url)
            
            
            await game["message"].edit(embed=embed, view=None)
            
            
            self.add_points(game["guild_id"], winner_id, 10)
            
            
            del self.active_games[game_id]
            return
            
        
        if self.check_draw(board):
            
            embed = discord.Embed(
                title="⭕ Morpion - Fin de partie",
                description="🤝 Match nul !",
                color=get_embed_color("games")
            )
            
            
            board_text = ""
            for row in board:
                board_text += "".join(row) + "\n"
                
            embed.add_field(name="Plateau final", value=board_text, inline=False)
            
            
            embed.set_footer(text=f"Partie terminée")
            
            
            await game["message"].edit(embed=embed, view=None)
            
            
            del self.active_games[game_id]
            return
            
        
        game["current_player"] = game["player2"] if game["current_player"] == game["player1"] else game["player1"]
        
        
        current_player = self.bot.get_user(game["current_player"])
        embed = discord.Embed(
            title="⭕ Morpion",
            description=f"C'est au tour de {current_player.mention} de jouer !",
            color=get_embed_color("games")
        )
        
        
        board_text = ""
        for row in board:
            board_text += "".join(row) + "\n"
            
        embed.add_field(name="Plateau", value=board_text, inline=False)
        
        
        embed.add_field(
            name="Comment jouer",
            value="Utilisez les boutons ci-dessous pour placer votre symbole (X ou O).",
            inline=False
        )
        
        
        embed.set_footer(text=f"Partie en cours", icon_url=current_player.display_avatar.url)
        
        
        await game["message"].edit(embed=embed)
        
        
        if game["is_bot_game"] and game["current_player"] == game["player2"]:
            await self.bot_play(game_id)
            
class TicTacToeView(discord.ui.View):
    def __init__(self, cog, game_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.game_id = game_id
        
        
        for i in range(3):
            for j in range(3):
                button = discord.ui.Button(
                    label="⬜",
                    custom_id=f"tictactoe_{i}_{j}",
                    style=discord.ButtonStyle.secondary,
                    row=i
                )
                button.callback = self.button_callback
                self.add_item(button)
                
    async def button_callback(self, interaction: discord.Interaction):
        
        custom_id = interaction.data["custom_id"]
        _, row, col = custom_id.split("_")
        row, col = int(row), int(col)
        
        
        game = self.cog.active_games.get(self.game_id)
        if not game:
            await interaction.response.send_message("❌ Cette partie n'existe plus !", ephemeral=True)
            return
            
        
        if interaction.user.id != game["current_player"]:
            await interaction.response.send_message("❌ Ce n'est pas votre tour !", ephemeral=True)
            return
            
        
        if game["board"][row][col] != "⬜":
            await interaction.response.send_message("❌ Cette case est déjà prise !", ephemeral=True)
            return
            
        
        await interaction.response.defer()
        
        
        await self.cog.update_game(self.game_id, row, col)

async def setup(bot):
    await bot.add_cog(TicTacToe(bot)) 
