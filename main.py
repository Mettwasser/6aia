import os, nextcord, dotenv
from nextcord.ext import commands

dotenv.load_dotenv()

bot_basic_color = 0x00A8FF

intents = nextcord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = False


bot = commands.Bot(
    intents=intents,
    status=nextcord.Status.online,
    activity=nextcord.Game("/help"),
    owner_id=350749990681051149,
)
bot.remove_command("help")


# On Ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# Overwrite default error handler
# @bot.event
# async def on_application_command_error(interaction: nextcord.Interaction, error):
#     pass


"""
Load Cogs
"""
for filename in os.listdir(R"./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")


# Run Bot
if __name__ == "__main__":
    bot.run(os.getenv("TESTTOKEN"))
