import os
import logging
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ChatAction
from telegram.ext import (
    ApplicationBuilder, MessageHandler, ContextTypes, filters
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

users = {}
bets = {}
game_active = {}
results_by_chat = {}

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

def get_results(chat_id):
    if chat_id not in results_by_chat:
        results_by_chat[chat_id] = []
    return results_by_chat[chat_id]

async def send_dice_and_get_value(context, chat_id):
    dice = await context.bot.send_dice(chat_id=chat_id, emoji="🎲")
    return dice.dice.value

async def run_baccarat_game(context: ContextTypes.DEFAULT_TYPE, chat_id):
    game_active[chat_id] = False  # 베팅 차단
    await context.bot.send_message(chat_id, "🎲 플레이어 주사위를 굴립니다!")
    p1 = await send_dice_and_get_value(context, chat_id)
    p2 = await send_dice_and_get_value(context, chat_id)
    await context.bot.send_message(chat_id, "🎲 뱅커 주사위를 굴립니다!")
    b1 = await send_dice_and_get_value(context, chat_id)
    b2 = await send_dice_and_get_value(context, chat_id)

    player_total = p1 + p2
    banker_total = b1 + b2

    if player_total > banker_total:
        result = "플레이어"
    elif banker_total > player_total:
        result = "뱅커"
    else:
        result = "타이"

    results_by_chat[chat_id].append(result)
    if len(results_by_chat[chat_id]) > 15:
        results_by_chat[chat_id] = results_by_chat[chat_id][-15:]

    bet_list = bets.pop(chat_id, {})
    result_msg = f"📊 결과: <b>{result}</b> 승!\n\n🎲 <b>Player</b>: {p1} + {p2} = {player_total}\n🎲 <b>Banker</b>: {b1} + {b2} = {banker_total}"
    await context.bot.send_message(chat_id, result_msg, parse_mode='HTML')

    for user_id, bet in bet_list.items():
        user = get_user(user_id)
        user["games"] += 1
        if bet["choice"] == result:
            reward = bet["amount"] * 2
            user["balance"] += reward
            user["wins"] += 1
        else:
            user["losses"] += 1

async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
    user = get_user(update.effective_user.id)
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    name = update.effective_user.first_name

    if game_active.get(chat_id, False):
        await update.message.reply_text("❌ 현재 게임이 진행 중입니다. 다음 라운드를 기다려주세요.")
        return

    try:
        amount = int(update.message.text.strip().split()[1])
    except:
        await update.message.reply_text("❌ 사용법: /명령어 [금액]")
        return

    if amount < 10000:
        await update.message.reply_text("⚠️ 최소 베팅 금액은 10,000원입니다.")
        return

    if user["balance"] < amount:
        await update.message.reply_text("❌ 보유 금액이 부족합니다.")
        return

    user["balance"] -= amount
    if chat_id not in bets:
        bets[chat_id] = {}
        game_active[chat_id] = True
        await update.message.reply_text("👀 누군가 베팅했습니다!\n🕒 30초 후 게임이 시작됩니다!\n🚀 서둘러 배팅에 참여하세요!")
        await context.job_queue.run_once(lambda c: run_baccarat_game(c, chat_id), 30)

    bets[chat_id][user_id] = {"choice": choice, "amount": amount}

    await update.message.reply_text(
        f"🎲 <b>{name}</b>\n└ 📌 베팅 항목: {choice}\n└ 💰 베팅 금액: {amount:,}원",
        parse_mode='HTML'
    )

async def baccarat_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    result_list = get_results(chat_id)
    total = len(result_list)
    p = result_list.count("플레이어")
    b = result_list.count("뱅커")
    t = result_list.count("타이")
    text = (
        f"🧾 <b>최근 바카라 결과</b>\n"
        f"📊 임팩트\n└ 총 플레이 횟수: {total}\n└ 총 P: {p} | B: {b} | T: {t}\n"
        f"━━━━━━━━━━━━━━\n"
    )
    for res in reversed(result_list):
        if res == "플레이어":
            text += "🟦 Player\n"
        elif res == "뱅커":
            text += "🟥 Banker\n"
        else:
            text += "🟩 Tie\n"
    text += "\n☝️ 가장 상단이 최신 결과입니다"
    await update.message.reply_text(text, parse_mode='HTML')

# 기타 기존 기능은 이전 코드와 동일하게 추가
# 예: /충전, /훈지, /출석, /보상 등

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("/바카라"):
        await baccarat_result(update, context)
    elif text.startswith("/뱅"):
        await handle_bet(update, context, "뱅커")
    elif text.startswith("/플"):
        await handle_bet(update, context, "플레이어")
    elif text.startswith("/타이"):
        await handle_bet(update, context, "타이")
    # ⚠️ 여기에 출석, 훈지, 충전, 보상, 농구, 축구 등도 연결

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/"), handle_commands))
    print("✅ Sonic Baccarat 봇 실행 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
