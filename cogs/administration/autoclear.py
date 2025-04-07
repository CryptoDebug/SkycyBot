import discord
from discord import app_commands
import json
import os
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from utils.colors import get_embed_color

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

class AutoClearSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/autoclear_config.json"
        self.config = self._load_config()
        self.enabled = True
        self.is_cleaning = False
        self.auto_clear_loop.start()

    def _load_config(self):
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def get_guild_config(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.config:
            self.config[guild_id] = {
                "active_channels": [],
                "clear_delay": 300
            }
        return self.config[guild_id]

    @tasks.loop(minutes=1)
    async def auto_clear_loop(self):
        if self.enabled:
            for guild_id, guild_config in self.config.items():
                for channel_id in guild_config["active_channels"]:
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        await self.clear_messages(channel)

    async def clear_messages(self, channel):
        if not self.enabled or self.is_cleaning:
            return
            
        guild_config = self.get_guild_config(channel.guild.id)
        clear_delay = timedelta(seconds=guild_config["clear_delay"])
        
        if not channel.permissions_for(channel.guild.me).manage_messages:
            return
            
        self.is_cleaning = True
        try:
            cutoff = datetime.now(timezone.utc) - clear_delay
            messages_to_delete = []
            
            async for message in channel.history(limit=None):
                if message.created_at.replace(tzinfo=timezone.utc) < cutoff:
                    messages_to_delete.append(message)
                else:
                    break
            
            if messages_to_delete:
                for i in range(0, len(messages_to_delete), 100):
                    batch = messages_to_delete[i:i+100]
                    await channel.delete_messages(batch)
                
        except Exception as e:
            print(f"Erreur AutoClear: {e}")
        finally:
            self.is_cleaning = False

    @app_commands.command(name="autoclear", description="Configure la suppression automatique des messages")
    @admin_or_owner()
    async def autoclear(self, interaction: discord.Interaction):
        await self.setup_ui(interaction)

    def create_status_embed(self, guild_id, interaction):
        guild_config = self.get_guild_config(guild_id)
        embed = discord.Embed(
            title="⚙️ Configuration de l'AutoClear",
            description="Configurez la suppression automatique des messages dans vos salons.\n\n"
                       "**💡 Guide d'utilisation:**\n"
                       "• Activez/désactivez le système avec le bouton ON/OFF\n"
                       "• Ajoutez/retirez des salons avec les boutons correspondants\n"
                       "• Définissez le délai de suppression avec le bouton DÉFINIR DÉLAI",
            color=get_embed_color("administration")
        )
        
        
        status = "🟢 Activé" if self.enabled else "🔴 Désactivé"
        embed.add_field(
            name="🔌 État du système",
            value=f"**Statut:** {status}\n"
                  f"**ID du serveur:** `{guild_id}`",
            inline=False
        )
        
        
        minutes = guild_config["clear_delay"] // 60
        embed.add_field(
            name="⏱️ Configuration du délai",
            value=f"**Délai actuel:** {minutes} minutes\n"
                  f"**Prochaine suppression:** <t:{int((datetime.now(timezone.utc) + timedelta(seconds=guild_config['clear_delay'])).timestamp())}:R>",
            inline=False
        )
        
        
        channels_list = []
        for channel_id in guild_config["active_channels"]:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                channels_list.append(f"• {channel.mention}")
        
        channels_text = "\n".join(channels_list) if channels_list else "*Aucun salon configuré*"
        embed.add_field(
            name=f"📺 Salons actifs ({len(guild_config['active_channels'])})",
            value=channels_text,
            inline=False
        )
        
        
        embed.add_field(
            name="⏰ Dernière modification",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        
        embed.set_footer(
            text=f"ID du serveur: {guild_id}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        return embed

    async def setup_ui(self, interaction):
        view = discord.ui.View(timeout=120)
        
        buttons = [
            ("ON/OFF GLOBAL", None, self.toggle_system, discord.ButtonStyle.red if self.enabled else discord.ButtonStyle.green, "🔌"),
            ("AJOUTER SALON", "Mentionnez un salon", self.request_channel_add, discord.ButtonStyle.blurple, "➕"),
            ("RETIRER SALON", "Mentionnez un salon", self.request_channel_remove, discord.ButtonStyle.blurple, "➖"),
            ("DÉFINIR DÉLAI", None, self.request_delay, discord.ButtonStyle.grey, "⏱️")
        ]
        
        for label, placeholder, callback, style, emoji in buttons:
            btn = discord.ui.Button(label=label, style=style, emoji=emoji)
            btn.callback = callback
            view.add_item(btn)

        await interaction.response.send_message(
            embed=self.create_status_embed(interaction.guild.id, interaction), 
            view=view
        )

    async def toggle_system(self, interaction):
        self.enabled = not self.enabled
        await interaction.response.edit_message(
            embed=self.create_status_embed(interaction.guild.id, interaction),
            view=None
        )
        await self.show_new_ui(interaction)

    async def request_channel_add(self, interaction):
        await interaction.response.send_message(
            "🔍 Mentionnez le salon à ajouter (ex: 
            ephemeral=True
        )
        self.bot.loop.create_task(self.wait_for_channel(interaction, add=True))

    async def request_channel_remove(self, interaction):
        await interaction.response.send_message(
            "🔍 Mentionnez le salon à retirer (ex: 
            ephemeral=True
        )
        self.bot.loop.create_task(self.wait_for_channel(interaction, add=False))

    async def wait_for_channel(self, interaction, add=True):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.channel_mentions
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            channel = msg.channel_mentions[0]
            guild_config = self.get_guild_config(interaction.guild.id)
            
            if add:
                if channel.id not in guild_config["active_channels"]:
                    guild_config["active_channels"].append(channel.id)
                    self._save_config()
                action = "ajouté"
            else:
                if channel.id in guild_config["active_channels"]:
                    guild_config["active_channels"].remove(channel.id)
                    self._save_config()
                action = "retiré"
            
            await msg.reply(f"✅ Salon {channel.mention} {action} avec succès!")
            await self.show_new_ui(interaction)
        except TimeoutError:
            await interaction.followup.send("❌ Temps écoulé", ephemeral=True)

    async def request_delay(self, interaction):
        modal = discord.ui.Modal(title="⏱️ Définir le délai de suppression")
        modal.add_item(discord.ui.TextInput(
            label="Minutes",
            placeholder="Ex: 5",
            min_length=1,
            max_length=3
        ))
        
        async def on_submit(interaction):
            try:
                minutes = int(modal.children[0].value)
                if minutes <= 0:
                    raise ValueError
                
                guild_config = self.get_guild_config(interaction.guild.id)
                guild_config["clear_delay"] = minutes * 60
                self._save_config()
                
                await interaction.response.send_message(
                    f"✅ Délai défini à {minutes} minutes\n"
                    f"⏱️ Prochaine suppression: <t:{int((datetime.now(timezone.utc) + timedelta(minutes=minutes)).timestamp())}:R>",
                    ephemeral=True
                )
                await self.show_new_ui(interaction)
            except:
                await interaction.response.send_message(
                    "❌ Valeur invalide. Entrez un nombre de minutes valide.",
                    ephemeral=True
                )
        
        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

    async def show_new_ui(self, interaction):
        try:
            if interaction.message:
                await interaction.message.delete()
        except:
            pass
        
        view = discord.ui.View(timeout=120)
        buttons = [
            ("ON/OFF GLOBAL", None, self.toggle_system, discord.ButtonStyle.red if self.enabled else discord.ButtonStyle.green, "🔌"),
            ("AJOUTER SALON", "Mentionnez un salon", self.request_channel_add, discord.ButtonStyle.blurple, "➕"),
            ("RETIRER SALON", "Mentionnez un salon", self.request_channel_remove, discord.ButtonStyle.blurple, "➖"),
            ("DÉFINIR DÉLAI", None, self.request_delay, discord.ButtonStyle.grey, "⏱️")
        ]
        
        for label, placeholder, callback, style, emoji in buttons:
            btn = discord.ui.Button(label=label, style=style, emoji=emoji)
            btn.callback = callback
            view.add_item(btn)
            
        await interaction.followup.send(
            embed=self.create_status_embed(interaction.guild.id, interaction),
            view=view
        )

async def setup(bot):
    await bot.add_cog(AutoClearSystem(bot))
