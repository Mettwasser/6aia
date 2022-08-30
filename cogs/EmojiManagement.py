import nextcord, aiohttp
from nextcord.ext import commands, application_checks
from main import bot_basic_color


async def get_bytes(link: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as resp:
            bytes = await resp.content.read()
    
    return bytes


class EmojiManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="emoji", description="emoji main command")
    @application_checks.has_guild_permissions(manage_emojis=True)
    @application_checks.guild_only()
    async def emoji(self, interaction: nextcord.Interaction):
        pass


    @emoji.subcommand(name="delete", description="Deletes an emoji by usage of the :emoji:.", inherit_hooks=True)
    async def delete(
    self, 
    interaction: nextcord.Interaction,
    emoji_str: str = nextcord.SlashOption(name="emoji", description="The link of the emoji."),
    ):

        if not emoji_str.startswith("<"):
            return await interaction.send("Please use a valid Discord emoji.")

        try:
            emoji = nextcord.PartialEmoji.from_str(emoji_str)
            await interaction.guild.delete_emoji(emoji)
        except nextcord.HTTPException:
            return await interaction.send("Could not find the emoji..", ephemeral=True)

        await interaction.send(embed=nextcord.Embed(title="Emoji removed!", description=f"`:{emoji.name}:` has been removed from this Server.", color=bot_basic_color))


    @emoji.subcommand(name="edit", description="Edits an emoji.", inherit_hooks=True)
    async def emoji_edit(
    self,
    interaction: nextcord.Interaction,
    emoji_str: str = nextcord.SlashOption(name="emoji", description="The emoji you want to edit."),
    new_name: str = nextcord.SlashOption(name="new-name", description="The name to overwrite with."),
    ):
        if not emoji_str.startswith("<"):
            return await interaction.send("Please use a valid Discord emoji.")

        try:
            emoji_id = nextcord.PartialEmoji.from_str(emoji_str).id
            emoji = await interaction.guild.fetch_emoji(emoji_id)
            await emoji.edit(name=new_name)
        except nextcord.HTTPException:
            return await interaction.send("I could not find the emoji or the new name is invalid..", ephemeral=True)

        await interaction.send(embed=nextcord.Embed(title="Emoji edited!", description=f"{str(emoji)} has been renamed to `:{new_name}:`.", color=bot_basic_color))


    @emoji.subcommand(name="steal", description="Steals an emoji by link or usage of the :emoji:.", inherit_hooks=True)
    async def steal(
    self, 
    interaction: nextcord.Interaction,
    ):
        pass


    @steal.subcommand(name="by-mention", description="Steals an emoji by usage of the :emoji:.", inherit_hooks=True)
    async def by_name(
    self, 
    interaction: nextcord.Interaction,
    emoji_str: str = nextcord.SlashOption(name="emoji", description="The emoji."),
    ):

        if not emoji_str.startswith("<"):
            return await interaction.send("Please use a valid Discord emoji.")

        try:
            emoji = nextcord.PartialEmoji.from_str(emoji_str)
            emoji._state = interaction._state
            bytes = await emoji.read()
        except nextcord.HTTPException:
            return await interaction.send("Could not find the emoji..", ephemeral=True)

        emoji = await interaction.guild.create_custom_emoji(name=emoji.name, image=bytes)
        await interaction.send(embed=nextcord.Embed(title="Emoji added!", description=f"{str(emoji)} added as `:{emoji.name}:`.", color=bot_basic_color))


    @steal.subcommand(name="by-link", description="Steals an emoji by link.", inherit_hooks=True)
    async def by_link(
    self,
    interaction: nextcord.Interaction,
    emoji_link: str = nextcord.SlashOption(name="emoji-link", description="The link of the emoji."),
    emoji_name: str = nextcord.SlashOption(name="emoji-name", description="The name the emoji will be saved as.")
    ):
        if not "https://cdn.discordapp.com/emojis/" in emoji_link:
            return await interaction.send("Please use a valid discord emoji link!")

        try:
            b = await get_bytes(emoji_link)
            emoji = await interaction.guild.create_custom_emoji(name=emoji_name, image=b)
            await interaction.send(embed=nextcord.Embed(title="Emoji added!", description=f"{str(emoji)} added as `:{emoji.name}:`.", color=bot_basic_color))
        except nextcord.HTTPException:
            return await interaction.send("I could not find the emoji or the name is invalid..", ephemeral=True)


    

    


def setup(bot):
    bot.add_cog(EmojiManager(bot))
