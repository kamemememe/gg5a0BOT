import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, Button, View
from discord import app_commands
from datetime import datetime

class AchievementModal(Modal):
    def __init__(self, bot, channel_id):
        super().__init__(title="実績投稿フォーム")
        self.bot = bot
        self.channel_id = channel_id

        # 入力フィールド
        self.product_name = TextInput(label="商品名", placeholder="商品名を入力してください", required=True)
        self.opinion = TextInput(label="感想", placeholder="感想を入力してください", required=True)
        self.rating = TextInput(label="評価 (1-5)", placeholder="1から5の評価を入力してください", required=True)

        # 入力フィールドを追加
        self.add_item(self.product_name)
        self.add_item(self.opinion)
        self.add_item(self.rating)

    async def on_submit(self, interaction: discord.Interaction):
        # チャンネルの取得
        channel = self.bot.get_channel(self.channel_id)
        
        if not channel:
            await interaction.response.send_message("指定されたチャンネルが見つかりません。", ephemeral=True)
            return
        
        # ユーザーのアイコンとID、日時の取得
        user_avatar = interaction.user.avatar.url
        user_id = interaction.user.id
        post_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 評価を星の絵文字に変換
        try:
            rating_value = int(self.rating.value)
            if 1 <= rating_value <= 5:
                rating_stars = '⭐' * rating_value
            else:
                rating_stars = "評価は1から5の間で入力してください。"
        except ValueError:
            rating_stars = "評価は数字で入力してください。"

        # Embed作成
        embed = discord.Embed(
            title="実績投稿",
            description=f"**商品名：** {self.product_name.value}\n**感想：** {self.opinion.value}",
            color=discord.Color.blue()
        )
        embed.add_field(name="評価", value=rating_stars)
        embed.add_field(name="投稿者", value=f"<@{user_id}>")  # 投稿者を @ID の形式に変更
        embed.add_field(name="投稿日時", value=post_time)
        embed.set_thumbnail(url=user_avatar)  # ユーザーアイコンを大きく表示

        # 投稿処理
        await channel.send(embed=embed)
        await interaction.response.send_message("実績が正常に投稿されました！", ephemeral=True)

        # 実績数増加機能を一時的に無効化
        # ここに実績数を増加するコードがあった場合、今は実行されません

class AchievementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="実績投稿パネル", description="実績投稿パネルを設置します。")
    async def achievement_post(self, interaction: discord.Interaction):
        # Embedでタイトル、説明、ボタンを表示
        embed = discord.Embed(
            title="実績投稿パネル",
            description="下のボタンから入力し投稿してください！",
            color=discord.Color.green()
        )
        button = Button(label="実績を投稿する！", style=discord.ButtonStyle.primary)

        # ボタンが押されたときにモーダルを表示
        async def button_callback(interaction: discord.Interaction):
            modal = AchievementModal(self.bot, channel_id=1335308393988227154)  # チャンネルIDを直接指定
            await interaction.response.send_modal(modal)

        button.callback = button_callback
        view = View()
        view.add_item(button)

        # ユーザーにボタンとともにEmbedを送信
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    # 非同期で add_cog を呼び出す
    await bot.add_cog(AchievementCog(bot))
