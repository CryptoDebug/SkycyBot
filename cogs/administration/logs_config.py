import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color
from utils.logs import LogsSystem
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

class LogsConfigCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logs = LogsSystem(bot)

    @app_commands.command(name="logs", description="Configure le système de logs")
    @admin_or_owner()
    async def logs_command(self, interaction: discord.Interaction):
        view = LogsConfigView(self.logs, interaction.guild.id)
        embed = await view.create_config_embed()
        await interaction.response.send_message(embed=embed, view=view)

class LogsConfigView(discord.ui.View):
    def __init__(self, logs_system, guild_id):
        super().__init__(timeout=120)
        self.logs = logs_system
        self.guild_id = guild_id
        self.config = self.logs.get_guild_config(guild_id)

        
        toggle_button = discord.ui.Button(
            label="ON/OFF",
            style=discord.ButtonStyle.danger if self.config["enabled"] else discord.ButtonStyle.success,
            emoji="🔌",
            custom_id="toggle_logs"
        )
        toggle_button.callback = self.toggle_logs
        self.add_item(toggle_button)

        
        channel_buttons = [
            ("Messages", "💬", "messages"),
            ("Modération", "🛡️", "moderation"),
            ("Administration", "⚙️", "administration")
        ]

        for label, emoji, channel_type in channel_buttons:
            btn = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                emoji=emoji,
                custom_id=f"set_{channel_type}"
            )
            btn.callback = lambda i, t=channel_type: self.set_channel(i, t)
            self.add_item(btn)

        
        filters_button = discord.ui.Button(
            label="Filtres",
            style=discord.ButtonStyle.secondary,
            emoji="🔍",
            custom_id="filters"
        )
        filters_button.callback = self.show_filters
        self.add_item(filters_button)

    async def create_config_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="⚙️ Configuration des Logs",
            description="Configurez les canaux de logs pour votre serveur.\n\n"
                       "**💡 Guide d'utilisation:**\n"
                       "• Activez/désactivez le système avec le bouton ON/OFF\n"
                       "• Configurez les canaux pour chaque type de log\n"
                       "• Gérez les filtres des logs\n"
                       "• Les logs sont envoyés en temps réel\n\n"
                       "**Note:** Les logs de rôles, salons, membres, emojis et serveur sont déjà disponibles dans les logs d'audit de Discord.",
            color=get_embed_color("administration")
        )

        
        status = "🟢 Activé" if self.config["enabled"] else "🔴 Désactivé"
        embed.add_field(
            name="🔌 État du système",
            value=f"**Statut:** {status}\n"
                  f"**ID du serveur:** `{self.guild_id}`",
            inline=False
        )

        
        channels_info = []
        for channel_type, channel_id in self.config["channels"].items():
            if channel_type in ["messages", "moderation", "administration"]:
                channel = self.logs.bot.get_channel(channel_id) if channel_id else None
                emoji = {
                    "messages": "💬",
                    "moderation": "🛡️",
                    "administration": "⚙️"
                }.get(channel_type, "📺")
                
                channel_name = channel.mention if channel else "Non configuré"
                channels_info.append(f"**{emoji} {channel_type.title()}:** {channel_name}")
        
        embed.add_field(
            name="📺 Canaux de logs",
            value="\n".join(channels_info),
            inline=False
        )

        
        filters_info = [
            f"**📺 Salons ignorés:** {len(self.config['filters']['ignored_channels'])}",
            f"**👤 Utilisateurs ignorés:** {len(self.config['filters']['ignored_users'])}",
            f"**👥 Rôles ignorés:** {len(self.config['filters']['ignored_roles'])}"
        ]
        
        embed.add_field(
            name="🔍 Filtres actifs",
            value="\n".join(filters_info),
            inline=False
        )

        
        embed.add_field(
            name="⏰ Dernière modification",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )

        
        embed.set_footer(
            text=f"ID du serveur: {self.guild_id}",
            icon_url=self.logs.bot.get_guild(self.guild_id).icon.url if self.logs.bot.get_guild(self.guild_id).icon else None
        )

        return embed

    async def toggle_logs(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(
                "❌ Cette commande est réservée aux administrateurs et au propriétaire du serveur.",
                ephemeral=True
            )

        self.config["enabled"] = not self.config["enabled"]
        self.logs.update_guild_config(self.guild_id, self.config)

        
        for item in self.children:
            if item.custom_id == "toggle_logs":
                item.style = discord.ButtonStyle.danger if self.config["enabled"] else discord.ButtonStyle.success
                break

        embed = await self.create_config_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def set_channel(self, interaction: discord.Interaction, channel_type: str):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(
                "❌ Cette commande est réservée aux administrateurs et au propriétaire du serveur.",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"🔍 Mentionnez le salon que vous souhaitez utiliser pour les logs de {channel_type.title()}",
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.channel_mentions

        try:
            msg = await self.logs.bot.wait_for('message', check=check, timeout=60)
            channel = msg.channel_mentions[0]
            
            if not channel.permissions_for(interaction.guild.me).send_messages:
                await msg.reply("❌ Je n'ai pas la permission d'envoyer des messages dans ce salon.")
                return

            self.config["channels"][channel_type] = channel.id
            self.logs.update_guild_config(self.guild_id, self.config)
            
            await msg.reply(f"✅ Salon {channel.mention} configuré pour les logs de {channel_type.title()}!")
            embed = await self.create_config_embed()
            await interaction.message.edit(embed=embed)
            
        except TimeoutError:
            await interaction.followup.send("❌ Temps écoulé. Veuillez réessayer.", ephemeral=True)

    async def show_filters(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(
                "❌ Cette commande est réservée aux administrateurs et au propriétaire du serveur.",
                ephemeral=True
            )

        modal = discord.ui.Modal(title="🔍 Configuration des Filtres")
        
        
        ignored_channels_text = discord.ui.TextInput(
            label="IDs des salons ignorés",
            placeholder="123456789,987654321",
            default=",".join(map(str, self.config["filters"]["ignored_channels"])),
            required=False
        )
        modal.add_item(ignored_channels_text)

        
        ignored_users_text = discord.ui.TextInput(
            label="IDs des utilisateurs ignorés",
            placeholder="123456789,987654321",
            default=",".join(map(str, self.config["filters"]["ignored_users"])),
            required=False
        )
        modal.add_item(ignored_users_text)

        
        ignored_roles_text = discord.ui.TextInput(
            label="IDs des rôles ignorés",
            placeholder="123456789,987654321",
            default=",".join(map(str, self.config["filters"]["ignored_roles"])),
            required=False
        )
        modal.add_item(ignored_roles_text)

        async def on_submit(interaction: discord.Interaction):
            try:
                
                self.config["filters"]["ignored_channels"] = [
                    int(cid.strip()) for cid in ignored_channels_text.value.split(",")
                    if cid.strip().isdigit()
                ]

                
                self.config["filters"]["ignored_users"] = [
                    int(uid.strip()) for uid in ignored_users_text.value.split(",")
                    if uid.strip().isdigit()
                ]

                
                self.config["filters"]["ignored_roles"] = [
                    int(rid.strip()) for rid in ignored_roles_text.value.split(",")
                    if rid.strip().isdigit()
                ]

                self.logs.update_guild_config(self.guild_id, self.config)
                await interaction.response.send_message("✅ Filtres mis à jour avec succès!", ephemeral=True)
                embed = await self.create_config_embed()
                await interaction.message.edit(embed=embed)

            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Erreur lors de la mise à jour des filtres: {str(e)}",
                    ephemeral=True
                )

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(LogsConfigCommand(bot)) 
