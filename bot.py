import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# .envファイルから環境変数をロード
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # コグの読み込み（非同期に実行）
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                # 非同期にコグを読み込む
                await bot.load_extension(f'cogs.{filename[:-3]}')  
                print(f"Loaded cog: {filename} - 正しく読み込めました。")
            except Exception as e:
                print(f"Failed to load cog {filename}: {e}")
    
    # スラッシュコマンドの同期
    await bot.tree.sync()
    print("スラッシュコマンドが正常に同期されました。")

# コグを読み込むコマンド
@bot.command()
async def load(ctx, extension):
    try:
        await bot.load_extension(f'cogs.{extension}')
        await ctx.send(f'{extension} を正しく読み込めました。')
    except Exception as e:
        await ctx.send(f"エラーが発生しました: {e}")

# コグをアンロードするコマンド
@bot.command()
async def unload(ctx, extension):
    try:
        await bot.unload_extension(f'cogs.{extension}')
        await ctx.send(f'{extension} をアンロードしました。')
    except Exception as e:
        await ctx.send(f"エラーが発生しました: {e}")

# コグをリロードするコマンド
@bot.command()
async def reload(ctx, extension):
    try:
        await bot.reload_extension(f'cogs.{extension}')
        await ctx.send(f'{extension} をリロードしました。')
    except Exception as e:
        await ctx.send(f"エラーが発生しました: {e}")

# Botの起動
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
