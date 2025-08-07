import os
import logging
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# 사용자 데이터 저장소 (메모리 기반)
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

### 바카라 게임 ###
async def baccarat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    result = random.choice(["플레이어", "뱅커", "타이"])
    await update.message.reply_text(f"🎲 바카라 결과: {result}\n💰 현재 포인트: {user['balance']:,}원")

### 공통 베팅 처리 ###
async def bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_type: str):
    user = get_user(update.effective_user.id)
    try:
        amount = int(context.args[0])
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

### 축구 ###
async def soccer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["⚽ 골!", "❌ 노골!"])
    await update.message.reply_text(f"축구 결과: {result}")

### 농구 ###
async def basketball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["🏀 골!", "❌ 노골!"])
    await update.message.reply_text(f"농구 결과: {result}")

### 충전 (1만, 조건부) ###
async def charge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if user["balance"] > 10000:
        await update.message.reply_text("💰 잔액이 10,000원을 초과하여 충전할 수 없습니다.")
        return
    user["balance"] += 10000
    await update.message.reply_text(f"💳 1만 포인트 충전 완료!\n💰 현재 포인트: {user['balance']:,}원")

### 훈지 (40% 확률, 30만원) ###
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

### 보상 (1회 30만원) ###
async def reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if user["reward_claimed"]:
        await update.message.reply_text("⛔ 이미 보상을 받았습니다.")
    else:
        user["balance"] += 300000
        user["reward_claimed"] = True
        await update.message.reply_text("🎁 보상 지급 완료! +30만 포인트")

### 출석 (10만 + 경험치 + 카드 메시지) ###
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

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # 명령어 등록
    app.add_handler(CommandHandler("바카라", baccarat))
    app.add_handler(CommandHandler("뱅", lambda u, c: bet_handler(u, c, "뱅커")))
    app.add_handler(CommandHandler("플", lambda u, c: bet_handler(u, c, "플레이어")))
    app.add_handler(CommandHandler("플페어", lambda u, c: bet_handler(u, c, "플페어")))
    app.add_handler(CommandHandler("뱅페어", lambda u, c: bet_handler(u, c, "뱅페어")))
    app.add_handler(CommandHandler("타이", lambda u, c: bet_handler(u, c, "타이")))

    app.add_handler(CommandHandler("축구", soccer))
    app.add_handler(CommandHandler("농구", basketball))
    app.add_handler(CommandHandler("충전", charge))
    app.add_handler(CommandHandler("훈지", hunji))
    app.add_handler(CommandHandler("보상", reward))
    app.add_handler(CommandHandler("출석", attendance))

    print("✅ 소닉 바카라 봇 실행 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
