import telebot
import google.generativeai as genai
import os
import random
import time

# === ТОКЕНЫ (их даст Render) ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

if not TOKEN or not GEMINI_KEY:
    raise ValueError("❌ Токены не найдены. Добавь их в Render.")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")
bot = telebot.TeleBot(TOKEN)

# Хранилище памяти (отдельно для каждого чата)
user_histories = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Гена активирован.")

@bot.message_handler(commands=['clear'])
def clear_history(message):
    chat_id = message.chat.id
    user_histories[chat_id] = []
    bot.reply_to(message, "Память очищена.")

# === ОБРАБОТЧИК ВСЕХ ТЕКСТОВЫХ СООБЩЕНИЙ ===
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):
    chat_id = message.chat.id
    user_text = message.text
    user_name = message.from_user.first_name

    # Игнорируем сообщения от самого бота
    if message.from_user.id == bot.get_me().id:
        return

    # Игнорируем команды (кроме /clear, но она обработана выше)
    if user_text.startswith('/'):
        return

    bot.send_chat_action(chat_id, 'typing')
    time.sleep(0.5)

    try:
        # Получаем историю чата
        history = user_histories.get(chat_id, [])
        
        # Определяем, кто написал (для контекста)
        if message.chat.type in ['group', 'supergroup']:
            history.append(f"{user_name}: {user_text}")
        else:
            history.append(f"Пользователь: {user_text}")

        user_histories[chat_id] = history[-10:]

        context = "\n".join(user_histories[chat_id])

        # Инструкция для нейросети
        prompt = f"""Ты — Гена. Отвечай кратко и по делу.
История диалога:
{context}
Гена:"""

        response = model.generate_content(prompt)
        reply = response.text.strip()

        if not reply:
            reply = "Понял."

        # Вставляем "Данзан манунов" (иногда)
        if "Данзан" not in reply and random.random() < 0.1:
            reply += " Данзан манунов."

        history.append(f"Гена: {reply}")
        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

print("✅ Бот Гена активирован (группы + личка)")
bot.infinity_polling()
