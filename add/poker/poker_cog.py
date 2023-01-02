from discord.ext import commands, tasks
import discord
import cv2
import uuid
import hashlib

import random


class EntryError(Exception):
    def __init__(self, *args: object):
        args = ("\n現在のセッションではエントリーできませんでした",)
        self.args = args


class EntryRepetitionError(Exception):
    def __init__(self, *args: object):
        args = ("\nすでにエントリーしているUserと名前が被っていますエントリーできません",)
        self.args = args


class GameStartError(Exception):
    def __init__(self, *args: object):
        args = ("\nセッション進行中です。新しいゲームはブロックされました。",)
        self.args = args


class NonActiveError(Exception):
    def __init__(self, *args: object):
        args = ("\n現在このコマンドは無効化されています。",)
        self.args = args


def create_cards(is_joker: bool = False):
    """
    # トランプカードのリストを作成してそれを返します。

    各イニシャル読み替え
    :`S = スペード`
    :`H = ハート`
    :`D = ダイヤ`
    :`C = クローバー`
    """
    all_list: list[str] = []
    for card_acronym in ("S", "H", "D", "C"):
        for i in range(13):
            all_list.append(
                f"{card_acronym}{i + 1}"
            )

    if is_joker:
        all_list.append("J")

    return all_list


class Judge:
    def __init__(self, card_list):

        self.card_list = card_list

        # KとAを含む順番として認められる配列
        self.loyal_list: list[int] = [1, 10, 11, 12, 13]

    def _sort(self, old_list: list = None):
        """カード配列をイニシャルを排除した数字をソートして配列として返します"""
        if old_list is None:
            old_list = self.card_list

        return sorted([int(item.replace(item[0], "")) for item in old_list])

    def _flash(self):
        """5枚のカード全てのイニシャルが同じか調べます"""
        for i in range(5):
            if not self.card_list[0][0] == self.card_list[i][0]:
                return False

        return True

    def _loyal(self):
        """[10, J, Q, K, A]の配列を判定します"""
        new_list = self._sort(self.card_list)

        if self.loyal_list == new_list:
            return True
        else:
            return False

    def _straight(self):
        """ストレートを判定します"""
        new_list = self._sort(self.card_list)

        for i in range(5):
            if not i == 0:
                if not new_list[i] == new_list[0] + i:
                    return False

        return True

    def _pair(self):
        """フラッシュ、ストレート以外の役を判定します"""
        new_list = self._sort(self.card_list)

        pair_dict = {}
        for item in new_list:
            if str(item) in pair_dict.keys():
                pair_dict[str(item)].append(item)
            else:
                pair_dict[str(item)] = [item]

        def dict_item3():
            role_word = "two_pair"
            for key in pair_dict.keys():
                if len(pair_dict[key]) == 3:
                    role_word = "3card"
            return role_word

        def dict_item2():
            role_word = "full_house"
            for key in pair_dict.keys():
                if len(pair_dict[key]) == 4:
                    role_word = "4card"
            return role_word

        judge_pair = {
            "5": "no_pair",
            "4": "one_pair",
            "3": dict_item3(),
            "2": dict_item2(),
        }

        return judge_pair[str(len(pair_dict))]

    def role(self):
        """役判定を行いをの役の名前を返します"""
        if self._flash() and self._loyal():
            return "loyal_straight_flash"

        if self._flash() and self._straight():
            return "straight_flash"

        if self._flash():
            return "flash"

        if self._straight():
            return "straight"

        return self._pair()

    def score(self):
        """役判定を行い役のスコアを返します(数字が大きい物が優位です）"""
        score_dict = {
            "loyal_straight_flash": 10,
            "straight_flash": 9, "4card": 8,
            "full_house": 7, "flash": 6,
            "straight": 5, "3card": 4,
            "two_pair": 3, "one_pair": 2, "no_pair": 1,
        }

        return score_dict[self.role()]


class Player:
    """Playersにインスタンスされている為呼び出し禁止"""

    def __init__(self, **kwargs):
        self.user_name: str = kwargs["user_name"]
        self.user_id: int = kwargs["user_id"]
        self.user_cards: list[str] = []
        self.role: str = ""
        self.score: int = 0

    def __str__(self):
        return self.user_name

    def __len__(self):
        return len(self.user_cards)

    def judge(self):
        judge = Judge(self.user_cards)
        self.role = judge.role()
        self.score = judge.score()


