import os
from dotenv import load_dotenv

load_dotenv()  # .env ファイルを読み込む

TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # 環境変数から取得
GUILD_ID = 1330566797937610984
ACHIEVEMENT_CHANNEL_ID = 1335308393988227154
ADMIN_ROLE_ID = 1338449791767547967
