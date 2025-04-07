import discord
import json
import os
from datetime import datetime
from utils.colors import get_embed_color

class InvitesSystem:
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/invites_config.json"
        self.config = self._load_config()
        self.invite_cache = {}

    def _load_config(self):
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"guilds": {}}

    def _save_config(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")

    def get_guild_config(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.config["guilds"]:
            self.config["guilds"][guild_id] = {
                "enabled": False,
                "channels": {
                    "joins": None,
                    "leaves": None
                },
                "invite_counts": {},
                "member_inviters": {}
            }
            self._save_config()
        return self.config["guilds"][guild_id]

    def update_guild_config(self, guild_id, new_config):
        guild_id = str(guild_id)
        if guild_id not in self.config["guilds"]:
            self.config["guilds"][guild_id] = {}
        self.config["guilds"][guild_id].update(new_config)
        self._save_config()
        print(f"Configuration mise à jour pour le serveur {guild_id}: {self.config['guilds'][guild_id]}")

    async def cache_invites(self, guild):
        self.invite_cache[guild.id] = {}
        for invite in await guild.invites():
            self.invite_cache[guild.id][invite.code] = invite.uses

    async def find_inviter(self, member):
        if member.guild.id not in self.invite_cache:
            return None

        new_invites = await member.guild.invites()
        for invite in new_invites:
            if invite.code in self.invite_cache[member.guild.id]:
                if invite.uses > self.invite_cache[member.guild.id][invite.code]:
                    return invite.inviter
        return None

    async def update_invite_cache(self, guild):
        for invite in await guild.invites():
            self.invite_cache[guild.id][invite.code] = invite.uses

    async def log_member_join(self, member, inviter):
        guild_config = self.get_guild_config(member.guild.id)
        
        if not guild_config["enabled"] or not guild_config["channels"]["joins"]:
            return

        channel = member.guild.get_channel(guild_config["channels"]["joins"])
        if not channel:
            return

        if inviter:
            inviter_id = str(inviter.id)
            
            if "invite_counts" not in guild_config:
                guild_config["invite_counts"] = {}
            if "member_inviters" not in guild_config:
                guild_config["member_inviters"] = {}
            
            if inviter_id not in guild_config["invite_counts"]:
                guild_config["invite_counts"][inviter_id] = 0
            guild_config["invite_counts"][inviter_id] += 1
            
            guild_config["member_inviters"][str(member.id)] = inviter_id
            
            self._save_config()

            message = f"{member.mention} a rejoint, invité par {inviter.mention} qui a désormais {guild_config['invite_counts'][inviter_id]} invitation{'s' if guild_config['invite_counts'][inviter_id] > 1 else ''}"
        else:
            message = f"{member.mention} a rejoint, mais je ne sais pas qui l'a invité (erreur: code d'invitation non trouvé)"

        await channel.send(message)

    async def log_member_leave(self, member):
        guild_config = self.get_guild_config(member.guild.id)
        
        if not guild_config["enabled"] or not guild_config["channels"]["leaves"]:
            return

        channel = member.guild.get_channel(guild_config["channels"]["leaves"])
        if not channel:
            return

        member_id = str(member.id)
        if "member_inviters" in guild_config and member_id in guild_config["member_inviters"]:
            inviter_id = guild_config["member_inviters"][member_id]
            if inviter_id in guild_config["invite_counts"]:
                guild_config["invite_counts"][inviter_id] -= 1
                if guild_config["invite_counts"][inviter_id] <= 0:
                    del guild_config["invite_counts"][inviter_id]
                del guild_config["member_inviters"][member_id]
                self._save_config()

                inviter = member.guild.get_member(int(inviter_id))
                if inviter:
                    message = f"{member.mention} a quitté, il avait été invité par {inviter.mention} qui a désormais {guild_config['invite_counts'].get(inviter_id, 0)} invitation{'s' if guild_config['invite_counts'].get(inviter_id, 0) > 1 else ''}"
                else:
                    message = f"{member.mention} a quitté, il avait été invité par un membre qui n'est plus sur le serveur"
            else:
                message = f"{member.mention} a quitté, il avait été invité par un membre qui n'est plus sur le serveur"
        else:
            message = f"{member.mention} a quitté mais je n'ai pas pu retracer son inviteur"

        await channel.send(message)

    async def show_leaderboard(self, guild, channel):
        guild_config = self.get_guild_config(guild.id)
        print(f"Configuration du serveur: {guild_config}")
        print(f"Compteurs d'invitations: {guild_config.get('invite_counts', {})}")

        if not guild_config.get("invite_counts"):
            return await channel.send("Aucune donnée d'invitation disponible.")

        sorted_inviters = sorted(guild_config["invite_counts"].items(), key=lambda x: x[1], reverse=True)
        print(f"Classement trié: {sorted_inviters}")
        
        embed = discord.Embed(
            title="🏆 Classement des invités",
            color=get_embed_color("info")
        )

        for i, (inviter_id, count) in enumerate(sorted_inviters[:10], 1):
            member = guild.get_member(int(inviter_id))
            print(f"Recherche membre {inviter_id}: {member}")
            if member:
                embed.add_field(
                    name=f"{i}. {member.name}",
                    value=f"{count} invitation{'s' if count > 1 else ''}",
                    inline=False
                )

        await channel.send(embed=embed) 
