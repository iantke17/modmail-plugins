    @emoji.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def export(self, ctx):
        """Export all emojis to a zip file"""
        if not ctx.guild.emojis:
            raise commands.BadArgument("This server has no custom emojis to export.")

        await ctx.send("Generating zip file...")
        async with ctx.typing():
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "emojis.zip")
                
                # Create the zip file context
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for e in ctx.guild.emojis:
                        try:
                            extension = "gif" if e.animated else "png"
                            # Download emoji data directly into memory
                            emoji_bytes = await e.url.read()
                            # Write bytes straight to the zip without making temporary files
                            zipf.writestr(f"{e.name}.{extension}", emoji_bytes)
                        except Exception as err:
                            # Prevents one broken emoji from crashing the entire export
                            print(f"Failed to export emoji {e.name}: {err}")
                            continue

                # Send the completed zip file
                await ctx.send(file=discord.File(zip_path))
