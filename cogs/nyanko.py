import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput, Select
import asyncio
import json
import datetime
import os
import logging
from colorlog import ColoredFormatter

# ログ設定
logger = logging.getLogger(__name__)

# ログフォーマットの設定
log_formatter = ColoredFormatter(
    "%(log_color)s[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)

# ログハンドラの設定
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

# チケット情報をファイルから読み込む
def load_ticket_info():
    if os.path.exists("ticket_info.json"):
        with open("ticket_info.json", "r") as f:
            return [json.loads(line) for line in f.readlines()]
    return []

# チケット情報をファイルに保存する
def save_ticket_info(ticket_info):
    with open("ticket_info.json", "a") as f:
        json.dump(ticket_info, f)
        f.write("\n")

# チケット情報を削除する
def remove_ticket_info(channel_id):
    ticket_info = load_ticket_info()
    ticket_info = [ticket for ticket in ticket_info if ticket["channel_id"] != channel_id]
    
    # 更新された情報を保存
    with open("ticket_info.json", "w") as f:
        for ticket in ticket_info:
            json.dump(ticket, f)
            f.write("\n")

# チケットフォームのモーダル
class NyankoTicketModal(Modal):
    def __init__(self, payment_method=None, ticket_button=None):
        super().__init__(title="にゃんこ代行フォーム")
        self.payment_method = payment_method
        self.ticket_button = ticket_button
        
        self.add_item(TextInput(label="代行内容", placeholder="例：猫缶, XP", custom_id="content"))
        self.add_item(TextInput(label="引き継ぎコード", placeholder="例：abcd1234", custom_id="transfer_code"))
        self.add_item(TextInput(label="認証番号", placeholder="例：1234", custom_id="auth_code"))

        if self.payment_method == 'PayPay':
            self.add_item(TextInput(label="支払いリンク", placeholder="例：https://pay.paypay.ne.jp/xxxxx", custom_id="payment_link"))
        elif self.payment_method == 'Google Play':
            self.add_item(TextInput(label="支払いコード", placeholder="例：ABCD1234EFGH", custom_id="payment_code"))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            content = {item.custom_id: item.value for item in self.children}
            user = interaction.user

            delegate_content = content['content']
            transfer_code = content['transfer_code']
            auth_code = content['auth_code']
            payment_method = self.payment_method
            payment_info = content.get('payment_link', content.get('payment_code', ''))

            guild_id = interaction.guild.id
            category_id = {
                1145733173167259739: 1270580967240892497,
                1330566797937610984: 1338449960634552350,
                1305183974808617043: 1340230837303640115
            }.get(guild_id)

            category = discord.utils.get(interaction.guild.categories, id=category_id)
            if not category:
                category = await interaction.guild.create_category("代行チケット")

            channel = await interaction.guild.create_text_channel(f"にゃんこ┊︎{user.name}", category=category)

            embed = discord.Embed(title="にゃんこ代行フォーム", description="以下の内容が送信されました。", color=discord.Color.green())
            embed.add_field(name="代行内容", value=f"```{delegate_content}```", inline=False)
            embed.add_field(name="引き継ぎコード", value=f"```{transfer_code}```", inline=False)
            embed.add_field(name="認証番号", value=f"```{auth_code}```", inline=False)
            embed.add_field(name="支払い方法", value=f"```{payment_method}```", inline=False)
            embed.add_field(name="支払い情報", value=f"```{payment_info}```", inline=False)
            embed.set_footer(text="")

            await channel.send(f"{user.mention}", embed=embed)

            delete_button = Button(label="チケット🎫を削除する", style=discord.ButtonStyle.danger)

            async def delete_button_callback(interaction: discord.Interaction):
                confirm_button = Button(label="削除を確定", style=discord.ButtonStyle.danger)
                cancel_button = Button(label="キャンセル", style=discord.ButtonStyle.secondary)

                async def confirm_button_callback(interaction: discord.Interaction):
                    await channel.send(embed=discord.Embed(title="チャンネル削除の確認", description="このチャンネルは10秒後に削除されます。", color=discord.Color.red()))
                    await asyncio.sleep(10)
                    await channel.delete()

                    # チケット情報削除
                    remove_ticket_info(channel.id)

                    # チケット削除のログ
                    logger.info(f"チケットが削除されました: チャンネルID {channel.id} ユーザーID {user.id} 削除日時 {datetime.datetime.utcnow().isoformat()}")

                async def cancel_button_callback(interaction: discord.Interaction):
                    await interaction.response.send_message("チケット削除をキャンセルしました。", ephemeral=True)

                confirm_button.callback = confirm_button_callback
                cancel_button.callback = cancel_button_callback
                confirm_view = View()
                confirm_view.add_item(confirm_button)
                confirm_view.add_item(cancel_button)

                await interaction.response.send_message("削除を確定する場合は、下のボタンを押してください。", view=confirm_view, ephemeral=True)

            delete_button.callback = delete_button_callback
            view = View()
            view.add_item(delete_button)

            await channel.send("このチャンネルを削除する場合は、下のボタンを押してください。", view=view)

            # 作成者のみにチャンネル案内
            if not interaction.response.is_done():
                await interaction.response.send_message(f"チケットが作成されました！\n{channel.mention}", ephemeral=True)

            # チケット情報を保存する際に現在の時刻を保存
            ticket_info = {
                'channel_id': channel.id,
                'user_id': user.id,
                'created_at': datetime.datetime.utcnow().isoformat(),  # UTCで保存
                'view_data': {
                    'delete_button': delete_button.label,  # ボタン情報を保存
                    'delete_button_callback': delete_button.callback.__name__
                }
            }

            # チケット情報をファイルに保存
            save_ticket_info(ticket_info)

            # チケット保存のログ
            logger.info(f"チケット情報が保存されました: チャンネルID {channel.id} ユーザーID {user.id} 作成日時 {ticket_info['created_at']}")

            # フォーム送信後にボタンを無効化
            if self.ticket_button:
                self.ticket_button.disabled = True
                await interaction.message.edit(view=self.ticket_button.view)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"エラーが発生しました: {str(e)}", ephemeral=True)

