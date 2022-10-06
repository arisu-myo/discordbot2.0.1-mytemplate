# MyTemplate
discord.py 2.0.1を使ったcommands.Botを含むMyTemplate

## 各種バージョン情報
python 3.8

discord.py 2.0.1

## 変更情報
2022/10/06 Button例を追加しました。

2022/09/24 スラッシュコマンドが一部更新されていなかった問題ついて

●MY_GUILDがMyBot内に移動しました(file:bot.py)
```python
# 修正前
MY_GUILD = discord.Object("serverID in int")

# 修正後
def __init__(self,prefix:str,intents:discord.Intents):
    super().__init__(command_prefix=prefix,intents=intents)
    self.my_guild = discord.Object("serverID in int")
```
●tasksを使用したreloadへ追加、変更(file:cogfile.py)
```python
# 修正前
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


# 修正後
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
```

## コマンド等々...
ライブラリーのバージョン確認(一覧)
```bash
pip list
```
パッケージ（ライブラリーを指定してアップデート）
```bash
pip install -U <package-name>
```
このファイル構成での起動コマンド
```bash
python bot.py
```

## テスト仮想環境
pipenv


