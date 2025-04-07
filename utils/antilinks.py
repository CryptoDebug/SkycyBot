import discord
import json
import os
import re
from typing import Dict, List

class AntiLinksSystem:
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/antilinks_config.json"
        self.url_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~
        self.config = self.load_config()

    def load_config(self) -> Dict:
        
        try:
            
            if not os.path.exists("data"):
                os.makedirs("data")
            
            
            if not os.path.exists(self.config_file):
                default_config = {}
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
            
            
            with open(self.config_file, "r", encoding="utf-8") as f:
                content = f.read()
                if not content:  
                    default_config = {}
                    with open(self.config_file, "w", encoding="utf-8") as f:
                        json.dump(default_config, f, indent=4)
                    return default_config
                return json.loads(content)
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            
            default_config = {}
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            return default_config

    def save_config(self):
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")

    def get_guild_config(self, guild_id: int) -> Dict:
        
        guild_id_str = str(guild_id)
        if guild_id_str not in self.config:
            self.config[guild_id_str] = {
                "enabled": False,
                "active_channels": [],
                "whitelisted_roles": [],
                "whitelisted_users": []
            }
            self.save_config()
        return self.config[guild_id_str]

    def update_guild_config(self, guild_id: int, config: Dict):
        
        self.config[str(guild_id)] = config
        self.save_config()

    def contains_url(self, message: str) -> bool:
        
        return bool(self.url_pattern.search(message))

    def is_whitelisted(self, message: discord.Message) -> bool:
        
        guild_config = self.get_guild_config(message.guild.id)
        
        
        for role_id in guild_config["whitelisted_roles"]:
            if any(role.id == int(role_id) for role in message.author.roles):
                return True
                
        
        return str(message.author.id) in guild_config["whitelisted_users"]

    async def check_links(self, message: discord.Message) -> bool:
        
        
        self.config = self.load_config()
        
        guild_config = self.get_guild_config(message.guild.id)
        
        
        if not guild_config["enabled"]:
            return False
            
        
        if str(message.channel.id) not in guild_config["active_channels"]:
            return False
            
        
        if self.is_whitelisted(message):
            return False
            
        
        return self.contains_url(message.content) 
