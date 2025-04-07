import discord
from discord.ext import commands
import json

class VoiceManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('config.json') as f:
            config = json.load(f)
        self.voice_channel_id = int(config["voice_channel_id"])
        self.voice_channels = {}
        
        self.permissions_updated = {}  

    async def update_channel_permissions(self, channel, member, is_owner):
        
        try:
            
            if channel.id in self.permissions_updated and member.id in self.permissions_updated[channel.id]:
                
                if self.permissions_updated[channel.id][member.id] == is_owner:
                    return
                
                self.permissions_updated[channel.id][member.id] = is_owner
            else:
                
                if channel.id not in self.permissions_updated:
                    self.permissions_updated[channel.id] = {}
                
                self.permissions_updated[channel.id][member.id] = is_owner
            
            
            default_permissions = discord.PermissionOverwrite(
                connect=True,
                speak=True,
                view_channel=True
            )
            
            
            owner_permissions = discord.PermissionOverwrite(
                connect=True,
                speak=True,
                view_channel=True,
                manage_channels=True,  
                manage_permissions=True,  
                mute_members=True,  
                deafen_members=True,  
                move_members=True,  
                stream=True,  
                priority_speaker=True  
            )
            
            
            if is_owner:
                await channel.set_permissions(member, overwrite=owner_permissions)
                print(f"👑 Droits de propriétaire accordés à {member.display_name} dans {channel.name}")
            else:
                await channel.set_permissions(member, overwrite=default_permissions)
                print(f"👤 Droits standards accordés à {member.display_name} dans {channel.name}")
                
        except Exception as e:
            print(f"⚠️ Erreur lors de la mise à jour des permissions: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            
            if after.channel and after.channel.id == self.voice_channel_id:
                new_channel = await member.guild.create_voice_channel(
                    f"Vocal de {member.display_name}",
                    category=after.channel.category
                )
                self.voice_channels[new_channel.id] = member.id
                await member.move_to(new_channel)
                
                
                await self.update_channel_permissions(new_channel, member, True)
                
                print(f"✅ Salon créé : {new_channel.name}")
            
            
            if before.channel and before.channel.id in self.voice_channels:
                
                if len(before.channel.members) == 0:
                    await before.channel.delete()
                    del self.voice_channels[before.channel.id]
                    
                    if before.channel.id in self.permissions_updated:
                        del self.permissions_updated[before.channel.id]
                    print(f"❌ Salon supprimé : {before.channel.name}")
                else:
                    
                    new_owner = before.channel.members[0]
                    if self.voice_channels[before.channel.id] != new_owner.id:
                        
                        old_owner_id = self.voice_channels[before.channel.id]
                        old_owner = before.channel.guild.get_member(old_owner_id)
                        if old_owner and old_owner in before.channel.members:
                            await self.update_channel_permissions(before.channel, old_owner, False)
                        
                        
                        await self.update_channel_permissions(before.channel, new_owner, True)
                        
                        
                        await before.channel.edit(name=f"Vocal de {new_owner.display_name}")
                        self.voice_channels[before.channel.id] = new_owner.id
                        print(f"🔀 Propriété transférée à {new_owner.display_name}")
            
            
            if after.channel and after.channel.id in self.voice_channels:
                
                is_owner = self.voice_channels[after.channel.id] == member.id
                
                await self.update_channel_permissions(after.channel, member, is_owner)
                
        except Exception as e:
            print(f"⚠️ Erreur : {e}")

async def setup(bot):
    await bot.add_cog(VoiceManager(bot))
