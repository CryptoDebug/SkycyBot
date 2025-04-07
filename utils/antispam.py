import discord
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List

class AntiSpamSystem:
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/antispam_config.json"
        self.config = self.load_config()
        self.message_history = {}  

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
                "max_messages": 5,
                "time_window": 5  
            }
            self.save_config()
        return self.config[guild_id_str]

    def update_guild_config(self, guild_id: int, config: Dict):
        
        self.config[str(guild_id)] = config
        self.save_config()

    async def is_spam(self, message: discord.Message) -> bool:
        
        
        self.config = self.load_config()
        
        guild_config = self.get_guild_config(message.guild.id)
        
        
        if not guild_config["enabled"]:
            return False
            
        
        if str(message.channel.id) not in guild_config["active_channels"]:
            return False
            
        
        if message.guild.id not in self.message_history:
            self.message_history[message.guild.id] = {}
        if message.channel.id not in self.message_history[message.guild.id]:
            self.message_history[message.guild.id][message.channel.id] = {}
        if message.author.id not in self.message_history[message.guild.id][message.channel.id]:
            self.message_history[message.guild.id][message.channel.id][message.author.id] = []
            
        
        current_time = datetime.utcnow()
        self.message_history[message.guild.id][message.channel.id][message.author.id].append(current_time)
        
        
        time_window = timedelta(seconds=guild_config["time_window"])
        self.message_history[message.guild.id][message.channel.id][message.author.id] = [
            t for t in self.message_history[message.guild.id][message.channel.id][message.author.id]
            if current_time - t <= time_window
        ]
        
        
        return len(self.message_history[message.guild.id][message.channel.id][message.author.id]) > guild_config["max_messages"] 
