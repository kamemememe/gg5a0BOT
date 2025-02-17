import discord
from discord.ext import commands
import asyncio

ticket_owners = {}

class TsumtsumTicketModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="ツムツム代行 - チケット情報")
        self.add_item(discord.ui.TextInput(label="メールアドレス", placeholder="example@example.com"))
        self.add_item(discord.ui.TextInput(label="パスワード", placeholder="password"))
        self.add_item(discord.ui.TextInput(label="PayPayリンク", placeholder="https://pay.paypay.ne.jp/xxxxx"))
        self.add_item(discord.ui.TextInput(label="代行内容", placeholder="代行内容の詳細"))

    async def callback(self, interaction: discord.Interaction):
        data = [child.value for child in self.children]
        server = interaction.guild
        user = interaction.user
        overwrites = {
            server.default_role: discord.PermissionOverwrite(read_messages=False),
            server.me: discord.PermissionOverwrite(read_messages=True),
            user: discord.PermissionOverwrite(read_messages=True)
        }
        channel_name = f"ツムツム代行-{user.name}"
        channel = await server.create_text_channel(name=channel_name, overwrites=overwrites)

        ticket_owners[channel.id] = user.id
        await interaction.response.send_message(f"チケットが作成されました: {channel.mention}")

class TicketButton(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    @discord.ui.button(label="削除", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        confirmation_embed = discord.Embed(
            title="削除確認",
            description="本当にチケットを削除しますか？\n削除後は元に戻せません。",
            color=discord.Color.red()
        )
        confirmation_view = discord.ui.View()
        confirmation_view.add_item(
            discord.ui.Button(label="確定", style=discord.ButtonStyle.danger, custom_id="confirm_delete")
        )
        confirmation_view.add_item(
            discord.ui.Button(label="キャンセル", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")
        )
        await interaction.response.send_message(embed=confirmation_embed, view=confirmation_view)

    @discord.ui.button(label="削除キャンセル", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")
    async def cancel_delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("チケット削除がキャンセルされました。", ephemeral=True)

    @discord.ui.button(label="確定", style=discord.ButtonStyle.danger, custom_id="confirm_delete")
    async def confirm_delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="削除確定",
                description="10秒後にチケットが削除されます。",
                color=discord.Color.green()
            )
        )
        await asyncio.sleep(10)
        await self.channel.delete()

# コグをセットアップするためのsetup関数
async def setup(bot: commands.Bot):
    @bot.tree.command(name="tsumtsum_ticket", description="ツムツム代行チケット作成")
    async def tsumtsum_ticket(interaction: discord.Interaction):
        modal = TsumtsumTicketModal()
        await interaction.response.send_modal(modal)
