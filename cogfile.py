
from discord.ext import commands, tasks


class ReloadCog(commands.Cog):
    """リロード関係"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reload_check = False

    @tasks.loop(count=1)
    async def now_load(self, ctx, old_message):
        """
        リロード本体
        ctx:ctx object
        old_message:command in send message object
        """

        self.reload_check = True

        try:
            # スラッシュコマンドを更新する
            self.bot.tree.copy_global_to(guild=self.bot.my_guild)
            await self.bot.tree.sync(guild=self.bot.my_guild)

            # コマンドからctxを取得しメッセージを送信する
            message = await ctx.send("処理が終了しました")
            await old_message.delete()
            await message.delete()

        except Exception as e:
            ctx.send(e)

        self.reload_check = False

    # .hybrid_command()は通常prefixコマンドとスラッシュコマンドが使用可能
    # スラッシュコマンドの場合は関数名のしたの文字列が説明として表示されます。

    @commands.hybrid_command()
    async def reload(self, ctx):
        """手動でリロードを行います。"""

        # 本体稼働中もコマンドが使用の為重複防止策
        if self.reload_check:
            return

        await self.bot.reload_extension("cogfile")
        message = await ctx.send("更新処理を開始します")
        self.now_load.start(ctx, message)


class TestCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def test(self, ctx):
        await ctx.send("test success...")


async def setup(bot: commands.Bot):
    """
    ※注意:この関数がBOT本体に読み込まれます\n
    新しくCogを追加した場合この関数に追加してください
    """
    await bot.add_cog(ReloadCog(bot))
    await bot.add_cog(TestCog(bot))
