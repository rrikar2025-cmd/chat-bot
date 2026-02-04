import os
import json
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)


TEACHER_ID = 5003470564

# ===============================
# 1) ПИТАННЯ ТЕСТУ
# ===============================

QUESTIONS = [
    {
        "question": "1️⃣ Що таке алгоритм?",
        "options": [
            "Комп'ютерна гра",
            "Послідовність команд для виконання завдання",
            "Назва програми",
            "Частина клавіатури",
        ],
        "correct": 1,
    },
    {
        "question": "2️⃣ Яка одиниця вимірювання інформації є найменшою?",
        "options": [
            "Кілобайт",
            "Байт",
            "Біт",
            "Мегабайт",
        ],
        "correct": 2,
    },
    {
        "question": "3️⃣ Що з переліченого є прикладом операційної системи?",
        "options": [
            "Microsoft Word",
            "Google Chrome",
            "Windows",
            "Paint",
        ],
        "correct": 2,
    },
    {
        "question": "4️⃣ Яка відповідь була у останньому ребусі (Четвер)?\n\n📝 Введіть відповідь текстом:",
        "type": "text_input",
        "correct_answer": "коридор",
    },
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
    index = context.user_data["current_question"]
    q = QUESTIONS[index]

    # Якщо питання з текстовим вводом
    if q.get("type") == "text_input":
        context.user_data["awaiting_text_answer"] = True
        await update.effective_chat.send_message(q["question"])
        return

    # Звичайне питання з варіантами
    keyboard = []
    for i, option in enumerate(q["options"]):
        keyboard.append(
            [InlineKeyboardButton(option, callback_data=f"answer_{i}")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_chat.send_message(
        q["question"],
        reply_markup=reply_markup,
    )


# ===============================
# 4) START
# ===============================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_question"] = 0
    context.user_data["score"] = 0
    context.user_data["awaiting_text_answer"] = False

    await update.message.reply_text(
        f"Привіт! Починаємо тест з {len(QUESTIONS)} питань ✅"
    )

    await send_question(update, context)


# ===============================
# 5) ОБРОБКА ВІДПОВІДІ
# ===============================


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = context.user_data["current_question"]

    selected = int(query.data.split("_")[1])
    correct = QUESTIONS[index]["correct"]

    if selected == correct:
        context.user_data["score"] += 1
        await query.edit_message_text("✅ Правильно!")
    else:
        await query.edit_message_text("❌ Неправильно!")

    # Наступне питання
    context.user_data["current_question"] += 1

    # Якщо питання закінчились
    if context.user_data["current_question"] >= len(QUESTIONS):
        await finish_quiz(query, context)
    else:
        await send_question(update, context)


# ===============================
# 6) ОБРОБКА ТЕКСТОВОЇ ВІДПОВІДІ
# ===============================


async def handle_text_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Перевіряємо чи очікуємо текстову відповідь
    if not context.user_data.get("awaiting_text_answer"):
        return

    context.user_data["awaiting_text_answer"] = False

    index = context.user_data["current_question"]
    q = QUESTIONS[index]

    user_answer = update.message.text.strip().lower()
    correct_answer = q["correct_answer"].lower()

    if user_answer == correct_answer:
        context.user_data["score"] += 1
        await update.message.reply_text("✅ Правильно!")
    else:
        await update.message.reply_text("❌ Неправильно!")

    # Наступне питання
    context.user_data["current_question"] += 1

    # Якщо питання закінчились
    if context.user_data["current_question"] >= len(QUESTIONS):
        await finish_quiz_text(update, context)
    else:
        await send_question(update, context)


async def finish_quiz_text(update, context):
    """Фініш тесту для текстових відповідей"""
    score = context.user_data["score"]
    user = update.effective_user

    if score == len(QUESTIONS):
        winners = load_winners()

        name = user.username or user.full_name

        # Перевірка чи вже вигравав
        already_won = any(w["name"] == name for w in winners)

        if not already_won:
            winners.append(
                {
                    "name": name,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            save_winners(winners)

        position = next(
            i for i, w in enumerate(winners, start=1) if w["name"] == name
        )

        await update.message.reply_text(
            f"🏆 ПЕРЕМОГА!\n"
            f"Ти відповів правильно на всі питання!\n"
            f"Ти №{position} у списку переможців 🎉"
        )
    else:
        await update.message.reply_text(
            f"Тест завершено.\n"
            f"Правильних відповідей: {score}/{len(QUESTIONS)}"
        )


# ===============================
# 7) ФІНІШ ТЕСТУ
# ===============================


async def finish_quiz(query, context):
    score = context.user_data["score"]
    user = query.from_user

    if score == len(QUESTIONS):
        winners = load_winners()

        name = user.username or user.full_name

        # Перевірка чи вже вигравав
        already_won = any(w["name"] == name for w in winners)

        if not already_won:
            winners.append(
                {
                    "name": name,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            save_winners(winners)

        position = next(
            i for i, w in enumerate(winners, start=1) if w["name"] == name
        )

        await query.message.reply_text(
            f"🏆 ПЕРЕМОГА!\n"
            f"Ти відповів правильно на всі питання!\n"
            f"Ти №{position} у списку переможців 🎉"
        )
    else:
        await query.message.reply_text(
            f"Тест завершено.\n"
            f"Правильних відповідей: {score}/{len(QUESTIONS)}"
        )


# ===============================
# 7) СПИСОК ПЕРЕМОЖЦІВ (ТІЛЬКИ ВЧИТЕЛЬ)
# ===============================


async def winners_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != TEACHER_ID:
        await update.message.reply_text("❌ Ця команда доступна тільки вчителю.")
        return

    winners = load_winners()

    if not winners:
        await update.message.reply_text("Переможців поки немає.")
        return

    text = "🏆 Список переможців:\n\n"
    for i, w in enumerate(winners, start=1):
        text += f"{i}. {w['name']} — {w['time']}\n"

    await update.message.reply_text(text)


# ===============================
# 8) ОЧИЩЕННЯ СПИСКУ (ТІЛЬКИ ВЧИТЕЛЬ)
# ===============================


async def clean_winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != TEACHER_ID:
        await update.message.reply_text("❌ Ця команда доступна тільки вчителю.")
        return

    save_winners([])
    await update.message.reply_text("✅ Список переможців очищено!")


# ===============================
# 9) MAIN
# ===============================


def main():
    TOKEN = os.getenv("TOKEN", "").strip().strip('"').strip("'")

    if not TOKEN:
        raise ValueError("❌ TOKEN не заданий у Railway Variables!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("winners", winners_list))
    app.add_handler(CommandHandler("clean", clean_winners))

    app.add_handler(CallbackQueryHandler(handle_answer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_answer))

    print("Бот працює...")
    app.run_polling()


if __name__ == "__main__":
    main()
