import discord
from discord.ext import commands
import json
import os
from datetime import datetime

DATA_FILE = "emoticons.json"

def load_emoticons():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_emoticons(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class EmoticonFinder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # Add Emoticon
    # =========================
    @commands.hybrid_command(name="emoticonadd", description="Add a new emoticon.")
    async def emoticon_add(self, ctx, emoticon: str, *, description: str = "No description provided"):
        emoticons = load_emoticons()
        
        # Prevent duplicates
        if any(e["emoticon"] == emoticon for e in emoticons):
            return await ctx.send("This emoticon already exists!", ephemeral=True)

        # Assign ID
        new_id = len(emoticons)
        if new_id >= 100:
            return await ctx.send("Emoticon limit reached (100)!", ephemeral=True)

        new_entry = {
            "id": new_id,
            "emoticon": emoticon,
            "description": description,
            "added_by": ctx.author.name,
            "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        emoticons.append(new_entry)
        save_emoticons(emoticons)

        embed = discord.Embed(
            title="Emoticon Finder",
            description=f"**Output:**\n```\n{emoticon}\n```",
            color=0xFFFFFF
        )
        embed.add_field(name="Description:", value=description)
        embed.set_footer(text=f"{ctx.author.name} added this | {new_id} | This plugin was created by Ian :)")

        await ctx.send(embed=embed, ephemeral=True)

    # =========================
    # Delete Emoticon
    # =========================
    @commands.hybrid_command(name="emoticondel", description="Delete an emoticon by ID or text.")
    async def emoticon_del(self, ctx, target: str):
        emoticons = load_emoticons()

        # Try ID first
        deleted = None
        if target.isdigit():
            target_id = int(target)
            for e in emoticons:
                if e["id"] == target_id:
                    deleted = e
                    emoticons.remove(e)
                    break
        else:
            for e in emoticons:
                if e["emoticon"] == target:
                    deleted = e
                    emoticons.remove(e)
                    break

        if not deleted:
            return await ctx.send("Emoticon not found.", ephemeral=True)

        # Reindex IDs (0–100)
        for idx, e in enumerate(emoticons):
            e["id"] = idx
        save_emoticons(emoticons)

        await ctx.send(f"Deleted emoticon `{deleted['emoticon']}` (ID: {deleted['id']})", ephemeral=True)

    # =========================
    # List Emoticons
    # =========================
    @commands.hybrid_command(name="emoticonlist", description="List all added emoticons (oldest to newest).")
    async def emoticon_list(self, ctx):
        emoticons = load_emoticons()
        if not emoticons:
            return await ctx.send("No emoticons have been added yet.", ephemeral=True)

        # Sort by date
        emoticons.sort(key=lambda e: e["added_date"])
        lines = [f"{i+1}. `{e['emoticon']}`" for i, e in enumerate(emoticons)]
        output = "\n".join(lines)

        await ctx.send(f"**Emoticon List (Oldest → Newest):**\n{output}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(EmoticonFinder(bot))
