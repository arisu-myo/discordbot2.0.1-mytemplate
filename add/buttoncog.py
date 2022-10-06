from discord.ext import commands
import discord


class TestButton(discord.ui.Button):
    """
    buttonの本体とその動作部分
    """

    def __init__(self,
                 style: discord.ButtonStyle = discord.ButtonStyle.primary,
                 label: str = "button", disabled: bool = False,
                 custom_id=None, url=None, emoji=None, row=None):
        super().__init__(
            style=style, label=label, disabled=disabled,
            custom_id=custom_id, url=url, emoji=emoji, row=row
        )

    async def callback(self, interaction: discord.Interaction):
        """
        [self.style]が[primary]だった場合[danger]に変更
        [danger]だった場合[primary]変更
        """

        if self.style is discord.ButtonStyle.primary:
            self.label = "button danger"
            self.style = discord.ButtonStyle.danger

        elif self.style is discord.ButtonStyle.danger:
            self.label = "button primary"
            self.style = discord.ButtonStyle.primary

        # ボタンの変更の送信
        await interaction.response.edit_message(view=self.view)

        # 応答メッセージの送信
        await interaction.response.send_message("response message")


class ButtonCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def test_button(self, ctx, count: int = 1):
        view = discord.ui.View(timeout=None)
        for i in range(count):
            view.add_item(TestButton(
                label="button text",
                style=discord.ButtonStyle.primary
            ))

        # Viewはclassを使ってoverrideしてもOK
        await ctx.send(view=view)