# `NyankoTicketCog` クラスの定義を追加
class NyankoTicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # チケット情報の読み込み
        self.load_existing_tickets()

    # 既存のチケット情報を読み込む
    def load_existing_tickets(self):
        existing_tickets = load_ticket_info()
        for ticket in existing_tickets:
            # 保存されたチケット情報に基づいて削除ボタンやチャンネルの復元
            logger.info(f"再起動時にチケット情報を読み込みました: チャンネルID {ticket['channel_id']} ユーザーID {ticket['user_id']} 作成日時 {ticket['created_at']}")

    @app_commands.command(name="にゃんこ代行", description="にゃんこ代行チケットを作成します")
    async def nyanko_ticket(self, interaction: discord.Interaction):
        # Embedでパネル表示
        embed = discord.Embed(
            title="にゃんこ代行パネル", 
            description="下のボタンからチケットを作成してください", 
            color=discord.Color.blue()
        )

        button_create_ticket = Button(label="🎫チケットを作成する", style=discord.ButtonStyle.primary)

        async def create_ticket_callback(interaction: discord.Interaction):
            # 支払い方法選択ボタン
            button_paypay = Button(label="PayPay", style=discord.ButtonStyle.primary)
            button_googleplay = Button(label="Google Play", style=discord.ButtonStyle.primary)

            async def paypay_callback(interaction: discord.Interaction):
                modal = NyankoTicketModal(payment_method="PayPay", ticket_button=button_paypay)
                await interaction.response.send_modal(modal)

            async def googleplay_callback(interaction: discord.Interaction):
                modal = NyankoTicketModal(payment_method="Google Play", ticket_button=button_googleplay)
                await interaction.response.send_modal(modal)

            button_paypay.callback = paypay_callback
            button_googleplay.callback = googleplay_callback
            payment_view = View()
            payment_view.add_item(button_paypay)
            payment_view.add_item(button_googleplay)

            # 支払い方法選択メッセージを送信
            await interaction.response.send_message("支払い方法を選択してください:", view=payment_view, ephemeral=True)

        button_create_ticket.callback = create_ticket_callback
        view = View()
        view.add_item(button_create_ticket)

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(NyankoTicketCog(bot))
