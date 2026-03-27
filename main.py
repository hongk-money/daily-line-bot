import logging
import os
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8279990526:AAHVP0yJpDjbYxHiVztj5vNajgzWT1nVzZo")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003854660566"))
ALLOWED_USER = os.environ.get("ALLOWED_USER", "Hongk_in_hk")  # 친구 A 텔레그램 username

logging.basicConfig(level=logging.INFO)

def get_hkt_time():
    hkt = pytz.timezone("Asia/Hong_Kong")
    now = datetime.now(hkt)
    return now.strftime("%m.%d %H:%M HKT")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # 허용된 유저만 처리 (봇 주인 or 친구 A)
    if ALLOWED_USER and user.username not in [ALLOWED_USER, "hongk_in_hk"]:
        await update.message.reply_text("권한이 없습니다.")
        return

    photo = update.message.photo[-1]  # 가장 큰 해상도
    caption = update.message.caption or ""

    # 캡션에 BTC/ETH 키워드 감지
    caption_lower = caption.lower()
    if "btc" in caption_lower or "bitcoin" in caption_lower:
        label = "BTC"
        emoji = "🟡"
    elif "eth" in caption_lower or "ethereum" in caption_lower:
        label = "ETH"
        emoji = "🔵"
    else:
        label = "차트"
        emoji = "📊"

    channel_caption = (
        f"{emoji} {label} 주요 라인 | {get_hkt_time()}\n"
        f"🟠 상단 저항선 · ⬜ 하단 지지선\n"
        f"─────────────────"
    )

    await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=photo.file_id,
        caption=channel_caption
    )

    await update.message.reply_text(f"✅ {label} 채널 발송 완료")

async def handle_group_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """그룹에서 봇에게 보낼 때도 처리"""
    await handle_photo(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("봇 시작됨. 사진을 보내면 채널에 자동 발송됩니다.")
    app.run_polling()

if __name__ == "__main__":
    main()
