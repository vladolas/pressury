# -*- coding: utf-8 -*-
import os
import logging
import csv
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем переменные из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к CSV-файлу
CSV_FILE = "pressure_data.csv"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Привет! Я бот для отслеживания давления.\n'
        'Отправь мне данные в формате: 120/80/70 (верхнее/нижнее/пульс)\n'
        'Пример: 130/85/72'
    )

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Защита от дублирующих обновлений
    if context.chat_data.get('last_update_id') == update.update_id:
        return
    context.chat_data['last_update_id'] = update.update_id

    text = update.message.text.strip()

    try:
        # Разбираем ввод: ожидаем формат "120/80/70"
        parts = text.split('/')
        if len(parts) != 3:
            await update.message.reply_text(
                "Ошибка: введите три числа через /\n"
                "Формат: верхнее/нижнее/пульс\n"
                "Пример: 130/85/72"
            )
            return

        systolic = int(parts[0])
        diastolic = int(parts[1])
        pulse = int(parts[2])

        # Проверка разумных значений
        if not (50 <= systolic <= 250 and 30 <= diastolic <= 150 and 40 <= pulse <= 200):
            await update.message.reply_text("Ошибка: значения вне допустимого диапазона.")
            return

        # === 1. Запись в CSV ===
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["Дата", "Верхнее", "Нижнее", "Пульс"])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                systolic,
                diastolic,
                pulse
            ])

        # === 2. Запись в PostgreSQL ===
        import asyncpg
        try:
            conn = await asyncpg.connect(
                user='bot_user',
                password='my_strong_password_123',
                database='pressure_bot',
                host='postgres',  # ✅ имя сервиса в docker-compose.yml
                port=5432
            )
            await conn.execute("""
                INSERT INTO pressure_log (systolic, diastolic, pulse)
                VALUES ($1, $2, $3)
            """, systolic, diastolic, pulse)
            await conn.close()
        except Exception as e:
            logger.error(f"Ошибка БД: {e}")
            # Не прерываем — CSV важнее

        await update.message.reply_text("Данные сохранены! ✅")

    except ValueError:
        await update.message.reply_text(
            "Ошибка: все значения должны быть числами.\n"
            "Пример: 130/85/72"
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте ещё раз.")

# Основная функция
def main():
    # Получаем токен из переменных окружения
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN не установлен!")
        return

    # Создаем приложение бота
    application = Application.builder().token(token).job_queue(None).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()