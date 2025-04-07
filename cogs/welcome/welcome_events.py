import discord
from discord.ext import commands
import json
import random
import asyncio
import os
from utils.colors import get_embed_color

class WelcomeEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/welcome/config.json"
        self.load_config()
        
    def load_config(self):
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}
            
    def get_guild_config(self, guild_id):
        
        guild_id = str(guild_id)
        if guild_id not in self.config:
            return None
        return self.config[guild_id]
        
    @commands.Cog.listener()
    async def on_member_join(self, member):
        
        guild_id = str(member.guild.id)
        guild_config = self.get_guild_config(guild_id)
        
        if not guild_config or not guild_config["enabled"]:
            return

        
        if guild_config["channel_id"]:
            channel = member.guild.get_channel(guild_config["channel_id"])
            if channel:
                message = guild_config["message"].format(
                    user=member.mention,
                    server=member.guild.name,
                    member_count=len(member.guild.members)
                )

                embed = discord.Embed(
                    title="👋 Bienvenue!",
                    description=message,
                    color=get_embed_color("welcome")
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
                embed.set_footer(text=f"ID: {member.id}")

                await channel.send(embed=embed)
        
        
        if guild_config["verification_enabled"] and guild_config["verification_channel_id"]:
            try:
                channel = member.guild.get_channel(guild_config["verification_channel_id"])
                if channel:
                    
                    question = random.choice(guild_config["verification_questions"])
                    verification_message = guild_config["verification_message"].format(question=question)
                    
                    
                    embed = discord.Embed(
                        title="🔒 Vérification requise",
                        description=f"{member.mention} {verification_message}",
                        color=get_embed_color("welcome")
                    )
                    embed.set_footer(text="Vous avez 5 minutes pour répondre")
                    
                    await channel.send(embed=embed)
                    
                    
                    
                    expected_answer = "Paris" if "capitale" in question else "4" if "2 + 2" in question else "bleu"
                    
                    
                    def check(m):
                        return m.author == member and m.channel == channel
                        
                    try:
                        msg = await self.bot.wait_for("message", check=check, timeout=300.0)
                        if msg.content.lower() == expected_answer.lower():
                            
                            success_embed = discord.Embed(
                                title="✅ Vérification réussie",
                                description=f"{member.mention} Vérification réussie ! Bienvenue sur le serveur !",
                                color=get_embed_color("success")
                            )
                            await channel.send(embed=success_embed)
                            
                            
                            if guild_config["auto_role_id"]:
                                try:
                                    role = member.guild.get_role(guild_config["auto_role_id"])
                                    if role:
                                        await member.add_roles(role)
                                except Exception as e:
                                    print(f"Erreur lors de l'attribution du rôle automatique : {e}")
                        else:
                            
                            error_embed = discord.Embed(
                                title="❌ Réponse incorrecte",
                                description=f"{member.mention} Réponse incorrecte. Veuillez réessayer.",
                                color=get_embed_color("error")
                            )
                            await channel.send(embed=error_embed)
                    except asyncio.TimeoutError:
                        
                        timeout_embed = discord.Embed(
                            title="⏱️ Temps écoulé",
                            description=f"{member.mention} Temps écoulé. Veuillez réessayer.",
                            color=get_embed_color("error")
                        )
                        await channel.send(embed=timeout_embed)
            except Exception as e:
                print(f"Erreur lors de la vérification : {e}")
                
async def setup(bot):
    await bot.add_cog(WelcomeEvents(bot)) 
