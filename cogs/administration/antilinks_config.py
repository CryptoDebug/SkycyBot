import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color
from utils.antilinks import AntiLinksSystem
import asyncio
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

def admin_or_owner():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or interaction.user.id == interaction.guild.owner_id:
            return True
        await interaction.response.send_message(
            "❌ Cette commande est réservée aux administrateurs et au propriétaire du serveur.",
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

class AntiLinksConfigCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antilinks = AntiLinksSystem(bot)
        self.config_file = "data/antilinks_config.json"
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
                "whitelisted_roles": [],
                "whitelisted_users": []
            }
            self.save_config()
        return self.config[guild_id_str]

    def update_guild_config(self, guild_id: int, config: Dict):
        
        self.config[str(guild_id)] = config
        self.save_config()
        self.antilinks.config = self.config

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

    @app_commands.command(name="antilinks", description="Configure le système anti-liens")
    async def antilinks(self, interaction: discord.Interaction):
        
        if not self.has_permissions(interaction):
            await interaction.response.send_message(
                "❌ Vous n'avez pas les permissions nécessaires pour utiliser cette commande. "
                "Seuls les administrateurs et le propriétaire du serveur peuvent l'utiliser.",
                ephemeral=True
            )
            return

        
        from cogs.administration.antispam_config import AntiSpamConfigCommand
        antispam_cog = self.bot.get_cog("AntiSpamConfigCommand")
        if antispam_cog and antispam_cog.is_configuration_active(interaction.guild_id):
            user_id = antispam_cog.get_active_configuration_user(interaction.guild_id)
            user = await self.bot.fetch_user(user_id)
            username = user.name if user else "un utilisateur"
            await interaction.response.send_message(
                f"❌ Veuillez terminer la configuration d'anti-spam (fermer) avant de configurer l'anti-liens.\n"
                f"Configuration en cours par {username}.",
                ephemeral=True
            )
            return

        
        self.start_configuration(interaction.guild_id, interaction.user.id)

        guild_config = self.get_guild_config(interaction.guild_id)
        
        
        toggle_button = discord.ui.Button(
            label="ON" if not guild_config["enabled"] else "OFF",
            style=discord.ButtonStyle.green if not guild_config["enabled"] else discord.ButtonStyle.red,
            custom_id="toggle_antilinks"
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
        
        whitelist_button = discord.ui.Button(
            label="Whitelist",
            style=discord.ButtonStyle.secondary,
            custom_id="whitelist"
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
        view.add_item(whitelist_button)
        view.add_item(close_button)
        
        
        embed = discord.Embed(
            title="⚙️ Configuration du système anti-liens",
            description="Configurez la protection contre les liens indésirables.\n\n"
                       "**💡 Guide d'utilisation:**\n"
                       "• Activez/désactivez le système avec le bouton ON/OFF\n"
                       "• Ajoutez/retirez des salons à protéger\n"
                       "• Gérez la whitelist des rôles et utilisateurs\n"
                       "• Cliquez sur 'Fermer' pour terminer la configuration",
            color=get_embed_color("administration")
        )
        
        
        status = "🟢 Activé" if guild_config["enabled"] else "🔴 Désactivé"
        embed.add_field(
            name="🔌 État du système",
            value=f"**Statut:** {status}\n"
                  f"**ID du serveur:** `{interaction.guild_id}`",
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
        
        
        whitelisted_roles = []
        for role_id in guild_config["whitelisted_roles"]:
            role = interaction.guild.get_role(int(role_id))
            if role:
                whitelisted_roles.append(f"• {role.mention}")
        
        roles_text = "\n".join(whitelisted_roles) if whitelisted_roles else "*Aucun rôle whitelisté*"
        embed.add_field(
            name=f"👥 Rôles whitelistés ({len(guild_config['whitelisted_roles'])})",
            value=roles_text,
            inline=False
        )
        
        
        whitelisted_users = []
        for user_id in guild_config["whitelisted_users"]:
            user = await self.bot.fetch_user(int(user_id))
            if user:
                whitelisted_users.append(f"• {user.mention}")
        
        users_text = "\n".join(whitelisted_users) if whitelisted_users else "*Aucun utilisateur whitelisté*"
        embed.add_field(
            name=f"👤 Utilisateurs whitelistés ({len(guild_config['whitelisted_users'])})",
            value=users_text,
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
                            check=lambda i: isinstance(i, discord.Interaction) and i.type == discord.InteractionType.component and i.data.get("custom_id") in ["toggle_antilinks", "add_channel", "remove_channel", "whitelist", "close"]
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
                
                if button_interaction.data["custom_id"] == "toggle_antilinks":
                    
                    guild_config["enabled"] = not guild_config["enabled"]
                    self.update_guild_config(button_interaction.guild_id, guild_config)
                    
                    
                    toggle_button.label = "ON" if not guild_config["enabled"] else "OFF"
                    toggle_button.style = discord.ButtonStyle.green if not guild_config["enabled"] else discord.ButtonStyle.red
                    
                    
                    status = "✅ Activé" if guild_config["enabled"] else "❌ Désactivé"
                    embed.set_field_at(0, name="🔌 État du système", value=f"**Statut:** {status}\n**ID du serveur:** `{button_interaction.guild_id}`")
                    
                    await button_interaction.response.edit_message(embed=embed, view=view)
                    
                elif button_interaction.data["custom_id"] == "add_channel":
                    await button_interaction.response.send_message(
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
                                channel = interaction.guild.get_channel(channel_id)
                            except ValueError:
                                await msg.reply("❌ Format invalide. Mentionnez un salon ou envoyez son ID.")
                                continue
                        
                        if channel:
                            
                            if str(channel.id) in guild_config["active_channels"]:
                                await msg.reply("❌ Ce salon est déjà protégé.")
                            else:
                                guild_config["active_channels"].append(str(channel.id))
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
                    await button_interaction.response.send_message(
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
                                channel = interaction.guild.get_channel(channel_id)
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
                        
                elif button_interaction.data["custom_id"] == "whitelist":
                    
                    whitelist_view = discord.ui.View()
                    
                    add_role_button = discord.ui.Button(
                        label="Ajouter un rôle",
                        style=discord.ButtonStyle.primary,
                        custom_id="add_role"
                    )
                    
                    remove_role_button = discord.ui.Button(
                        label="Retirer un rôle",
                        style=discord.ButtonStyle.danger,
                        custom_id="remove_role"
                    )
                    
                    add_user_button = discord.ui.Button(
                        label="Ajouter un utilisateur",
                        style=discord.ButtonStyle.primary,
                        custom_id="add_user"
                    )
                    
                    remove_user_button = discord.ui.Button(
                        label="Retirer un utilisateur",
                        style=discord.ButtonStyle.danger,
                        custom_id="remove_user"
                    )
                    
                    whitelist_view.add_item(add_role_button)
                    whitelist_view.add_item(remove_role_button)
                    whitelist_view.add_item(add_user_button)
                    whitelist_view.add_item(remove_user_button)
                    
                    await button_interaction.response.send_message(
                        "⚙️ Gestion de la whitelist\n\n"
                        "Utilisez les boutons ci-dessous pour gérer la whitelist.\n"
                        "Vous pouvez mentionner les rôles/utilisateurs, donner leur nom ou leur ID.",
                        view=whitelist_view,
                        ephemeral=True
                    )
                    
                    try:
                        while True:
                            whitelist_interaction = await self.bot.wait_for(
                                "interaction",
                                check=lambda i: isinstance(i, discord.Interaction) and 
                                             i.type == discord.InteractionType.component and 
                                             i.data.get("custom_id") in ["add_role", "remove_role", "add_user", "remove_user"]
                            )
                            
                            if not whitelist_interaction.user.guild_permissions.administrator and whitelist_interaction.user.id != whitelist_interaction.guild.owner_id:
                                await whitelist_interaction.response.send_message(
                                    "❌ Cette commande est réservée aux administrateurs et au propriétaire du serveur.",
                                    ephemeral=True
                                )
                                continue
                            
                            if whitelist_interaction.data["custom_id"] == "add_role":
                                await whitelist_interaction.response.send_message(
                                    "🔍 Mentionnez le rôle à ajouter, donnez son nom ou son ID",
                                    ephemeral=True
                                )
                                
                                def check(m):
                                    return m.author == whitelist_interaction.user and m.channel == whitelist_interaction.channel
                                
                                try:
                                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                                    role = None
                                    
                                    
                                    if msg.role_mentions:
                                        role = msg.role_mentions[0]
                                    else:
                                        
                                        role = discord.utils.get(whitelist_interaction.guild.roles, name=msg.content)
                                        if not role:
                                            
                                            try:
                                                role_id = int(msg.content)
                                                role = whitelist_interaction.guild.get_role(role_id)
                                            except ValueError:
                                                await msg.reply("❌ Format invalide. Mentionnez un rôle, donnez son nom ou son ID.")
                                                continue
                                    
                                    if role:
                                        if str(role.id) not in guild_config["whitelisted_roles"]:
                                            guild_config["whitelisted_roles"].append(str(role.id))
                                            self.update_guild_config(whitelist_interaction.guild_id, guild_config)
                                            
                                            
                                            whitelisted_roles = []
                                            for role_id in guild_config["whitelisted_roles"]:
                                                r = whitelist_interaction.guild.get_role(int(role_id))
                                                if r:
                                                    whitelisted_roles.append(r.mention)
                                            
                                            roles_text = "\n".join(whitelisted_roles) if whitelisted_roles else "*Aucun rôle whitelisté*"
                                            embed.set_field_at(2, name=f"👥 Rôles whitelistés ({len(guild_config['whitelisted_roles'])})", value=roles_text)
                                            await button_interaction.message.edit(embed=embed, view=view)
                                            
                                            await msg.reply(f"✅ Rôle {role.mention} ajouté à la whitelist!")
                                        else:
                                            await msg.reply("❌ Ce rôle est déjà dans la whitelist.")
                                    else:
                                        await msg.reply("❌ Rôle non trouvé.")
                                        
                                except asyncio.TimeoutError:
                                    await whitelist_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                                    
                            elif whitelist_interaction.data["custom_id"] == "remove_role":
                                await whitelist_interaction.response.send_message(
                                    "🔍 Mentionnez le rôle à retirer, donnez son nom ou son ID",
                                    ephemeral=True
                                )
                                
                                def check(m):
                                    return m.author == whitelist_interaction.user and m.channel == whitelist_interaction.channel
                                
                                try:
                                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                                    role = None
                                    
                                    
                                    if msg.role_mentions:
                                        role = msg.role_mentions[0]
                                    else:
                                        
                                        role = discord.utils.get(whitelist_interaction.guild.roles, name=msg.content)
                                        if not role:
                                            
                                            try:
                                                role_id = int(msg.content)
                                                role = whitelist_interaction.guild.get_role(role_id)
                                            except ValueError:
                                                await msg.reply("❌ Format invalide. Mentionnez un rôle, donnez son nom ou son ID.")
                                                continue
                                    
                                    if role:
                                        if str(role.id) in guild_config["whitelisted_roles"]:
                                            guild_config["whitelisted_roles"].remove(str(role.id))
                                            self.update_guild_config(whitelist_interaction.guild_id, guild_config)
                                            
                                            
                                            whitelisted_roles = []
                                            for role_id in guild_config["whitelisted_roles"]:
                                                r = whitelist_interaction.guild.get_role(int(role_id))
                                                if r:
                                                    whitelisted_roles.append(r.mention)
                                            
                                            roles_text = "\n".join(whitelisted_roles) if whitelisted_roles else "*Aucun rôle whitelisté*"
                                            embed.set_field_at(2, name=f"👥 Rôles whitelistés ({len(guild_config['whitelisted_roles'])})", value=roles_text)
                                            await interaction.message.edit(embed=embed, view=view)
                                            
                                            await msg.reply(f"✅ Rôle {role.mention} retiré de la whitelist!")
                                        else:
                                            await msg.reply("❌ Ce rôle n'est pas dans la whitelist.")
                                    else:
                                        await msg.reply("❌ Rôle non trouvé.")
                                        
                                except asyncio.TimeoutError:
                                    await whitelist_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                                    
                            elif whitelist_interaction.data["custom_id"] == "add_user":
                                await whitelist_interaction.response.send_message(
                                    "🔍 Mentionnez l'utilisateur à ajouter, donnez son nom ou son ID",
                                    ephemeral=True
                                )
                                
                                def check(m):
                                    return m.author == whitelist_interaction.user and m.channel == whitelist_interaction.channel
                                
                                try:
                                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                                    user = None
                                    
                                    
                                    if msg.mentions:
                                        user = msg.mentions[0]
                                    else:
                                        
                                        user = discord.utils.get(whitelist_interaction.guild.members, name=msg.content)
                                        if not user:
                                            
                                            try:
                                                user_id = int(msg.content)
                                                user = await self.bot.fetch_user(user_id)
                                            except (ValueError, discord.NotFound):
                                                await msg.reply("❌ Format invalide. Mentionnez un utilisateur, donnez son nom ou son ID.")
                                                continue
                                    
                                    if user:
                                        if str(user.id) not in guild_config["whitelisted_users"]:
                                            guild_config["whitelisted_users"].append(str(user.id))
                                            self.update_guild_config(whitelist_interaction.guild_id, guild_config)
                                            
                                            
                                            whitelisted_users = []
                                            for user_id in guild_config["whitelisted_users"]:
                                                u = await self.bot.fetch_user(int(user_id))
                                                if u:
                                                    whitelisted_users.append(u.mention)
                                            
                                            users_text = "\n".join(whitelisted_users) if whitelisted_users else "*Aucun utilisateur whitelisté*"
                                            embed.set_field_at(3, name=f"👤 Utilisateurs whitelistés ({len(guild_config['whitelisted_users'])})", value=users_text)
                                            await interaction.message.edit(embed=embed, view=view)
                                            
                                            await msg.reply(f"✅ Utilisateur {user.mention} ajouté à la whitelist!")
                                        else:
                                            await msg.reply("❌ Cet utilisateur est déjà dans la whitelist.")
                                    else:
                                        await msg.reply("❌ Utilisateur non trouvé.")
                                        
                                except asyncio.TimeoutError:
                                    await whitelist_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                                    
                            elif whitelist_interaction.data["custom_id"] == "remove_user":
                                await whitelist_interaction.response.send_message(
                                    "🔍 Mentionnez l'utilisateur à retirer, donnez son nom ou son ID",
                                    ephemeral=True
                                )
                                
                                def check(m):
                                    return m.author == whitelist_interaction.user and m.channel == whitelist_interaction.channel
                                
                                try:
                                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                                    user = None
                                    
                                    
                                    if msg.mentions:
                                        user = msg.mentions[0]
                                    else:
                                        
                                        user = discord.utils.get(whitelist_interaction.guild.members, name=msg.content)
                                        if not user:
                                            
                                            try:
                                                user_id = int(msg.content)
                                                user = await self.bot.fetch_user(user_id)
                                            except (ValueError, discord.NotFound):
                                                await msg.reply("❌ Format invalide. Mentionnez un utilisateur, donnez son nom ou son ID.")
                                                continue
                                    
                                    if user:
                                        if str(user.id) in guild_config["whitelisted_users"]:
                                            guild_config["whitelisted_users"].remove(str(user.id))
                                            self.update_guild_config(whitelist_interaction.guild_id, guild_config)
                                            
                                            
                                            whitelisted_users = []
                                            for user_id in guild_config["whitelisted_users"]:
                                                u = await self.bot.fetch_user(int(user_id))
                                                if u:
                                                    whitelisted_users.append(u.mention)
                                            
                                            users_text = "\n".join(whitelisted_users) if whitelisted_users else "*Aucun utilisateur whitelisté*"
                                            embed.set_field_at(3, name=f"👤 Utilisateurs whitelistés ({len(guild_config['whitelisted_users'])})", value=users_text)
                                            await interaction.message.edit(embed=embed, view=view)
                                            
                                            await msg.reply(f"✅ Utilisateur {user.mention} retiré de la whitelist!")
                                        else:
                                            await msg.reply("❌ Cet utilisateur n'est pas dans la whitelist.")
                                    else:
                                        await msg.reply("❌ Utilisateur non trouvé.")
                                        
                                except asyncio.TimeoutError:
                                    await whitelist_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                                    
                    except asyncio.TimeoutError:
                        
                        for item in whitelist_view.children:
                            item.disabled = True
                        await whitelist_interaction.message.edit(view=whitelist_view)
                    
        except Exception as e:
            
            self.end_configuration(interaction.guild_id)
            print(f"Erreur dans la commande antilinks: {e}")

async def setup(bot):
    await bot.add_cog(AntiLinksConfigCommand(bot)) 
