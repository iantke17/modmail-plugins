import asyncio
import datetime
import discord
import logging
import pytz

from difflib import get_close_matches
from discord.ext import commands
from pytz import timezone

from core import checks
from core.models import PermissionLevel


logger = logging.getLogger("Modmail")


class BirthdayPlugin(commands.Cog):
    """Birthday plugin."""

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

        self.birthdays = {}
        self.roles = {}
        self.channels = {}
        self.messages = {}

        self.timezone = "America/Chicago"
        self.enabled = True

        asyncio.create_task(self._startup())

    # --------------------------------------------------

    async def _startup(self):
        await self.bot.wait_until_ready()
        await self._set_db()

    # --------------------------------------------------

    async def _set_db(self):

        birthdays = await self.db.find_one({"_id": "birthdays"})
        config = await self.db.find_one({"_id": "config"})

        if birthdays is None:
            await self.db.find_one_and_update(
                {"_id": "birthdays"},
                {"$set": {"birthdays": {}}},
                upsert=True
            )

            birthdays = await self.db.find_one({"_id": "birthdays"})

        if config is None:
            await self.db.find_one_and_update(
                {"_id": "config"},
                {
                    "$set": {
                        "roles": {},
                        "channels": {},
                        "enabled": True,
                        "timezone": "America/Chicago",
                        "messages": {},
                    }
                },
                upsert=True
            )

            config = await self.db.find_one({"_id": "config"})

        self.birthdays = birthdays.get("birthdays", {})
        self.roles = config.get("roles", {})
        self.channels = config.get("channels", {})
        self.enabled = config.get("enabled", True)
        self.timezone = config.get("timezone", "America/Chicago")
        self.messages = config.get("messages", {})

        asyncio.create_task(self._handle_birthdays())

    # --------------------------------------------------

    async def _update_birthdays(self):

        await self.db.find_one_and_update(
            {"_id": "birthdays"},
            {"$set": {"birthdays": self.birthdays}},
            upsert=True
        )

    # --------------------------------------------------

    async def _update_config(self):

        await self.db.find_one_and_update(
            {"_id": "config"},
            {
                "$set": {
                    "roles": self.roles,
                    "channels": self.channels,
                    "enabled": self.enabled,
                    "timezone": self.timezone,
                    "messages": self.messages,
                }
            },
            upsert=True
        )

    # --------------------------------------------------

    async def _handle_birthdays(self):

        await self.bot.wait_until_ready()

        while not self.bot.is_closed():

            if not self.enabled:
                await asyncio.sleep(60)
                continue

            tz = timezone(self.timezone)
            now = datetime.datetime.now(tz)
            today = now.date()

            for user_id, obj in self.birthdays.items():

                if obj["month"] != today.month or obj["day"] != today.day:
                    continue

                guild = self.bot.get_guild(int(obj["guild"]))
                if not guild:
                    continue

                member = guild.get_member(int(user_id))
                if not member:
                    continue

                # Add role
                role_id = self.roles.get(obj["guild"])

                if role_id:
                    role = guild.get_role(int(role_id))

                    if role:
                        await member.add_roles(
                            role,
                            reason="Birthday"
                        )

                # Send message
                channel_id = self.channels.get(obj["guild"])
                msg = self.messages.get(obj["guild"])

                if channel_id and msg:

                    channel = guild.get_channel(int(channel_id))

                    if not channel:
                        continue

                    # Age
                    age = ""

                    if obj.get("year"):
                        age = str(now.year - obj["year"])

                    age_text = age if age else "N/A"

                    text = (
                        msg.replace("{user.mention}", member.mention)
                           .replace("{user}", str(member))
                           .replace("{age}", age_text)
                    )

                    await channel.send(text)

            # Sleep until midnight
            tomorrow = (now + datetime.timedelta(days=1)).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )

            sleep_time = max(
                (tomorrow - now).total_seconds(),
                0
            )

            await asyncio.sleep(sleep_time)

    # --------------------------------------------------

    @commands.group(invoke_without_command=True)
    async def birthday(self, ctx: commands.Context):
        """Birthday commands"""

        await ctx.send_help(ctx.command)

    # --------------------------------------------------

    @birthday.command()
    async def set(self, ctx: commands.Context, date: str):
        """
        Set your birthday.

        Format:
        DD/MM or DD/MM/YYYY
        """

        parts = date.split("/")

        try:
            if len(parts) == 2:

                day, month = map(int, parts)
                year = None

                datetime.date(2000, month, day)

            elif len(parts) == 3:

                day, month, year = map(int, parts)

                datetime.date(year, month, day)

            else:
                raise ValueError

        except Exception:
            await ctx.send("Invalid format. Use DD/MM or DD/MM/YYYY.")
            return

        birthday_obj = {
            "day": day,
            "month": month,
            "year": year,
            "guild": str(ctx.guild.id),
        }

        self.birthdays[str(ctx.author.id)] = birthday_obj

        await self._update_birthdays()

        await ctx.send(f"Birthday set to `{date}`")

    # --------------------------------------------------

    @birthday.command()
    async def clear(self, ctx: commands.Context):
        """Remove your birthday"""

        self.birthdays.pop(str(ctx.author.id), None)

        await self._update_birthdays()

        await ctx.send("Birthday cleared.")

    # --------------------------------------------------

    @birthday.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set announcement channel"""

        self.channels[str(ctx.guild.id)] = str(channel.id)

        await self._update_config()

        await ctx.send("Channel set.")

    # --------------------------------------------------

    @birthday.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def role(self, ctx: commands.Context, role: discord.Role):
        """Set birthday role"""

        self.roles[str(ctx.guild.id)] = str(role.id)

        await self._update_config()

        await ctx.send("Role set.")

    # --------------------------------------------------

    @birthday.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def message(self, ctx: commands.Context, *, msg: str):
        """Set birthday message"""

        self.messages[str(ctx.guild.id)] = msg

        await self._update_config()

        await ctx.send("Message set.")

    # --------------------------------------------------

    @birthday.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def toggle(self, ctx: commands.Context):
        """Enable/Disable plugin"""

        self.enabled = not self.enabled

        await self._update_config()

        status = "Enabled" if self.enabled else "Disabled"

        await ctx.send(f"{status} birthday plugin.")

    # --------------------------------------------------

    @birthday.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def timezone(self, ctx: commands.Context, timezone_name: str):
        """Set timezone"""

        if timezone_name not in pytz.all_timezones:

            matches = get_close_matches(
                timezone_name,
                pytz.all_timezones
            )

            if matches:

                embed = discord.Embed(
                    color=0xEB3446,
                    description=(
                        "Did you mean:\n"
                        f"`{'`, `'.join(matches)}`"
                    )
                )

                await ctx.send(embed=embed)

            else:
                await ctx.send("Timezone not found.")

            return

        self.timezone = timezone_name

        await self._update_config()

        await ctx.send("Timezone updated.")


# --------------------------------------------------


async def setup(bot):
    await bot.add_cog(BirthdayPlugin(bot))
