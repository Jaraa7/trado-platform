"""
يعيد تسجيل webhook تيليجرام مع secret_token.
يُشغَّل داخل machine على Fly (الأسرار هناك فقط):
    flyctl ssh console -a trado-bot -C "python scripts/set_telegram_webhook.py"
لا يطبع أي سر.
"""
import json
import os
import urllib.parse
import urllib.request

token = os.environ["TELEGRAM_BOT_TOKEN"]
secret = os.environ["TELEGRAM_WEBHOOK_SECRET"]
url = os.getenv("WEBHOOK_URL", "https://trado-bot.fly.dev/telegram/webhook")

data = urllib.parse.urlencode({
    "url": url,
    "secret_token": secret,
    "drop_pending_updates": "false",
    "allowed_updates": json.dumps(["message", "callback_query"]),
}).encode()
with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/setWebhook", data=data, timeout=20) as r:
    print("setWebhook:", json.loads(r.read()).get("description"))
with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=20) as r:
    info = json.loads(r.read())["result"]
    print("url:", info.get("url"), "| pending:", info.get("pending_update_count"),
          "| last_error:", info.get("last_error_message"))
