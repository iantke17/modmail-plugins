import discord
from discord.ext import commands
import aiohttp
import json

from core import checks
from core.models import PermissionLevel


class AIChatbot(commands.Cog):
    """AI Chatbot with optional memory."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.plugin_db.get_partition(self)
        self.bot_prefix = "@botping"  # Required custom prefix

    async def get_key(self):
        return await self.config.find_one({"_id": "api_key"})

    async def get_memory_state(self):
        mem = await self.config.find_one({"_id": "memory"})
        if mem is None:
            # Default ON
            await self.config.update_one(
                {"_id": "memory"},
                {"$set": {"enabled": True}},
                upsert=True
            )
            return True
        return mem.get("enabled", True)

    async def update_memory_state(self, value: bool):
        await self.config.update_one(
            {"_id": "memory"},
            {"$set": {"enabled": value}},
            upsert=True
        )

    def cog_check(self, ctx):
        # Only respond when prefix matches "@botping"
        return ctx.prefix == self.bot_prefix

    #
    # COMMAND: aisetkey  (Owner only)
    #
    @commands.command(name="aisetkey")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def aisetkey(self, ctx, *, key: str):
        """Set the model API key."""
        await self.config.update_one(
            {"_id": "api_key"},
            {"$set": {"value": key}},
            upsert=True
        )
        await ctx.reply("API key saved.", mention_author=False)

    #
    # COMMAND: airemember (toggle)
    #
    @commands.command(name="airemember")
    async def airemember(self, ctx):
        """Toggle AI memory ON/OFF."""
        enabled = await self.get_memory_state()
        new_value = not enabled
        await self.update_memory_state(new_value)

        state = "enabled" if new_value else "disabled"
        await ctx.reply(f"AI memory {state}.", mention_author=False)

    #
    # Internal: Generate AI response
    #
    async def generate_ai(self, prompt: str, key: str, memory_enabled: bool):
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        messages = []

        # If memory enabled, include last memory blob
        if memory_enabled:
            mem = await self.config.find_one({"_id": "memory_blob"})
            if mem:
                messages.append({"role": "system", "content": mem["value"]})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.7
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return f"API error {resp.status}: {await resp.text()}"

                data = await resp.json()
                reply = data["choices"][0]["message"]["content"]

                # Save memory if enabled
                if memory_enabled:
                    await self.config.update_one(
                        {"_id": "memory_blob"},
                        {"$set": {"value": reply}},
                        upsert=True
                    )

                return reply


async def setup(bot):
    await bot.add_cog(AIChatbot(bot))
