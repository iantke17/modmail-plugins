import discord
from discord.ext import commands
from discord.ui import Modal, InputText
import datetime

# === CONFIGURATION ===
ALLOWED_ROLE_ID = 123456789  # Role allowed to use commands
SHIFT_CHANNEL_ID = 1418971833775947867  # Channel where shifts are posted

class ShiftModal(Modal):
    def __init__(self, bot, test_mode=False):
        super().__init__(title="Create a New Shift")
        self.bot = bot
        self.test_mode = test_mode

        self.add_item(InputText(label="Host Roblox Username", placeholder="e.g. CoolBakerIan"))
        self.add_item(InputText(label="Cohost Roblox Username (optional)", required=False))
        self.add_item(InputText(label="Description", style=discord.InputTextStyle.long, required=False))
        self.add_item(InputText(label="Date (DD/MM/YYYY)", placeholder="e.g. 15/10/2025"))
        self.add_item(InputText(label="Time (HH:MM in 24h format)", placeholder="e.g. 16:00"))

    async def callback(self, interaction: discord.Interaction):
        try:
            host = self.children[0].value.strip()
            cohost = self.children[1].value.strip() or "None"
            desc = self.children[2].value.strip() or "No description provided."
            date_str = self.children[3].value.strip()
            time_str = self.children[4].value.strip()

            # Parse date and time
            dt_obj = datetime.datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
            timestamp = int(dt_obj.timestamp())
            weekday = dt_obj.strftime("%A")

            # Roblox links
            host_url = f"https://www.roblox.com/search/users?keyword={host}"
            cohost_url = f"https://www.roblox.com/search/users?keyword={cohost}" if cohost != "None" else "None"

            # Shift message
            msg_content = (
                f"<@&{ALLOWED_ROLE_ID}>\n"
                f"🍞 **New Bakery Shift Starting Soon!**\n"
                f"**Host:** [{host}]({host_url})\n"
                f"**Cohost:** [{cohost}]({cohost_url})\n"
                f"**Description:** {desc}\n\n"
                f"**Date:** <t:{timestamp}:D> ({weekday})\n"
                f"**Time:** <t:{timestamp}:t>\n"
                f"**Place:** [www.roblox.com](https://www.roblox.com)\n\n"
                f"All <@&{ALLOWED_ROLE_ID}> attending, please come in 30 minutes earlier!"
            )

            channel = self.bot.get_channel(SHIFT_CHANNEL_ID)
            if not channel:
                await interaction.response.send_message("Shift channel not found.", ephemeral=True)
                return

            # Test mode = don’t ping role
            if self.test_mode:
                msg_content = msg_content.replace(f"<@&{ALLOWED_ROLE_ID}>", "`@Shift Ping`")

            sent_msg = await channel.send(msg_content)
            self.bot.last_shift_message_id = sent_msg.id

            await interaction.response.send_message("✅ Shift announcement sent successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)


class ShiftManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_shift_message_id = None

    async def cog_check(self, ctx):
        """Restrict commands to specific role."""
        return any(role.id == ALLOWED_ROLE_ID for role in ctx.author.roles)

    @commands.command(name="createshift")
    async def create_shift(self, ctx):
        """Create a new shift announcement."""
        modal = ShiftModal(self.bot, test_mode=False)
        await ctx.send_modal(modal)

    @commands.command(name="testshift")
    async def test_shift(self, ctx):
        """Send a test shift message (no ping)."""
        modal = ShiftModal(self.bot, test_mode=True)
        await ctx.send_modal(modal)

    @commands.command(name="shiftcancel")
    async def cancel_shift(self, ctx):
        """Cancel the last posted shift."""
        if not hasattr(self.bot, "last_shift_message_id") or not self.bot.last_shift_message_id:
            await ctx.send("No recent shift message found to cancel.")
            return

        channel = self.bot.get_channel(SHIFT_CHANNEL_ID)
        if not channel:
            await ctx.send("Shift channel not found.")
            return

        try:
            msg = await channel.fetch_message(self.bot.last_shift_message_id)
            await msg.delete()
            self.bot.last_shift_message_id = None
            await ctx.send("✅ Last shift message has been cancelled.")
        except discord.NotFound:
            await ctx.send("Message not found — it may have been deleted already.")
        except Exception as e:
            await ctx.send(f"Error deleting message: {e}")


async def setup(bot):
    await bot.add_cog(ShiftManager(bot))

