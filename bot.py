import os
import logging
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ChatAction
from telegram.constants import ChatAction  # ✅ 수정된 위치
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import asyncio

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

users = {}
bets = {}
history = {}  # 채팅방별 결과 통계 저장

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 10000,
            "last_attendance": None,
            "reward_claimed": False,
            "exp": 0,
            "games": 0,
            "wins": 0,
            "losses": 0
        }
    return users[user_id]

# 📌 베팅 커맨드 핸들러
async def bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_type: str):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user = get_user(user_id)
    name = update.effective_user.first_name
    try:
        amount = int(update.message.text.strip().split()[1])
    except:
        await update.message.reply_text(f"❌ 사용법: /{bet_type.lower()} [금액]")
        return

    if amount < 10000:
        await update.message.reply_text("⚠️ 최소 베팅 금액은 10,000원입니다.")
        return

    if user["balance"] < amount:
        await update.message.reply_text("❌ 보유 금액이 부족합니다.")
        return

    user["balance"] -= amount
    user["games"] += 1

    if chat_id not in bets:
        bets[chat_id] = {"bets": [], "betting_open": True}

    if not bets[chat_id]["betting_open"]:
        await update.message.reply_text("⚠️ 현재 게임이 진행 중입니다. 다음 라운드를 기다려주세요.")
        return

    bets[chat_id]["bets"].append({
        "user_id": user_id,
        "name": name,
        "bet_type": bet_type,
        "amount": amount,
        "time": datetime.now()
    })

    await update.message.reply_text(
        f"🎲 베팅 완료!\n{bet_type} 항목에 {amount:,}원 베팅하셨습니다.\n게임은 30초 후 시작됩니다!"
    )

    if len(bets[chat_id]["bets"]) == 1:
        asyncio.create_task(run_game(update, context, chat_id))

# 📌 게임 실행
async def run_game(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    bets[chat_id]["betting_open"] = False
    await context.bot.send_message(chat_id, "🎲 누군가 베팅했습니다!\n⏳ 30초 후 게임이 시작됩니다!\n🚀 서둘러 베팅에 참여하세요!")

    await asyncio.sleep(30)

    await context.bot.send_message(chat_id, "🧿 플레이어 주사위를 굴립니다.")
    msg1 = await context.bot.send_dice(chat_id, emoji="🎲")
    await asyncio.sleep(3)
    msg2 = await context.bot.send_dice(chat_id, emoji="🎲")
    await asyncio.sleep(3)

    await context.bot.send_message(chat_id, "🧿 뱅커 주사위를 굴립니다.")
    msg3 = await context.bot.send_dice(chat_id, emoji="🎲")
    await asyncio.sleep(3)
    msg4 = await context.bot.send_dice(chat_id, emoji="🎲")
    await asyncio.sleep(3)

    player_sum = msg1.dice.value + msg2.dice.value
    banker_sum = msg3.dice.value + msg4.dice.value

    if player_sum > banker_sum:
        result = "플레이어"
    elif banker_sum > player_sum:
        result = "뱅커"
    else:
        result = "타이"

    await context.bot.send_message(chat_id, f"📢 결과: *{result}* 승!", parse_mode="Markdown")
    await context.bot.send_message(chat_id, f"🎲 *Player*: {msg1.dice.value} + {msg2.dice.value} = {player_sum}\n🎲 *Banker*: {msg3.dice.value} + {msg4.dice.value} = {banker_sum}", parse_mode="Markdown")

    # 결과 통계 저장
    if chat_id not in history:
        history[chat_id] = {"플레이어": 0, "뱅커": 0, "타이": 0}
    history[chat_id][result] += 1

    # 베팅 정산
    for bet in bets[chat_id]["bets"]:
        user = get_user(bet["user_id"])
        if bet["bet_type"] == result:
            user["balance"] += bet["amount"] * 2
            user["wins"] += 1
        else:
            user["losses"] += 1

    bets[chat_id] = {"bets": [], "betting_open": True}

# 📌 /바카라 통계만 출력
async def baccarat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    data = history.get(chat_id, {"플레이어": 0, "뱅커": 0, "타이": 0})
    total = sum(data.values())

    recent_results = "\n".join([f"{key}: {val}회" for key, val in data.items()])
    await update.message.reply_text(
        f"📊 최근 바카라 결과 (임팩트)\n총 게임 수: {total}\n\n{recent_results}\n\n☝️ 가장 최근 결과가 상단입니다."
    )

# 기타 명령어 동일 (출석, 충전, 훈지 등)
# ... (이전 코드에 맞춰 그대로 붙여 사용하세요. 변경 필요 시 알려주세요)

# 📌 메시지 분기 처리
async def handle_korean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("/바카라"):
        await baccarat(update, context)
    elif text.startswith("/뱅"):
        await bet_handler(update, context, "뱅커")
    elif text.startswith("/플"):
        await bet_handler(update, context, "플레이어")
    elif text.startswith("/타이"):
        await bet_handler(update, context, "타이")
    # 기타 커맨드 (출석, 충전, 훈지 등)도 여기에 이어서 처리

# 📌 실행
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/"), handle_korean_command))
    print("✅ 소닉 바카라 봇 실행 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
