import os
import logging
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, ContextTypes, filters
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

users = {}

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

# 📌 공통 베팅 처리
async def bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_type: str):
    user = get_user(update.effective_user.id)
    try:
        amount = int(update.message.text.strip().split()[1])
    except:
        await update.message.reply_text(f"❌ 사용법: /{bet_type.lower()} [금액]")
        return

    if user["balance"] < amount:
        await update.message.reply_text("❌ 보유 금액이 부족합니다.")
        return

    user["balance"] -= amount
    user["games"] += 1
    win = random.random() < 0.5
    if win:
        user["balance"] += amount * 2
        user["wins"] += 1
        await update.message.reply_text(f"🎉 {bet_type} 베팅 성공! 2배 지급!\n💰 포인트: {user['balance']:,}원")
    else:
        user["losses"] += 1
        await update.message.reply_text(f"😭 {bet_type} 베팅 실패!\n💰 포인트: {user['balance']:,}원")

# 🎲 바카라
async def baccarat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    result = random.choice(["플레이어", "뱅커", "타이"])
    await update.message.reply_text(f"🎲 바카라 결과: {result}\n💰 현재 포인트: {user['balance']:,}원")

# ⚽ 축구
async def soccer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["⚽ 골!", "❌ 노골!"])
    await update.message.reply_text(f"축구 결과: {result}")

# 🏀 농구
async def basketball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["🏀 골!", "❌ 노골!"])
    await update.message.reply_text(f"농구 결과: {result}")

# 💳 충전
async def charge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if user["balance"] > 10000:
        await update.message.reply_text("💰 잔액이 10,000원을 초과하여 충전할 수 없습니다.")
        return
    user["balance"] += 50000
    await update.message.reply_text(f"💳 5만 포인트 충전 완료!\n💰 현재 포인트: {user['balance']:,}원")

# 🎁 보상
async def reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if user["reward_claimed"]:
        await update.message.reply_text("⛔ 이미 보상을 받았습니다.")
    else:
        user["balance"] += 300000
        user["reward_claimed"] = True
        await update.message.reply_text("🎁 보상 지급 완료! +30만 포인트")

# 📅 출석
async def attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    today = datetime.now().date()
    name = update.effective_user.first_name
    username = update.effective_user.username or "N/A"

    if user["last_attendance"] == today:
        await update.message.reply_text("⚠️ 이미 출석체크를 완료하셨습니다\n📅 내일 00시에 다시해주세요!")
        return

    user["last_attendance"] = today
    user["balance"] += 100000
    user["exp"] += 2

    exp_percent = min(int(user["exp"]), 100)
    exp_bar = "▓" * (exp_percent // 10) + "░" * (10 - exp_percent // 10)
    win_rate = int((user["wins"] / user["games"]) * 100) if user["games"] > 0 else 0

    msg = (
        f"✅ 출석체크 완료\n🎁 경험치 +2 및 10만원 지급!\n\n"
        f"🧑‍💼 {name}\n"
        f"🔗 @{username}   🪪 {user_id}   🧱 LV 3\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 보유 금액: {user['balance']:,}원\n"
        f"🎯 게임 횟수: {user['games']}회\n"
        f"⚔️ 게임 전적: {user['wins']}승 {user['losses']}패 ({win_rate}%)\n"
        f"🔋 경험치: {exp_bar} {exp_percent}%\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Sonic Dice Baccarat"
    )
    await update.message.reply_text(msg)

# 🧧 훈지 (40% 확률, 30만)
async def hunji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    name = update.effective_user.first_name

    if random.random() < 0.4:
        reward = 300000
        user["balance"] += reward
        msg = (
            f"🧑‍💼 {name}님 축하합니다!\n"
            f"🎯 40% 확률에 당첨되셨습니다!\n"
            f"💸 30만원이 지급되었습니다!\n"
            f"💰 보유 잔액: {user['balance']:,}원"
        )
    else:
        msg = (
            f"🧑‍💼 {name}님,\n"
            f"😢 아쉽게도 이번에는 당첨되지 않았습니다.\n"
            f"📅 내일 오전 9시 이후 다시 도전해보세요!"
        )

    await update.message.reply_text(msg)

# 💬 한글 명령어 분기 처리
async def handle_korean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("/바카라"):
        await baccarat(update, context)
    elif text.startswith("/출석"):
        await attendance(update, context)
    elif text.startswith("/훈지"):
        await hunji(update, context)
    elif text.startswith("/충전"):
        await charge(update, context)
    elif text.startswith("/보상"):
        await reward(update, context)
    elif text.startswith("/축구"):
        await soccer(update, context)
    elif text.startswith("/농구"):
        await basketball(update, context)
    elif text.startswith("/뱅페어"):
        await bet_handler(update, context, "뱅페어")
    elif text.startswith("/플페어"):
        await bet_handler(update, context, "플페어")
    elif text.startswith("/뱅"):
        await bet_handler(update, context, "뱅커")
    elif text.startswith("/플"):
        await bet_handler(update, context, "플레이어")
    elif text.startswith("/타이"):
        await bet_handler(update, context, "타이")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/"), handle_korean_command))
    print("✅ 소닉 바카라 봇 실행 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
