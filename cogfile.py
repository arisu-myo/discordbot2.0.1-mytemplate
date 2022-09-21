from discord.ext import commands


class ReloadCog(commands.Cog):
    """リロード関係"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # .hybrid_command()は通常prefixコマンドとスラッシュコマンドが使用可能
    # スラッシュコマンドの場合は関数名のしたの文字列が説明として表示されます。
    @commands.hybrid_command()
    async def reload(self, ctx):
        """手動でリロードを行います。"""
        await self.bot.reload_extension("cogfile")

        # リロードが完了するとメッセージを表示、削除します。
        message = await ctx.send("reload success...")
        await message.delete()


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