class Players:

    def __init__(self):
        self.users: dict[str, Player] = {}

    def __getitem__(self, key):
        return self.users[key]

    def _repetition(self, name):
        """既存User名と重複があればエラーを返します"""

        self._over_entry()  # 5人以上はお断り

        for user in self.users:
            if user == name:
                raise EntryRepetitionError()

    def _over_entry(self):
        """すでにエントリーUserが上限の5人場合エラーを返す"""
        if 5 == self.count:
            raise EntryError()

    def create(self, name: str, id: int):
        self._repetition(name)
        self.users[name] = Player(user_name=name, user_id=id)

    def count(self):
        return len(self.users)

    def names(self):
        user_list = []
        for user in self.users.keys():
            user_list.append(user)

        return user_list

    def all_judgement(self):

        for user in self.users.keys():
            self.users[user].judge()


class CheckAction:
    def __init__(self):
        self.active_new_game = False
        self.active_entry = False

    def new_game(self):
        return "new_game"

    def entry_game(self):
        return "entry"

    def entry_stop(self):
        return "entry_stop"

    def next(self, stage: str):
        if stage == "new_game":
            self.active_new_game = True

        if stage == "entry_stop":
            self.active_entry = True

    def check(self, stage: str):
        if stage == "new_game":
            return self.active_new_game

        if stage == "entry" or stage == "entry_stop":
            return self.active_entry


class PokerBase:

    def __init__(self):

        self.all_card: list[str] = []  # 山札
        self.on_button_count: int = 0  # 確定ボタン押された数
        self.change_cards: dict[str, list[str]] = {}  # 変更したいカード
        self.users = Players()

    def test_draw(self):

        test_yamahuda = create_cards()
        test_motihuda = []

        for i in range(5):
            card = random.choice(test_yamahuda)
            test_motihuda.append(card)
            test_yamahuda.remove(card)

        return test_motihuda

    def start_draw(self, user: str = None):
        for i in range(5):
            card = random.choice(self.all_card)
            self.users[user].user_cards.append(card)
            self.all_card.remove(card)

    async def change_draw(self, user: str):
        for remove_card in self.change_cards[user]:
            self.users[user].user_cards.remove(remove_card)

        for i in range(5 - len(self.users[user])):
            card = random.choice(self.all_card)
            self.users[user].user_cards.append(card)
            self.all_card.remove(card)


class PokerBackEnd(PokerBase):
    def __init__(self):
        super().__init__()
        self.action = CheckAction()

    def new_game(self, user: str, id: int, is_entry: bool = True):
        if self.action.check(self.action.new_game()):
            raise GameStartError()

        self.all_card = create_cards()

        if is_entry:
            self.entry_game(user, id)

        self.action.next(self.action.new_game())

    def entry_game(self, user: str, id: int):
        if self.action.check(self.action.entry_game()):
            raise EntryError()

        self.users.create(user, id)
        self.start_draw(user)

        self.action.next(self.action.entry_game())

    def entry_stop(self):
        self.action.check(self.action.entry_stop())
        self.action.next(self.action.entry_stop())

    def end_game(self):

        self.users.all_judgement()


class SelectButton(discord.ui.Button):
    def __init__(
        self, style: discord.ButtonStyle = discord.ButtonStyle.primary,
        label: str = "button", disabled: bool = False, custom_id=None,
        url=None, emoji=None, row=None, poker: PokerBackEnd = None, user: str = None,
        ctx: commands.context.Context = None, on_type: str = "card"
    ):
        super().__init__(
            style=style, label=label, disabled=disabled,
            custom_id=custom_id, url=url, emoji=emoji, row=row
        )

        self.poker = poker
        self.ctx = ctx
        self.on_type = on_type
        self.user = user
        self.user_id = ctx.author.id

    async def callback(self, interaction: discord.Interaction):
        try:
            if not self.user_id == interaction.user.id:
                await interaction.response.edit_message(
                    view=self.view
                )
                return

            if self.on_type == "select":
                if self.label == "確定":
                    self.poker.on_button_count += 1
                    self.style = discord.ButtonStyle.danger
                    self.label = "キャンセル"
                else:
                    self.poker.on_button_count -= 1
                    self.style = discord.ButtonStyle.primary
                    self.label = "確定"

            elif self.on_type == "card":
                if self.style is discord.ButtonStyle.primary:
                    self.poker.change_cards[self.user].append(self.label)
                    self.style = discord.ButtonStyle.danger
                else:
                    self.poker.change_cards[self.user].remove(self.label)
                    self.style = discord.ButtonStyle.primary

            await interaction.response.edit_message(view=self.view)

        except Exception as error:
            print(error)


