import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from yt_dlp import YoutubeDL

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Проверка наличия FFmpeg
def is_ffmpeg_installed():
    return os.system("ffmpeg -version") == 0

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Добро пожаловать! Данный бот может скачать видео с:\n"
        "- TikTok(!Только Видео!)\n"
        "- YouTube (до 50 МБ)\n"
        "- Instagram Reels\n\n"
        "Отправьте ссылку, и получите видео в максимальном качестве!\n\n"
        "Связаться с автором: @FlexGentle"
    )

# Функция для проверки платформы
def detect_platform(url: str) -> str:
    if "tiktok.com" in url:
        return "tiktok"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "instagram.com/reel/" in url:
        return "instagram"
    return "unknown"

# Функция для обработки ссылок
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    platform = detect_platform(url)

    if platform == "unknown":
        await update.message.reply_text("Это не похоже на поддерживаемую ссылку. Попробуйте TikTok, YouTube или Instagram Reels.")
        return

    # Проверка FFmpeg
    if not is_ffmpeg_installed():
        await update.message.reply_text("FFmpeg не установлен. Установите его для обработки видео.")
        return

    await update.message.reply_text("Скачиваю видео, подождите немного...")

    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'merge_output_format': 'mp4',
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Проверка условий
            if platform == "youtube":
                file_size_estimate = info.get("filesize_approx", 0)  # Оценка размера
                if file_size_estimate > 50 * 1024 * 1024:  # 50 MB
                    await update.message.reply_text(
                        f"Видео слишком большое для отправки (примерно {file_size_estimate / (1024 * 1024):.2f} МБ)."
                    )
                    return

            filename = ydl.prepare_filename(info)
            ydl.download([url])

            # Получение качества видео
            video_format = info.get("format", "неизвестный формат")
            resolution = info.get("height", "неизвестная высота")
            fps = info.get("fps", "неизвестная частота кадров")

            # Отправка видео
            with open(filename, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video_file,
                    caption=(
                        f"Вот ваше видео: {info['title']}\n\n"
                        f"**Качество:** {resolution}p, {fps} FPS\n"
                    ),
                    parse_mode="Markdown",
                )

            
            os.remove(filename)
    except Exception as e:
        logging.error(f"Ошибка при скачивании/отправке: {e}")
        await update.message.reply_text(f"Произошла ошибка.\nПроверьте ссылку и попробуйте снова.\nНапоминаем снова что бот может скачивать только видео!")

def main():
    TOKEN = "7364124522:AAHIxyPi2s4djtwSwa63VykpI09QM2XD59E"

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    # Запуск
    application.run_polling()

if __name__ == "__main__":
    main()

