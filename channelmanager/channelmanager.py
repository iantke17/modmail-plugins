import typing
import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

class ChannelPermsPlugin(commands.Cog):
    """Manage channel permission overwrites using traditional text commands."""

    def __init__(self, bot):
        self.bot = bot

    # --- Internal Shared Helper ---
    async def _apply_overwrite(self, ctx, permission_name: str, target: typing.Union[discord.Role, discord.Member], channel: discord.abc.GuildChannel, value_str: str):
        # Convert text value parameter to Python type
        norm_val = value_str.lower()
        if norm_val == "true":
            value = True
        elif norm_val == "false":
            value = False
        elif norm_val in ["none", "null", "reset"]:
            value = None
        else:
            raise commands.BadArgument("Value parameter must be exactly `True`, `False`, or `None`.")

        # Map display names to discord.Permissions attribute names
        perm_map = {
            "view channel": "view_channel",
            "manage channel": "manage_channels",
            "manage permissions": "manage_permissions",
            "manage webhooks": "manage_webhooks",
            "create invite": "create_instant_invite",
            "send messages": "send_messages",
            "send messages in threads": "send_messages_in_threads",
            "create public threads": "create_public_threads",
            "create private threads": "create_private_threads",
            "embed links": "embed_links",
            "attach files": "attach_files",
            "add reactions": "add_reactions",
            "use external emojis": "use_external_emojis",
            "use external stickers": "use_external_stickers",
            "mention @everyone, @here and all roles": "mention_everyone",
            "manage messages": "manage_messages",
            "pin messages": "read_message_history", # Modifies target through message context history layer
            "bypass slowmode": "manage_channels",
            "manage threads": "manage_threads",
            "read message history": "read_message_history",
            "send text-to-speech messages": "send_tts_messages",
            "send voice messages": "send_voice_messages",
            "create polls": "create_polls",
            "use application commands": "use_application_commands",
            "use activities": "use_embedded_activities",
            "use external apps": "use_external_apps"
        }

        clean_perm = permission_name.lower().strip()
        if clean_perm not in perm_map:
            raise commands.BadArgument(f"Invalid permission name selection. Read command help block rules.")

        attr_name = perm_map[clean_perm]
        
        # Pull current overwrites for role/user, update it, and apply
        overwrite = channel.overwrites_for(target)
        setattr(overwrite, attr_name, value)

        try:
            await channel.set_permissions(target, overwrite=overwrite)
            status_text = "ALLOWED" if value is True else ("DENIED" if value is False else "RESET (NONE)")
            await ctx.send(f"✅ Set **{permission_name}** to **{status_text}** for {target.mention} in {channel.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ Error: I lack required permissions to update overrides inside that channel.")

    # --- 1. ?channelpermissions ---
    @commands.command(name="channelpermissions")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def channel_permissions(self, ctx, permission: str, target: typing.Union[discord.Role, discord.Member], channel: discord.abc.GuildChannel, value: str):
        """Manage core basic channel configurations.
        
        Choices: View Channel, Manage Channel, Manage Permissions, Manage Webhooks
        Format: ?channelpermissions "View Channel" @Role #channel True
        """
        await self._apply_overwrite(ctx, permission, target, channel, value)

    # --- 2. ?membershippermissions ---
    @commands.command(name="membershippermissions")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def membership_permissions(self, ctx, permission: str, channel: discord.abc.GuildChannel, target: typing.Union[discord.Role, discord.Member], value: str):
        """Manage context invite creation parameters.
        
        Choices: Create Invite
        Format: ?membershippermissions "Create Invite" #channel @User False
        """
        await self._apply_overwrite(ctx, permission, target, channel, value)

    # --- 3. ?textchannelpermissions ---
    @commands.command(name="textchannelpermissions")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def text_channel_permissions(self, ctx, permission: str, channel: discord.abc.GuildChannel, target: typing.Union[discord.Role, discord.Member], value: str):
        """Manage writing, threads, and moderation text limits.
        
        Choices: Send Messages, Send Messages in Threads, Create Public Threads, Create Private Threads, Embed Links, Attach Files, Add Reactions, Use External Emojis, Use External Stickers, Mention @everyone, @here and All Roles, Manage Messages, Pin Messages, Bypass Slowmode, Manage Threads, Read Message History, Send Text-to-speech Messages, Send Voice Messages, Create Polls
        Format: ?textchannelpermissions "Send Messages" #channel @Role True
        """
        await self._apply_overwrite(ctx, permission, target, channel, value)

    # --- 4. ?appspermissions ---
    @commands.command(name="appspermissions")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def apps_permissions(self, ctx, permission: str, channel: discord.abc.GuildChannel, target: typing.Union[discord.Role, discord.Member], value: str):
        """Manage interactive external application integrations.
        
        Choices: Use Application Commands, Use Activities, Use External Apps
        Format: ?appspermissions "Use Application Commands" #channel @User None
        """
        await self._apply_overwrite(ctx, permission, target, channel, value)


async def setup(bot):
    await bot.add_cog(ChannelPermsPlugin(bot))
