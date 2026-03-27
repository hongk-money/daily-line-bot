import logging
import os
import base64
from datetime import datetime
import pytz
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))
ALLOWED_USER = os.environ.get("ALLOWED_USER", "").lower()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def get_hkt_time():
    hkt = pytz.timezone("Asia/Hong_Kong")
    now = datetime.now(hkt)
    return now.strftime("%m.%d %H:%M HKT")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ 홍크 라인봇 작동 중\n\n"
        "사진만 보내주세요. 자동으로 라인값 추출해서 채널에 올려드려요.\n\n"
        "캡션에 BTC 또는 ETH 입력해주세요."
    )

async def analyze_chart(image_bytes: bytes, coin: str) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    prompt = f"""이 차트 이미지에서 두 가지 수평선의 가격값을 읽어주세요.

1. 주황색(오렌지색) 점선 또는 굵은 선 = 상단 저항선
2. 회색 점선 또는 굵은 선 = 하단 지지선

차트 오른쪽 끝에 표시된 숫자값을 읽어주세요.

반드시 아래 형식으로만 답해주세요:
상단: [숫자]
하단: [숫자]

숫자 외에 다른 말은 하지 마세요."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": prompt}
                ],
            }
        ],
    )

    result = message.content[0].text.strip()
    logger.info(f"Claude 분석 결과: {result}")

    upper = lower = None
    for line in result.split('\n'):
        if '상단' in line:
            val = line.split(':')[-1].strip().replace(',', '')
            upper = val
        elif '하단' in line:
            val = line.split(':')[-1].strip().replace(',', '')
            lower = val

    return {"upper": upper, "lower": lower}

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = (user.username or "").lower()

    if ALLOWED_USER and username != ALLOWED_USER:
        await update.message.reply_text("❌ 권한 없음")
        return

    caption = (update.message.caption or "").upper()
    if "BTC" in caption or "BITCOIN" in caption:
        coin = "BTC"
        emoji = "🟡"
    elif "ETH" in caption or "ETHEREUM" in caption:
        coin = "ETH"
        emoji = "🔵"
    else:
        await update.message.reply_text("❌ 캡션에 BTC 또는 ETH 입력해주세요.")
        return

    processing_msg = await update.message.reply_text("⏳ 차트 분석 중...")

    try:
        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)
        image_bytes = await photo_file.download_as_bytearray()

        values = await analyze_chart(bytes(image_bytes), coin)

        if values["upper"] and values["lower"]:
            message = (
                f"{emoji} {coin} 주요 라인 | {get_hkt_time()}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🟠 상단 저항선  {values['upper']}\n"
                f"⬜ 하단 지지선  {values['lower']}\n"
                f"━━━━━━━━━━━━━━━━"
            )
        else:
            message = (
                f"{emoji} {coin} 주요 라인 | {get_hkt_time()}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"⚠️ 라인값 자동추출 실패\n"
                f"━━━━━━━━━━━━━━━━"
            )

        await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
        await processing_msg.edit_text(f"✅ 채널 발송 완료!\n\n{message}")
        logger.info(f"발송 성공: {coin}")

    except Exception as e:
        await processing_msg.edit_text(f"❌ 오류 발생: {str(e)}")
        logger.error(f"오류: {e}")

def main():
    logger.info(f"봇 시작 - CHANNEL_ID: {CHANNEL_ID}, ALLOWED_USER: {ALLOWED_USER}")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
