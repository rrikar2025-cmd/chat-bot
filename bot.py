import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ===============================
# 1) ПИТАННЯ ТЕСТУ
# ===============================

QUESTIONS = [
    {
        "question": "1️⃣ Що таке алгоритм?",
        "options": [
            "Комп’ютерна гра",
            "Послідовність команд для виконання завдання",
            "Назва програми",
            "Частина клавіатури"
        ],
        "correct": 1
    },
    {
        "question": "2️⃣ Яка одиниця вимірювання інформації є найменшою?",
        "options": [
            "Кілобайт",
            "Байт",
            "Біт",
            "Мегабайт"
        ],
        "correct": 2
    },
    {
        "question": "3️⃣ Що з переліченого є прикладом операційної системи?",
        "options": [
            "Microsoft Word",
            "Google Chrome",
            "Windows",
            "Paint"
        ],
        "correct": 2
    }
]


WINNERS_FILE = "winners.json"

# ===============================
# 2) ЗАВАНТАЖЕННЯ / ЗБЕРЕЖЕННЯ
# ===============================

def load_winners():
    if not os.path.exists(WINNERS_FILE):
        return []
    with open(WINNERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_winners(winners):
    with open(WINNERS_FILE, "w", encoding="utf-8") as f:
        json.dump(winners, f, ensure_ascii=False, indent=2)


# ===============================
# 3) ПОКАЗ ПИТАННЯ
# ===============================

async def send_question(update, context):
    user_data = context.user_data
    index = user_data["current_question"]

    q = QUESTIONS[index]

    keyboard = []
    for i, option in enumerate(q["options"]):
        keyboard.append(
            [InlineKeyboardButton(option, callback_data=f"answer_{i}")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_chat.send_message(
        q["question"],
        reply_markup=reply_markup
    )


# ===============================
# 4) START
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_question"] = 0
    context.user_data["score"] = 0

    await update.message.reply_text(
        "Привіт! Починаємо тест з 3 питань ✅"
    )

    await send_question(update, context)


# ===============================
# 5) ОБРОБКА ВІДПОВІДІ
# ===============================

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    index = user_data["current_question"]

    selected = int(query.data.split("_")[1])
    correct = QUESTIONS[index]["correct"]

    if selected == correct:
        user_data["score"] += 1
        await query.edit_message_text("✅ Правильно!")
    else:
        await query.edit_message_text("❌ Неправильно!")

    # Наступне питання
    user_data["current_question"] += 1

    # Якщо питання закінчились
    if user_data["current_question"] >= len(QUESTIONS):
        await finish_quiz(query, context)
    else:
        await send_question(update, context)


# ===============================
# 6) ФІНІШ ТЕСТУ
# ===============================

async def finish_quiz(query, context):
    score = context.user_data["score"]
    user = query.from_user

    if score == len(QUESTIONS):
        winners = load_winners()

        # Перевірка чи вже вигравав
        if user.username not in winners:
            winners.append(user.username or user.full_name)
            save_winners(winners)

        position = winners.index(user.username or user.full_name) + 1

        await query.message.reply_text(
            f"🏆 ПЕРЕМОГА!\n"
            f"Ти відповів правильно на всі питання!\n"
            f"Ти №{position} у списку переможців 🎉"
        )
    else:
        await query.message.reply_text(
            f"Тест завершено.\n"
            f"Правильних відповідей: {score}/3"
        )


# ===============================
# 7) СПИСОК ПЕРЕМОЖЦІВ ДЛЯ ВЧИТЕЛЯ
# ===============================

async def winners_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    winners = load_winners()

    if not winners:
        await update.message.reply_text("Переможців поки немає.")
        return

    text = "🏆 Список переможців:\n\n"
    for i, name in enumerate(winners, start=1):
        text += f"{i}. {name}\n"

    await update.message.reply_text(text)


# ===============================
# 8) MAIN
# ===============================

def main():
    
    TOKEN = os.getenv("TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("winners", winners_list))
    app.add_handler(CallbackQueryHandler(handle_answer))

    print("Бот працює...")
    app.run_polling()


if __name__ == "__main__":
    main()
