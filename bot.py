import asyncio  # 2.0.xで必須級に
import discord
# 一部環境ではいるかも？
# from discord import app_commands
from discord.ext import commands

TOKEN = "discordBOT token in str"
# Objectの頭文字は大文字


class MyBot(commands.Bot):
    """
    setup_hook,on_readyは任意名ではないことに注意
    """

    def __init__(self, prefix: str, intents: discord.Intents):
        super().__init__(command_prefix=prefix, intents=intents)
        self.my_guild = discord.Object("serverID in int")
        # 動かなかった場合アクティブしたら動くかも？
        # self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # スラッシュコマンド使えるようにしてると思われ・・・
        # self.tree.add_command(guild=MY_GUILD)
        self.tree.copy_global_to(guild=self.my_guild)
        await self.tree.sync(guild=self.my_guild)

    async def on_ready(self):
        print("起動完了...")

    async def on_command_error(self, ctx, error):
        await ctx.send(f"{error}")


async def main():
    intents = discord.Intents.all()
    intents.message_content = True
    bot = MyBot(prefix="$", intents=intents)
    # CogFileの初回読込
    await bot.load_extension("cogfile")

    async with bot:
        await bot.start(TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
