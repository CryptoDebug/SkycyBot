import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color
from utils.antispam import AntiSpamSystem
import asyncio
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

class AntiSpamConfigCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam = AntiSpamSystem(bot)
        self.config_file = "data/antispam_config.json"
        self.config = self.load_config()
        
        self.active_configurations = {}  

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
        
        self.antispam.config = self.config

    def has_permissions(self, interaction: discord.Interaction) -> bool:
        
        if interaction.user.id == interaction.guild.owner_id:
            return True
        return interaction.user.guild_permissions.administrator

    def is_configuration_active(self, guild_id: int) -> bool:
        
        return guild_id in self.active_configurations

    def get_active_configuration_user(self, guild_id: int) -> int:
        
        return self.active_configurations.get(guild_id)

    def start_configuration(self, guild_id: int, user_id: int):
        
        self.active_configurations[guild_id] = user_id

    def end_configuration(self, guild_id: int):
        
        if guild_id in self.active_configurations:
            del self.active_configurations[guild_id]

    @app_commands.command(name="antispam", description="Configure le système anti-spam")
    async def antispam(self, interaction: discord.Interaction):
        
        if not self.has_permissions(interaction):
            await interaction.response.send_message(
                "❌ Vous n'avez pas les permissions nécessaires pour utiliser cette commande. "
                "Seuls les administrateurs et le propriétaire du serveur peuvent l'utiliser.",
                ephemeral=True
            )
            return

        
        from cogs.administration.antilinks_config import AntiLinksConfigCommand
        antilinks_cog = self.bot.get_cog("AntiLinksConfigCommand")
        if antilinks_cog and antilinks_cog.is_configuration_active(interaction.guild_id):
            user_id = antilinks_cog.get_active_configuration_user(interaction.guild_id)
            user = await self.bot.fetch_user(user_id)
            username = user.name if user else "un utilisateur"
            await interaction.response.send_message(
                f"❌ Veuillez terminer la configuration d'anti-liens (fermer) avant de configurer l'anti-spam.\n"
                f"Configuration en cours par {username}.",
                ephemeral=True
            )
            return

        
        self.start_configuration(interaction.guild_id, interaction.user.id)

        guild_config = self.get_guild_config(interaction.guild_id)
        
        
        toggle_button = discord.ui.Button(
            label="ON" if not guild_config["enabled"] else "OFF",
            style=discord.ButtonStyle.green if not guild_config["enabled"] else discord.ButtonStyle.red,
            custom_id="toggle_antispam"
        )
        
        add_channel_button = discord.ui.Button(
            label="Ajouter un salon",
            style=discord.ButtonStyle.primary,
            custom_id="add_channel"
        )
        
        remove_channel_button = discord.ui.Button(
            label="Retirer un salon",
            style=discord.ButtonStyle.primary,
            custom_id="remove_channel"
        )
        
        settings_button = discord.ui.Button(
            label="Paramètres",
            style=discord.ButtonStyle.secondary,
            custom_id="settings"
        )
        
        close_button = discord.ui.Button(
            label="Fermer",
            style=discord.ButtonStyle.danger,
            custom_id="close"
        )
        
        
        view = discord.ui.View(timeout=300)  
        view.add_item(toggle_button)
        view.add_item(add_channel_button)
        view.add_item(remove_channel_button)
        view.add_item(settings_button)
        view.add_item(close_button)
        
        
        embed = discord.Embed(
            title="⚙️ Configuration du système anti-spam",
            description="Configurez la protection anti-spam de votre serveur.\n\n"
                       "**💡 Guide d'utilisation:**\n"
                       "• Activez/désactivez le système avec le bouton ON/OFF\n"
                       "• Ajoutez/retirez des salons à protéger\n"
                       "• Ajustez les paramètres de détection",
            color=get_embed_color("administration")
        )
        
        
        status = "✅ Activé" if guild_config["enabled"] else "❌ Désactivé"
        embed.add_field(
            name="🔌 État du système",
            value=f"**Statut:** {status}\n**ID du serveur:** `{interaction.guild_id}`",
            inline=False
        )
        
        
        channels_list = []
        for channel_id in guild_config["active_channels"]:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                channels_list.append(f"• {channel.mention}")
        
        channels_text = "\n".join(channels_list) if channels_list else "*Aucun salon protégé*"
        embed.add_field(
            name=f"📺 Salons protégés ({len(guild_config['active_channels'])})",
            value=channels_text,
            inline=False
        )
        
        
        settings = f"• Messages maximum: `{guild_config['max_messages']}`\n"
        settings += f"• Fenêtre de temps: `{guild_config['time_window']}` secondes\n"
        
        embed.add_field(
            name="⚙️ Configuration actuelle",
            value=settings,
            inline=False
        )
        
        
        embed.add_field(
            name="⏰ Dernière modification",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        
        embed.set_footer(
            text=f"ID du serveur: {interaction.guild_id}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        
        await interaction.response.send_message(embed=embed, view=view)
        
        
        try:
            
            timeout = 300
            start_time = datetime.now()
            
            while True:
                
                elapsed_time = (datetime.now() - start_time).total_seconds()
                if elapsed_time >= timeout:
                    
                    self.end_configuration(interaction.guild_id)
                    
                    
                    try:
                        
                        if interaction.message:
                            
                            await interaction.message.delete()
                        
                        
                        await interaction.channel.send("⏱️ La configuration a été fermée automatiquement après 5 minutes d'inactivité.")
                    except Exception as e:
                        print(f"Erreur lors de la fermeture automatique: {e}")
                    return
                
                
                remaining_time = timeout - elapsed_time
                if remaining_time <= 0:
                    remaining_time = 1  
                
                try:
                    button_interaction = await asyncio.wait_for(
                        self.bot.wait_for(
                            "interaction",
                            check=lambda i: isinstance(i, discord.Interaction) and i.type == discord.InteractionType.component and i.data.get("custom_id") in ["toggle_antispam", "add_channel", "remove_channel", "settings", "close"]
                        ),
                        timeout=remaining_time
                    )
                except asyncio.TimeoutError:
                    
                    continue
                
                
                start_time = datetime.now()
                
                if not self.has_permissions(button_interaction):
                    await button_interaction.response.send_message(
                        "❌ Vous n'avez pas les permissions nécessaires pour utiliser cette commande. "
                        "Seuls les administrateurs et le propriétaire du serveur peuvent l'utiliser.",
                        ephemeral=True
                    )
                    continue
                
                if button_interaction.data["custom_id"] == "close":
                    
                    self.end_configuration(button_interaction.guild_id)
                    
                    await button_interaction.message.delete()
                    return
                
                if button_interaction.data["custom_id"] == "toggle_antispam":
                    
                    guild_config["enabled"] = not guild_config["enabled"]
                    self.update_guild_config(button_interaction.guild_id, guild_config)
                    
                    
                    toggle_button.label = "ON" if not guild_config["enabled"] else "OFF"
                    toggle_button.style = discord.ButtonStyle.green if not guild_config["enabled"] else discord.ButtonStyle.red
                    
                    
                    status = "✅ Activé" if guild_config["enabled"] else "❌ Désactivé"
                    embed.set_field_at(0, name="🔌 État du système", value=f"**Statut:** {status}\n**ID du serveur:** `{button_interaction.guild_id}`")
                    
                    try:
                        await button_interaction.response.edit_message(embed=embed, view=view)
                    except discord.errors.InteractionResponded:
                        await button_interaction.message.edit(embed=embed, view=view)
                    
                elif button_interaction.data["custom_id"] == "add_channel":
                    try:
                        await button_interaction.response.send_message(
                            "🔍 Mentionnez le salon à ajouter ou envoyez son ID",
                            ephemeral=True
                        )
                    except discord.errors.InteractionResponded:
                        await button_interaction.followup.send(
                            "🔍 Mentionnez le salon à ajouter ou envoyez son ID",
                            ephemeral=True
                        )
                    
                    def check(m):
                        return m.author == button_interaction.user and m.channel == button_interaction.channel
                    
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=60)
                        channel = None
                        
                        
                        if msg.channel_mentions:
                            channel = msg.channel_mentions[0]
                        else:
                            
                            try:
                                channel_id = int(msg.content)
                                channel = button_interaction.guild.get_channel(channel_id)
                            except ValueError:
                                await msg.reply("❌ Format invalide. Mentionnez un salon ou envoyez son ID.")
                                continue
                        
                        if channel:
                            
                            active_channels = guild_config["active_channels"]
                            if str(channel.id) in active_channels:
                                await msg.reply("❌ Ce salon est déjà protégé par le système anti-spam.")
                            else:
                                active_channels.append(str(channel.id))
                                guild_config["active_channels"] = active_channels
                                self.update_guild_config(button_interaction.guild_id, guild_config)
                                
                                
                                channels_list = []
                                for channel_id in guild_config["active_channels"]:
                                    channel_obj = self.bot.get_channel(int(channel_id))
                                    if channel_obj:
                                        channels_list.append(f"• {channel_obj.mention}")
                                
                                channels_text = "\n".join(channels_list) if channels_list else "*Aucun salon protégé*"
                                embed.set_field_at(1, name=f"📺 Salons protégés ({len(guild_config['active_channels'])})", value=channels_text)
                                await button_interaction.message.edit(embed=embed, view=view)
                                await msg.reply(f"✅ Salon {channel.mention} ajouté avec succès!")
                        else:
                            await msg.reply("❌ Salon non trouvé.")
                            
                    except asyncio.TimeoutError:
                        await button_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                        
                elif button_interaction.data["custom_id"] == "remove_channel":
                    try:
                        await button_interaction.response.send_message(
                            "🔍 Mentionnez le salon à retirer ou envoyez son ID",
                            ephemeral=True
                        )
                    except discord.errors.InteractionResponded:
                        await button_interaction.followup.send(
                            "🔍 Mentionnez le salon à retirer ou envoyez son ID",
                            ephemeral=True
                        )
                    
                    def check(m):
                        return m.author == button_interaction.user and m.channel == button_interaction.channel
                    
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=60)
                        channel = None
                        
                        
                        if msg.channel_mentions:
                            channel = msg.channel_mentions[0]
                        else:
                            
                            try:
                                channel_id = int(msg.content)
                                channel = button_interaction.guild.get_channel(channel_id)
                            except ValueError:
                                await msg.reply("❌ Format invalide. Mentionnez un salon ou envoyez son ID.")
                                continue
                        
                        if channel:
                            if str(channel.id) in guild_config["active_channels"]:
                                guild_config["active_channels"].remove(str(channel.id))
                                self.update_guild_config(button_interaction.guild_id, guild_config)
                                
                                
                                channels_list = []
                                for channel_id in guild_config["active_channels"]:
                                    channel = self.bot.get_channel(int(channel_id))
                                    if channel:
                                        channels_list.append(f"• {channel.mention}")
                                
                                channels_text = "\n".join(channels_list) if channels_list else "*Aucun salon protégé*"
                                embed.set_field_at(1, name=f"📺 Salons protégés ({len(guild_config['active_channels'])})", value=channels_text)
                                await button_interaction.message.edit(embed=embed, view=view)
                                await msg.reply(f"✅ Salon {channel.mention} retiré avec succès!")
                            else:
                                await msg.reply("❌ Ce salon n'est pas protégé.")
                        else:
                            await msg.reply("❌ Salon non trouvé.")
                            
                    except asyncio.TimeoutError:
                        await button_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                    
        except Exception as e:
            
            self.end_configuration(interaction.guild_id)
            print(f"Erreur dans la commande antispam: {e}")

async def setup(bot):
    await bot.add_cog(AntiSpamConfigCommand(bot)) 
