import discord
import json
import os
from datetime import datetime
from utils.colors import get_embed_color
from discord.ext import tasks

class LogsSystem:
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/logs_config.json"
        self._ensure_config_file()

    def _ensure_config_file(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.config_file):
            with open(self.config_file, "w") as f:
                json.dump({"guilds": {}}, f, indent=4)

    def _load_config(self):
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"guilds": {}}

    def _save_config(self, config):
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=4)

    def get_guild_config(self, guild_id):
        guild_id = str(guild_id)
        config = self._load_config()
        if guild_id not in config["guilds"]:
            config["guilds"][guild_id] = {
                "enabled": False,
                "channels": {
                    "messages": None,
                    "moderation": None,
                    "administration": None
                },
                "filters": {
                    "ignored_channels": [],
                    "ignored_users": [],
                    "ignored_roles": []
                }
            }
            self._save_config(config)
        else:
            
            guild_config = config["guilds"][guild_id]
            
            
            new_channels = {
                "messages": None,
                "moderation": None,
                "administration": None
            }
            for channel_type, channel_id in new_channels.items():
                if channel_type not in guild_config["channels"]:
                    guild_config["channels"][channel_type] = channel_id

            
            if "filters" not in guild_config:
                guild_config["filters"] = {
                    "ignored_channels": [],
                    "ignored_users": [],
                    "ignored_roles": []
                }
            else:
                
                required_filters = ["ignored_channels", "ignored_users", "ignored_roles"]
                for filter_type in required_filters:
                    if filter_type not in guild_config["filters"]:
                        guild_config["filters"][filter_type] = []

            self._save_config(config)
        return config["guilds"][guild_id]

    def update_guild_config(self, guild_id, new_config):
        guild_id = str(guild_id)
        config = self._load_config()
        config["guilds"][guild_id] = new_config
        self._save_config(config)

    async def log_event(self, guild_id: int, event_type: str, embed: discord.Embed):
        
        guild_config = self.get_guild_config(guild_id)
        if not guild_config["enabled"]:
            return

        
        if "filters" in guild_config:
            filters = guild_config["filters"]
            
            
            if "ignored_channels" in filters:
                
                channel_id = None
                for field in embed.fields:
                    if field.name == "Salon":
                        try:
                            
                            channel_id = int(field.value.split("<
                            break
                        except:
                            continue
                
                if channel_id and channel_id in filters["ignored_channels"]:
                    return

            
            if "ignored_users" in filters:
                
                user_id = None
                for field in embed.fields:
                    if field.name == "Utilisateur":
                        try:
                            
                            user_id = int(field.value.split("<@")[1].split(">")[0])
                            break
                        except:
                            continue
                
                if user_id and user_id in filters["ignored_users"]:
                    return

            
            if "ignored_roles" in filters:
                
                role_id = None
                for field in embed.fields:
                    if field.name == "Rôle":
                        try:
                            
                            role_id = int(field.value.split("<@&")[1].split(">")[0])
                            break
                        except:
                            continue
                
                if role_id and role_id in filters["ignored_roles"]:
                    return

        
        channel_id = None
        if event_type.startswith("message"):
            channel_id = guild_config["channels"]["messages"]
        elif event_type.startswith("moderation"):
            channel_id = guild_config["channels"]["moderation"]
        elif event_type.startswith("administration"):
            channel_id = guild_config["channels"]["administration"]

        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    
    async def log_message_delete(self, message):
        guild_config = self.get_guild_config(message.guild.id)
        if not guild_config["enabled"] or not guild_config["channels"]["messages"]:
            return

        embed = discord.Embed(
            title="🗑️ Message supprimé",
            color=get_embed_color("logs")
        )
        embed.add_field(name="Auteur", value=message.author.mention, inline=True)
        embed.add_field(name="Salon", value=message.channel.mention, inline=True)
        embed.add_field(name="Contenu", value=message.content or "Aucun contenu", inline=False)
        embed.set_footer(text=f"ID: {message.id}")

        await self.log_event(message.guild.id, "messages", embed)

    async def log_message_edit(self, before, after):
        if before.content == after.content:
            return

        guild_config = self.get_guild_config(before.guild.id)
        if not guild_config["enabled"] or not guild_config["channels"]["messages"]:
            return

        embed = discord.Embed(
            title="✏️ Message modifié",
            color=get_embed_color("logs")
        )
        embed.add_field(name="Auteur", value=before.author.mention, inline=True)
        embed.add_field(name="Salon", value=before.channel.mention, inline=True)
        embed.add_field(name="Avant", value=before.content or "Aucun contenu", inline=False)
        embed.add_field(name="Après", value=after.content or "Aucun contenu", inline=False)
        embed.set_footer(text=f"ID: {before.id}")

        await self.log_event(before.guild.id, "messages", embed)

    async def log_member_ban(self, guild, user, moderator, reason):
        guild_config = self.get_guild_config(guild.id)
        if not guild_config["enabled"] or not guild_config["channels"]["moderation"]:
            return

        channel = guild.get_channel(guild_config["channels"]["moderation"])
        if not channel:
            return

        embed = discord.Embed(
            title="🔨 Membre banni",
            color=get_embed_color("logs")
        )
        embed.add_field(name="Utilisateur", value=user.mention, inline=True)
        embed.add_field(name="Modérateur", value=moderator.mention, inline=True)
        embed.add_field(name="Raison", value=reason or "Aucune raison", inline=False)
        embed.set_footer(text=f"ID: {user.id}")

        await channel.send(embed=embed)

    async def log_member_unban(self, guild, user, moderator):
        guild_config = self.get_guild_config(guild.id)
        if not guild_config["enabled"] or not guild_config["channels"]["moderation"]:
            return

        channel = guild.get_channel(guild_config["channels"]["moderation"])
        if not channel:
            return

        embed = discord.Embed(
            title="🔓 Membre débanni",
            color=get_embed_color("logs")
        )
        embed.add_field(name="Utilisateur", value=user.mention, inline=True)
        embed.add_field(name="Modérateur", value=moderator.mention, inline=True)
        embed.set_footer(text=f"ID: {user.id}")

        await channel.send(embed=embed)

    async def log_member_kick(self, guild, user, moderator, reason):
        guild_config = self.get_guild_config(guild.id)
        if not guild_config["enabled"] or not guild_config["channels"]["moderation"]:
            return

        channel = guild.get_channel(guild_config["channels"]["moderation"])
        if not channel:
            return

        embed = discord.Embed(
            title="👢 Membre expulsé",
            color=get_embed_color("logs")
        )
        embed.add_field(name="Utilisateur", value=user.mention, inline=True)
        embed.add_field(name="Modérateur", value=moderator.mention, inline=True)
        embed.add_field(name="Raison", value=reason or "Aucune raison", inline=False)
        embed.set_footer(text=f"ID: {user.id}")

        await channel.send(embed=embed)
