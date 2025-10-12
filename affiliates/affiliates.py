import discord
from discord.ext import commands
import json
import os

# ===== CONFIG =====
ALLOWED_ROLES = [123456789012345678, 987654321098765432]  # Replace with your actual role IDs
AFFILIATE_FILE = "affiliates.json"  # JSON backup file path
AFFILIATE_LIST_CHANNEL_ID = 111111111111111111  # Replace with your #affiliates-list channel ID
PARTNER_LOGS_CHANNEL_ID = 222222222222222222    # Replace with your #partner-logs channel ID
# ==================

class Affiliates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = {}
        self.load_data()

    # ========== Helper Functions ==========

    def load_data(self):
        """Load affiliate data from JSON backup"""
        if os.path.exists(AFFILIATE_FILE):
            with open(AFFILIATE_FILE, "r") as f:
                try:
                    self.db = json.load(f)
                except json.JSONDecodeError:
                    self.db = {}
        else:
            self.db = {}

    def save_data(self):
        """Save affiliate data to JSON backup"""
        with open(AFFILIATE_FILE, "w") as f:
            json.dump(self.db, f, indent=4)

    async def has_permission(self, ctx):
        """Check if the user has at least one allowed role (by ID)"""
        return any(role.id in ALLOWED_ROLES for role in ctx.author.roles)

    async def update_affiliate_list(self, channel):
        """Auto-update the affiliate list channel"""
        if not channel:
            return

        title = "## Jimmy John's | Affiliates List\n"
        body = ""

        for aff in self.db.values():
            reps = ", ".join(aff['reps'])
            body += f"**{aff['affiliate']} | {reps}**\n"

        body += "\n*This list will auto-updates when we have new affiliates*"

        # Delete previous bot messages (keep list clean)
        async for msg in channel.history(limit=10):
            if msg.author == self.bot.user:
                await msg.delete()

        await channel.send(f"{title}{body}")

    # ========== Commands ==========

    @commands.slash_command(name="register", description="Register a new affiliate")
    async def register(self, ctx, affiliate_name: str, reps: str):
        """Register a new affiliate"""
        if not await self.has_permission(ctx):
            return await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)

        registered_by = ctx.author.display_name
        reps_list = [r.strip() for r in reps.split(",")]

        self.db[affiliate_name.lower()] = {
            "affiliate": affiliate_name,
            "reps": reps_list,
            "registered_by": registered_by
        }
        self.save_data()

        # Fetch channels by ID
        log_channel = self.bot.get_channel(PARTNER_LOGS_CHANNEL_ID)
        list_channel = self.bot.get_channel(AFFILIATE_LIST_CHANNEL_ID)

        # Log the registration
        if log_channel:
            await log_channel.send(
                f"**{affiliate_name}**\n"
                f"Name of Affiliate: {affiliate_name}\n"
                f"Affiliate Representatives: {', '.join(reps_list)}\n"
                f"Person In Charge: {registered_by}"
            )

        # Update affiliate list
        await self.update_affiliate_list(list_channel)
        await ctx.respond(f"✅ {affiliate_name} registered successfully!")

    @commands.slash_command(name="unregister", description="Remove an affiliate")
    async def unregister(self, ctx, affiliate_name: str):
        """Unregister an affiliate"""
        if not await self.has_permission(ctx):
            return await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)

        if affiliate_name.lower() not in self.db:
            return await ctx.respond("❌ Affiliate not found!", ephemeral=True)

        del self.db[affiliate_name.lower()]
        self.save_data()

        list_channel = self.bot.get_channel(AFFILIATE_LIST_CHANNEL_ID)
        await self.update_affiliate_list(list_channel)

        await ctx.respond(f"✅ {affiliate_name} removed successfully!")

    @commands.slash_command(name="listaffiliates", description="View all registered affiliates")
    async def listaffiliates(self, ctx):
        """Show all affiliates"""
        if not self.db:
            return await ctx.respond("📭 No affiliates registered yet.")

        body = "\n".join([f"**{a['affiliate']} | {', '.join(a['reps'])}**" for a in self.db.values()])
        await ctx.respond(f"## Current Affiliates\n{body}")

def setup(bot):
    bot.add_cog(Affiliates(bot))
