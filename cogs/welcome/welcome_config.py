import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime
from utils.colors import get_embed_color

class WelcomeConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/welcome/config.json"
        self.load_config()
        
        self.active_configurations = {}  
        
    def load_config(self):
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}
            
    def save_config(self):
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)
            
    def get_guild_config(self, guild_id):
        
        guild_id = str(guild_id)
        if guild_id not in self.config:
            self.config[guild_id] = {
                "enabled": False,
                "channel_id": None,
                "message": "Bienvenue {user.mention} sur {server.name} ! Tu es notre {member_count}ème membre !",
                "auto_role_id": None,
                "verification_enabled": False,
                "verification_channel_id": None,
                "verification_message": "Pour vérifier votre compte, répondez à la question suivante :\n{question}",
                "verification_questions": [
                    "Quelle est la capitale de la France ?",
                    "Combien font 2 + 2 ?",
                    "Quelle est la couleur du ciel ?"
                ]
            }
            self.save_config()
        return self.config[guild_id]
        
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
        
    @app_commands.command(name="welcome", description="Configurer le système de bienvenue")
    async def welcome(self, interaction: discord.Interaction):
        
        if not self.has_permissions(interaction):
            await interaction.response.send_message(
                "❌ Vous n'avez pas les permissions nécessaires pour utiliser cette commande. "
                "Seuls les administrateurs et le propriétaire du serveur peuvent l'utiliser.",
                ephemeral=True
            )
            return

        
        if self.is_configuration_active(interaction.guild_id):
            user_id = self.get_active_configuration_user(interaction.guild_id)
            user = await self.bot.fetch_user(user_id)
            username = user.name if user else "un utilisateur"
            await interaction.response.send_message(
                f"❌ Une configuration est déjà en cours par {username}.",
                ephemeral=True
            )
            return

        
        self.start_configuration(interaction.guild_id, interaction.user.id)

        guild_config = self.get_guild_config(interaction.guild_id)
        
        
        toggle_button = discord.ui.Button(
            label="ON" if not guild_config["enabled"] else "OFF",
            style=discord.ButtonStyle.green if not guild_config["enabled"] else discord.ButtonStyle.red,
            custom_id="toggle_welcome"
        )
        
        channel_button = discord.ui.Button(
            label="Canal de bienvenue",
            style=discord.ButtonStyle.primary,
            custom_id="welcome_channel"
        )
        
        message_button = discord.ui.Button(
            label="Message de bienvenue",
            style=discord.ButtonStyle.primary,
            custom_id="welcome_message"
        )
        
        verification_button = discord.ui.Button(
            label="Vérification",
            style=discord.ButtonStyle.secondary,
            custom_id="verification"
        )
        
        role_button = discord.ui.Button(
            label="Rôle automatique",
            style=discord.ButtonStyle.secondary,
            custom_id="auto_role"
        )
        
        close_button = discord.ui.Button(
            label="Fermer",
            style=discord.ButtonStyle.danger,
            custom_id="close"
        )
        
        
        view = discord.ui.View(timeout=300)  
        view.add_item(toggle_button)
        view.add_item(channel_button)
        view.add_item(message_button)
        view.add_item(verification_button)
        view.add_item(role_button)
        view.add_item(close_button)
        
        
        embed = discord.Embed(
            title="⚙️ Configuration du système de bienvenue",
            description="Configurez le système de bienvenue pour votre serveur.\n\n"
                       "**💡 Guide d'utilisation:**\n"
                       "• Activez/désactivez le système avec le bouton ON/OFF\n"
                       "• Configurez le canal et le message de bienvenue\n"
                       "• Configurez le système de vérification\n"
                       "• Configurez le rôle automatique\n"
                       "• Cliquez sur 'Fermer' pour terminer la configuration",
            color=get_embed_color("welcome")
        )
        
        
        status = "🟢 Activé" if guild_config["enabled"] else "🔴 Désactivé"
        embed.add_field(
            name="🔌 État du système",
            value=f"**Statut:** {status}\n"
                  f"**ID du serveur:** `{interaction.guild_id}`",
            inline=False
        )
        
        
        channel_text = "Non défini"
        if guild_config["channel_id"]:
            channel = interaction.guild.get_channel(guild_config["channel_id"])
            if channel:
                channel_text = channel.mention
                
        embed.add_field(
            name="📺 Canal de bienvenue",
            value=channel_text,
            inline=False
        )
        
        
        embed.add_field(
            name="💬 Message de bienvenue",
            value=guild_config["message"],
            inline=False
        )
        
        
        verification_status = "Activé" if guild_config["verification_enabled"] else "Désactivé"
        verification_channel = "Non défini"
        if guild_config["verification_channel_id"]:
            channel = interaction.guild.get_channel(guild_config["verification_channel_id"])
            if channel:
                verification_channel = channel.mention
                
        embed.add_field(
            name="🔒 Système de vérification",
            value=f"**Statut:** {verification_status}\n"
                  f"**Canal:** {verification_channel}",
            inline=False
        )
        
        
        role_text = "Non défini"
        if guild_config["auto_role_id"]:
            role = interaction.guild.get_role(guild_config["auto_role_id"])
            if role:
                role_text = role.mention
                
        embed.add_field(
            name="👤 Rôle automatique",
            value=role_text,
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
                            check=lambda i: isinstance(i, discord.Interaction) and i.type == discord.InteractionType.component and i.data.get("custom_id") in ["toggle_welcome", "welcome_channel", "welcome_message", "verification", "auto_role", "close"]
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
                
                if button_interaction.data["custom_id"] == "toggle_welcome":
                    
                    guild_config = self.get_guild_config(button_interaction.guild_id)
                    guild_config["enabled"] = not guild_config["enabled"]
                    self.save_config()
                    
                    
                    toggle_button.label = "ON" if not guild_config["enabled"] else "OFF"
                    toggle_button.style = discord.ButtonStyle.green if not guild_config["enabled"] else discord.ButtonStyle.red
                    
                    
                    status = "🟢 Activé" if guild_config["enabled"] else "🔴 Désactivé"
                    embed.set_field_at(0, name="🔌 État du système", value=f"**Statut:** {status}\n**ID du serveur:** `{button_interaction.guild_id}`")
                    
                    await button_interaction.response.edit_message(embed=embed, view=view)
                    
                elif button_interaction.data["custom_id"] == "welcome_channel":
                    await button_interaction.response.send_message(
                        "🔍 Mentionnez le canal de bienvenue ou envoyez son ID",
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
                                await msg.reply("❌ Format invalide. Mentionnez un canal ou envoyez son ID.")
                                continue
                        
                        if channel:
                            guild_config = self.get_guild_config(button_interaction.guild_id)
                            guild_config["channel_id"] = channel.id
                            self.save_config()
                            
                            
                            embed.set_field_at(1, name="📺 Canal de bienvenue", value=channel.mention)
                            await button_interaction.message.edit(embed=embed, view=view)
                            await msg.reply(f"✅ Canal de bienvenue configuré sur {channel.mention}!")
                        else:
                            await msg.reply("❌ Canal non trouvé.")
                            
                    except asyncio.TimeoutError:
                        await button_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                        
                elif button_interaction.data["custom_id"] == "welcome_message":
                    await button_interaction.response.send_message(
                        "📝 Envoyez le message de bienvenue. Vous pouvez utiliser les variables suivantes:\n"
                        "• `{user.mention}` - Mentionne l'utilisateur\n"
                        "• `{server.name}` - Nom du serveur\n"
                        "• `{member_count}` - Nombre de membres",
                        ephemeral=True
                    )
                    
                    def check(m):
                        return m.author == button_interaction.user and m.channel == button_interaction.channel
                    
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=60)
                        
                        guild_config = self.get_guild_config(button_interaction.guild_id)
                        guild_config["message"] = msg.content
                        self.save_config()
                        
                        
                        embed.set_field_at(2, name="💬 Message de bienvenue", value=msg.content)
                        await button_interaction.message.edit(embed=embed, view=view)
                        await msg.reply("✅ Message de bienvenue configuré!")
                            
                    except asyncio.TimeoutError:
                        await button_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                        
                elif button_interaction.data["custom_id"] == "verification":
                    
                    verification_view = discord.ui.View()
                    
                    toggle_verification_button = discord.ui.Button(
                        label="ON" if not guild_config["verification_enabled"] else "OFF",
                        style=discord.ButtonStyle.green if not guild_config["verification_enabled"] else discord.ButtonStyle.red,
                        custom_id="toggle_verification"
                    )
                    
                    verification_channel_button = discord.ui.Button(
                        label="Canal de vérification",
                        style=discord.ButtonStyle.primary,
                        custom_id="verification_channel"
                    )
                    
                    verification_message_button = discord.ui.Button(
                        label="Message de vérification",
                        style=discord.ButtonStyle.primary,
                        custom_id="verification_message"
                    )
                    
                    verification_questions_button = discord.ui.Button(
                        label="Questions de vérification",
                        style=discord.ButtonStyle.secondary,
                        custom_id="verification_questions"
                    )
                    
                    back_button = discord.ui.Button(
                        label="Retour",
                        style=discord.ButtonStyle.danger,
                        custom_id="back"
                    )
                    
                    verification_view.add_item(toggle_verification_button)
                    verification_view.add_item(verification_channel_button)
                    verification_view.add_item(verification_message_button)
                    verification_view.add_item(verification_questions_button)
                    verification_view.add_item(back_button)
                    
                    
                    verification_embed = discord.Embed(
                        title="⚙️ Configuration du système de vérification",
                        description="Configurez le système de vérification pour les nouveaux membres.\n\n"
                                   "**💡 Guide d'utilisation:**\n"
                                   "• Activez/désactivez la vérification avec le bouton ON/OFF\n"
                                   "• Configurez le canal de vérification\n"
                                   "• Configurez le message de vérification\n"
                                   "• Configurez les questions de vérification\n"
                                   "• Cliquez sur 'Retour' pour revenir au menu principal",
                        color=get_embed_color("welcome")
                    )
                    
                    
                    verification_status = "🟢 Activé" if guild_config["verification_enabled"] else "🔴 Désactivé"
                    verification_embed.add_field(
                        name="🔌 État du système de vérification",
                        value=f"**Statut:** {verification_status}",
                        inline=False
                    )
                    
                    
                    verification_channel_text = "Non défini"
                    if guild_config["verification_channel_id"]:
                        channel = button_interaction.guild.get_channel(guild_config["verification_channel_id"])
                        if channel:
                            verification_channel_text = channel.mention
                            
                    verification_embed.add_field(
                        name="📺 Canal de vérification",
                        value=verification_channel_text,
                        inline=False
                    )
                    
                    
                    verification_embed.add_field(
                        name="💬 Message de vérification",
                        value=guild_config["verification_message"],
                        inline=False
                    )
                    
                    
                    questions_text = "\n".join([f"• {q}" for q in guild_config["verification_questions"]])
                    verification_embed.add_field(
                        name="❓ Questions de vérification",
                        value=questions_text,
                        inline=False
                    )
                    
                    await button_interaction.response.edit_message(embed=verification_embed, view=verification_view)
                    
                    try:
                        while True:
                            verification_interaction = await self.bot.wait_for(
                                "interaction",
                                check=lambda i: isinstance(i, discord.Interaction) and 
                                             i.type == discord.InteractionType.component and 
                                             i.data.get("custom_id") in ["toggle_verification", "verification_channel", "verification_message", "verification_questions", "back"]
                            )
                            
                            if not self.has_permissions(verification_interaction):
                                await verification_interaction.response.send_message(
                                    "❌ Vous n'avez pas les permissions nécessaires pour utiliser cette commande. "
                                    "Seuls les administrateurs et le propriétaire du serveur peuvent l'utiliser.",
                                    ephemeral=True
                                )
                                continue
                            
                            if verification_interaction.data["custom_id"] == "back":
                                await verification_interaction.response.edit_message(embed=embed, view=view)
                                break
                            
                            if verification_interaction.data["custom_id"] == "toggle_verification":
                                
                                guild_config = self.get_guild_config(verification_interaction.guild_id)
                                guild_config["verification_enabled"] = not guild_config["verification_enabled"]
                                self.save_config()
                                
                                
                                toggle_verification_button.label = "ON" if not guild_config["verification_enabled"] else "OFF"
                                toggle_verification_button.style = discord.ButtonStyle.green if not guild_config["verification_enabled"] else discord.ButtonStyle.red
                                
                                
                                verification_status = "🟢 Activé" if guild_config["verification_enabled"] else "🔴 Désactivé"
                                verification_embed.set_field_at(0, name="🔌 État du système de vérification", value=f"**Statut:** {verification_status}")
                                
                                await verification_interaction.response.edit_message(embed=verification_embed, view=verification_view)
                                
                            elif verification_interaction.data["custom_id"] == "verification_channel":
                                await verification_interaction.response.send_message(
                                    "🔍 Mentionnez le canal de vérification ou envoyez son ID",
                                    ephemeral=True
                                )
                                
                                def check(m):
                                    return m.author == verification_interaction.user and m.channel == verification_interaction.channel
                                
                                try:
                                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                                    channel = None
                                    
                                    
                                    if msg.channel_mentions:
                                        channel = msg.channel_mentions[0]
                                    else:
                                        
                                        try:
                                            channel_id = int(msg.content)
                                            channel = verification_interaction.guild.get_channel(channel_id)
                                        except ValueError:
                                            await msg.reply("❌ Format invalide. Mentionnez un canal ou envoyez son ID.")
                                            continue
                                    
                                    if channel:
                                        guild_config = self.get_guild_config(verification_interaction.guild_id)
                                        guild_config["verification_channel_id"] = channel.id
                                        self.save_config()
                                        
                                        
                                        verification_embed.set_field_at(1, name="📺 Canal de vérification", value=channel.mention)
                                        await verification_interaction.message.edit(embed=verification_embed, view=verification_view)
                                        await msg.reply(f"✅ Canal de vérification configuré sur {channel.mention}!")
                                    else:
                                        await msg.reply("❌ Canal non trouvé.")
                                        
                                except asyncio.TimeoutError:
                                    await verification_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                                    
                            elif verification_interaction.data["custom_id"] == "verification_message":
                                await verification_interaction.response.send_message(
                                    "📝 Envoyez le message de vérification. Vous pouvez utiliser la variable suivante:\n"
                                    "• `{question}` - La question de vérification",
                                    ephemeral=True
                                )
                                
                                def check(m):
                                    return m.author == verification_interaction.user and m.channel == verification_interaction.channel
                                
                                try:
                                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                                    
                                    guild_config = self.get_guild_config(verification_interaction.guild_id)
                                    guild_config["verification_message"] = msg.content
                                    self.save_config()
                                    
                                    
                                    verification_embed.set_field_at(2, name="💬 Message de vérification", value=msg.content)
                                    await verification_interaction.message.edit(embed=verification_embed, view=verification_view)
                                    await msg.reply("✅ Message de vérification configuré!")
                                        
                                except asyncio.TimeoutError:
                                    await verification_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                                    
                            elif verification_interaction.data["custom_id"] == "verification_questions":
                                await verification_interaction.response.send_message(
                                    "📝 Envoyez les questions de vérification, une par ligne. Exemple:\n"
                                    "Quelle est la capitale de la France ?\n"
                                    "Combien font 2 + 2 ?\n"
                                    "Quelle est la couleur du ciel ?",
                                    ephemeral=True
                                )
                                
                                def check(m):
                                    return m.author == verification_interaction.user and m.channel == verification_interaction.channel
                                
                                try:
                                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                                    
                                    guild_config = self.get_guild_config(verification_interaction.guild_id)
                                    guild_config["verification_questions"] = [q.strip() for q in msg.content.split("\n") if q.strip()]
                                    self.save_config()
                                    
                                    
                                    questions_text = "\n".join([f"• {q}" for q in guild_config["verification_questions"]])
                                    verification_embed.set_field_at(3, name="❓ Questions de vérification", value=questions_text)
                                    await verification_interaction.message.edit(embed=verification_embed, view=verification_view)
                                    await msg.reply("✅ Questions de vérification configurées!")
                                        
                                except asyncio.TimeoutError:
                                    await verification_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                                    
                    except asyncio.TimeoutError:
                        
                        for item in verification_view.children:
                            item.disabled = True
                        await verification_interaction.message.edit(view=verification_view)
                        
                elif button_interaction.data["custom_id"] == "auto_role":
                    await button_interaction.response.send_message(
                        "🔍 Mentionnez le rôle à attribuer automatiquement ou envoyez son ID",
                        ephemeral=True
                    )
                    
                    def check(m):
                        return m.author == button_interaction.user and m.channel == button_interaction.channel
                    
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=60)
                        role = None
                        
                        
                        if msg.role_mentions:
                            role = msg.role_mentions[0]
                        else:
                            
                            try:
                                role_id = int(msg.content)
                                role = button_interaction.guild.get_role(role_id)
                            except ValueError:
                                await msg.reply("❌ Format invalide. Mentionnez un rôle ou envoyez son ID.")
                                continue
                        
                        if role:
                            guild_config = self.get_guild_config(button_interaction.guild_id)
                            guild_config["auto_role_id"] = role.id
                            self.save_config()
                            
                            
                            embed.set_field_at(4, name="👤 Rôle automatique", value=role.mention)
                            await button_interaction.message.edit(embed=embed, view=view)
                            await msg.reply(f"✅ Rôle automatique configuré sur {role.mention}!")
                        else:
                            await msg.reply("❌ Rôle non trouvé.")
                            
                    except asyncio.TimeoutError:
                        await button_interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                    
        except Exception as e:
            
            self.end_configuration(interaction.guild_id)
            print(f"Erreur dans la commande welcome: {e}")
        
    @app_commands.command(name="welcomeinfo", description="Affiche la configuration actuelle du système de bienvenue")
    async def welcome_info_command(self, interaction: discord.Interaction):
        
        guild_config = self.get_guild_config(interaction.guild_id)
        
        embed = discord.Embed(
            title="Configuration du système de bienvenue",
            color=get_embed_color("welcome")
        )
        
        embed.add_field(name="État", value="Activé" if guild_config["enabled"] else "Désactivé", inline=False)
        
        if guild_config["channel_id"]:
            channel = interaction.guild.get_channel(guild_config["channel_id"])
            embed.add_field(name="Salon de bienvenue", value=channel.mention if channel else "Non défini", inline=False)
            
        embed.add_field(name="Message de bienvenue", value=guild_config["message"], inline=False)
        
        if guild_config["auto_role_id"]:
            role = interaction.guild.get_role(guild_config["auto_role_id"])
            embed.add_field(name="Rôle automatique", value=role.mention if role else "Non défini", inline=False)
            
        embed.add_field(name="Vérification", value="Activée" if guild_config["verification_enabled"] else "Désactivée", inline=False)
        
        if guild_config["verification_channel_id"]:
            channel = interaction.guild.get_channel(guild_config["verification_channel_id"])
            embed.add_field(name="Salon de vérification", value=channel.mention if channel else "Non défini", inline=False)
            
        await interaction.response.send_message(embed=embed)
        
async def setup(bot):
    await bot.add_cog(WelcomeConfig(bot)) 