class PokerCog(commands.Cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot
        self.poker = PokerBackEnd()

    def create_image(self, user=None):
        _cv2_list = []

        def create_name():
            name = str(uuid.uuid4()).encode()
            name = hashlib.md5(name).hexdigest()
            return name

        if user is None:
            # テスト用の画像生成
            _card_path = "./img/create/test_img.png"
            for path in self.poker.test_draw():
                _cv2_list.append(
                    cv2.imread(f"./img/{path}.png")
                )

        elif user is not None:
            # 本番用の画像生成

            cards = self.poker.users[user]

            _fname = create_name()
            _card_path = f"./img/create/{_fname}.png"
            for path in cards.user_cards:
                _cv2_list.append(
                    cv2.imread(f"./img/{path}.png")
                )

        else:
            raise

        _img = cv2.hconcat(_cv2_list)
        cv2.imwrite(_card_path, _img)
        return _card_path

    @tasks.loop(seconds=0.5, count=1)
    async def main_show(self, ctx):
        self.loop_check.start(ctx)
        for user in self.poker.users.names():

            # create embed and image file
            fname = f"{uuid.uuid4()}.png"
            file = discord.File(
                fp=self.create_image(user=user),
                filename=fname, spoiler=False
            )
            embed = discord.Embed(title=f"{user}さんのカード")
            embed.set_image(url=f"attachment://{fname}")

            # add buttons
            view = discord.ui.View(timeout=180)

            for item in self.poker.users[user].user_cards:
                view.add_item(SelectButton(
                    label=item, poker=self.poker, ctx=ctx, user=user,
                ))

            view.add_item(SelectButton(
                label="確定", poker=self.poker, ctx=ctx, on_type="select",
                user=user
            ))

            self.poker.change_cards[user] = []

            await ctx.send(view=view, file=file, embed=embed)

    @tasks.loop(seconds=0.5)
    async def loop_check(self, ctx):
        if self.poker.on_button_count == self.poker.users.count():
            for user in self.poker.users.users:
                await self.poker.change_draw(user)
            self.poker.on_button_count = 0
            self.main_show.start(ctx)
            self.loop_check.stop()

        if len(self.poker.all_card) > 5 * self.poker.users.count():

            self.poker.users.all_judgement()

            for user in self.poker.users.users:
                await ctx.send(
                    "全Userがカードを全て交換した場合カードがなくなりますので" +
                    "、終了処理を開始します。")
                await ctx.send(
                    f"{user}さん：\n" +
                    f" ロール:{self.poker.users[user].role}\n" +
                    f" スコア:{self.poker.users[user].score}"
                )

            await ctx.send(
                "BOTを更新して初期化処理を開始します..."
            )
            self.loop_check.stop()

            await self.bot.reload_extension("poker_cog")
            await ctx.send("正常に初期化処理を完了しました...")

    @commands.hybrid_command()
    async def test_draw(self, ctx: commands.context.Context):
        fname = "test.png"

        file = discord.File(
            fp=self.create_image(),
            filename=fname,
            spoiler=False
        )

        embed = discord.Embed(title=f"{ctx.author.name}さんのカード")
        embed.set_image(url=f"attachment://{fname}")

        await ctx.send(file=file, embed=embed)

    # main poker game
    @commands.hybrid_command()
    async def new_poker_game(self, ctx: commands.context.Context):
        self.poker.new_game(ctx.author, ctx.author)
        user_name = ctx.author
        user_count = self.poker.users.count()

        await ctx.send(
            f"{user_name}さんがNewGamePokerのアクションを開始しました\n" +
            "`/entry`を入力してゲームに参加してください。" +
            f"残り最大{5 - user_count}人がエントリー可能です"
        )

    @commands.hybrid_command()
    async def entry(self, ctx: commands.context.Context, user=None):
        if user is None:
            user = ctx.author

        self.poker.entry_game(user, ctx.author.id)
        await ctx.send(
            f"{user}さんがエントリーしました。\n" +
            f"最大残り{5 - self.poker.users.count()}人がエントリー可能です."
        )

    @commands.hybrid_command()
    async def entry_stop(self, ctx):
        await ctx.send("エントリーが締め切られました")
        self.poker.entry_stop()
        self.main_show.start(ctx)

    @commands.hybrid_command()
    async def judge(self, ctx):

        self.poker.users.all_judgement()

        for user in self.poker.users.users:
            await ctx.send(
                f"{user}さん：" +
                f" ロール:{self.poker.users[user].role}" +
                f" スコア:{self.poker.users[user].score}"
            )

        await ctx.send(
            "BOTを更新して初期化処理を開始します..."
        )

        await self.bot.reload_extension("poker_cog")
        await ctx.send("正常に初期化処理を完了しました...")


async def setup(bot: commands.Bot):
    """
    ※注意:この関数がBOT本体に読み込まれます\n
    新しくCogを追加した場合この関数に追加してください
    """

    await bot.add_cog(PokerCog(bot))
    # new Cog class add ...
