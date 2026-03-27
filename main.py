import logging
import os
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))
ALLOWED_USER = os.environ.get("ALLOWED_USER", "").lower()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_hkt_time():
    hkt = pytz.timezone("Asia/Hong_Kong")
    now = datetime.now(hkt)
    return now.strftime("%m.%d %H:%M HKT")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ 홍크 라인봇 작동 중\n\n"
        "사진과 함께 캡션에 BTC 또는 ETH 입력해서 보내주세요."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = (user.username or "").lower()

    logger.info(f"사진 수신 - 유저: {username}, ALLOWED: {ALLOWED_USER}")

    if ALLOWED_USER and username != ALLOWED_USER:
        await update.message.reply_text(f"❌ 권한 없음 (username: {username})")
        return

    photo = update.message.photo[-1]
    caption = (update.message.caption or "").lower()

    if "btc" in caption or "bitcoin" in caption:
        label = "BTC"
        emoji = "🟡"
    elif "eth" in caption or "ethereum" in caption:
        label = "ETH"
        emoji = "🔵"
    else:
        label = "차트"
        emoji = "📊"

    channel_caption = (
        f"{emoji} {label} 주요 라인 | {get_hkt_time()}\n"
        f"🟠 상단 저항선  ·  ⬜ 하단 지지선\n"
        f"─────────────────"
    )

    try:
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo.file_id,
            caption=channel_caption
        )
        await update.message.reply_text(f"✅ {label} 채널 발송 완료!")
        logger.info(f"{label} 채널 발송 성공")
    except Exception as e:
        await update.message.reply_text(f"❌ 발송 실패: {str(e)}")
        logger.error(f"발송 실패: {e}")

def main():
    logger.info(f"봇 시작 - CHANNEL_ID: {CHANNEL_ID}, ALLOWED_USER: {ALLOWED_USER}")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
