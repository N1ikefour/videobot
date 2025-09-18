import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

from telegram import Update, Message
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)
from telegram.constants import ChatAction

from config import settings, SUPPORTED_VIDEO_FORMATS
from video_processor import video_processor

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class VideoBot:
    """Телеграм бот для сжатия видео с добавлением случайных рамок"""
    
    def __init__(self):
        self.application = Application.builder().token(settings.bot_token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        
        # Обработка видео файлов
        self.application.add_handler(
            MessageHandler(filters.VIDEO, self.handle_video)
        )
        
        # Обработка документов (видео как документы)
        self.application.add_handler(
            MessageHandler(filters.Document.ALL, self.handle_document)
        )
        
        # Обработка текстовых сообщений
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
        )
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_message = """
🎬 *Добро пожаловать в VideoBot!*

Я умею сжимать видео и конвертировать их в формат Stories (1080x1920).

📎 *Как использовать:*
• Отправь мне видео файл
• Получишь сразу 6 разных вариантов!
• Все в формате 1080x1920 (Stories)

📋 *Поддерживаемые форматы:*
MP4, AVI, MOV, MKV, WEBM, FLV и другие

⚙️ *Возможности:*
• 6 вариантов с разным размером файла
• Уникальные рамки разной толщины для каждого варианта
• 20 разных цветов рамок (случайный выбор)
• Размер всегда 1080x1920 (Stories)
• Визуально лossless качество

Отправь видео и получи 6 уникальных вариантов! 🚀
        """
        
        await update.message.reply_text(
            welcome_message, 
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_message = """
📖 *Справка по VideoBot*

🎯 *Основная функция:*
Создание 6 вариантов видео в формате Stories (1080x1920) с разными рамками

📝 *Доступные команды:*
/start - Начать работу с ботом
/help - Показать эту справку
/stats - Статистика обработки

📐 *Что получаешь:*
• 6 вариантов одного видео
• Размер: 1080x1920 (Stories)
• Каждый с уникальной рамкой (от тонкой до мега-толстой)
• Разные размеры файлов (от компактного до максимального качества)
• 20 разных цветов рамок (случайный выбор)
• Сохранение пропорций исходного видео

⚠️ *Ограничения:*
• Максимальный размер: 20MB (лимит Telegram Bot API)
• Поддерживаемые форматы: {formats}

💡 *Советы:*
• Файлы до 20MB обрабатываются надёжно
• Для больших файлов используйте сжатие перед отправкой
• Telegram getFile API имеет жёсткий лимит 20MB

🔧 *Технические особенности:*
• 6 настроек качества: от максимального до ультра-компактного
• Толщина рамок: от 10px до 150px (7 вариантов)
• Кодек H.264 с разными CRF (18-30)
• Bitrate от 400k до 2500k
• Сохранение аудио в высоком качестве
        """.format(
            max_size=settings.max_file_size_mb,
            formats=", ".join(sorted(SUPPORTED_VIDEO_FORMATS))
        )
        
        await update.message.reply_text(
            help_message, 
            parse_mode='Markdown'
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats"""
        stats_message = """
📊 *Статистика VideoBot*

🗂 *Директории:*
• Временные файлы: `{temp_dir}`
• Выходные файлы: `{output_dir}`

⚙️ *Настройки:*
• Максимальный размер: {max_size}MB
• Поддерживаемых форматов: {formats_count}

🎲 *Доступных соотношений сторон:* {ratios_count}

Bot работает стабильно! ✅
        """.format(
            temp_dir=settings.temp_dir,
            output_dir=settings.output_dir,
            max_size=settings.max_file_size_mb,
            formats_count=len(SUPPORTED_VIDEO_FORMATS),
            ratios_count=len(video_processor.calculate_resize_params.__code__.co_names)
        )
        
        await update.message.reply_text(
            stats_message, 
            parse_mode='Markdown'
        )
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик видео файлов"""
        message = update.message
        video = message.video
        
        # Логируем размер полученного видео
        file_size_mb = video.file_size / (1024 * 1024)
        logger.info(f"📥 ВИДЕО получено: {file_size_mb:.2f}MB ({video.file_size} bytes)")
        logger.info(f"📋 Детали видео: {video.width}x{video.height}, длительность: {video.duration}с")
        
        # Проверяем размер файла
        if video.file_size > settings.max_file_size_mb * 1024 * 1024:
            logger.warning(f"❌ ВИДЕО отклонено: размер {file_size_mb:.2f}MB превышает лимит {settings.max_file_size_mb}MB")
            await message.reply_text(
                f"❌ Видео превышает максимальный размер!\n\n"
                f"📁 Размер вашего видео: {file_size_mb:.1f}MB\n"
                f"📏 Максимальный размер: {settings.max_file_size_mb}MB\n\n"
                f"💡 Уменьшите размер файла до 50MB или меньше"
            )
            return
        
        # Сразу обрабатываем видео с 6 вариантами
        await self.process_video_file(message, context, video.file_id, 
                                    video.file_name or f"video_{int(time.time())}.mp4", 6)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик документов (видео отправленные как документы)"""
        message = update.message
        document = message.document
        
        # Проверяем, является ли документ видео файлом
        if not document.file_name:
            return
        
        file_extension = Path(document.file_name).suffix.lower()
        if file_extension not in SUPPORTED_VIDEO_FORMATS:
            return
        
        # Логируем размер полученного документа
        file_size_mb = document.file_size / (1024 * 1024)
        logger.info(f"📄 ДОКУМЕНТ получен: {file_size_mb:.2f}MB ({document.file_size} bytes)")
        logger.info(f"📋 Имя файла: {document.file_name}, тип: {document.mime_type}")
        
        # Проверяем размер файла
        if document.file_size > settings.max_file_size_mb * 1024 * 1024:
            logger.warning(f"❌ ДОКУМЕНТ отклонен: размер {file_size_mb:.2f}MB превышает лимит {settings.max_file_size_mb}MB")
            await message.reply_text(
                f"❌ Документ превышает максимальный размер!\n\n"
                f"📁 Размер файла: {file_size_mb:.1f}MB\n"
                f"📏 Максимальный размер: {settings.max_file_size_mb}MB\n\n"
                f"💡 Уменьшите размер файла до 50MB или меньше"
            )
            return
        
        # Сразу обрабатываем видео-документ с 6 вариантами
        await self.process_video_file(message, context, document.file_id, document.file_name, 6)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        await update.message.reply_text(
            "🎬 Отправь мне видео файл!\n\n"
            "📱 Простой процесс:\n"
            "1️⃣ Отправляешь видео\n"
            "2️⃣ Получаешь сразу 6 разных вариантов!\n\n"
            "✅ Каждый вариант с уникальной рамкой\n"
            "✅ Разные размеры файлов\n"
            "✅ Все в формате 1080x1920 (Stories)\n\n"
            "Используй /help для получения справки."
        )
    
    async def process_video_file(self, message: Message, context: ContextTypes.DEFAULT_TYPE, file_id: str, filename: str, variant_count: int = 6):
        """Основная функция обработки видео"""
        user_id = message.from_user.id
        logger.info(f"Начинаю обработку видео для пользователя {user_id}, файл: {filename}")
        
        # Уведомляем пользователя о начале обработки
        await message.reply_text("🎬 Начинаю обработку видео...")
        
        # Показываем индикатор "загрузка видео"
        await message.chat.send_action(ChatAction.UPLOAD_VIDEO)
        
        # Создаем уникальные имена файлов
        timestamp = int(time.time())
        temp_input_path = settings.temp_dir / f"{user_id}_{timestamp}_input_{filename}"
        temp_output_path = settings.output_dir / f"{user_id}_{timestamp}_output.mp4"
        
        try:
            # Скачиваем файл
            progress_message = await message.reply_text("📥 Скачиваю видео...")
            
            try:
                file = await context.bot.get_file(file_id)
                
                # Логируем детальную информацию о файле через Bot API
                api_file_size_mb = file.file_size / (1024*1024)
                logger.info(f"🔍 Bot API информация:")
                logger.info(f"   📏 Размер: {api_file_size_mb:.2f}MB ({file.file_size} bytes)")
                logger.info(f"   📂 Путь: {file.file_path}")
                logger.info(f"   🆔 File ID: {file.file_id}")
                
                # Дополнительная проверка размера файла через Bot API  
                if file.file_size > 20 * 1024 * 1024:  # 20MB жёсткий лимит
                    await progress_message.edit_text(
                        f"❌ Файл превышает максимальный лимит!\n\n"
                        f"📁 Размер файла: {file.file_size / (1024*1024):.1f}MB\n"
                        f"📏 Лимит Telegram Bot API: 20MB (жёсткий)\n\n"
                        f"💡 Уменьшите размер файла до 20MB или меньше"
                    )
                    return
                
                # Скачиваем файл
                if file.file_size > 15 * 1024 * 1024:  # 15MB+
                    # Для файлов больше 15MB используем увеличенный таймаут
                    download_task = asyncio.create_task(file.download_to_drive(temp_input_path))
                    try:
                        await asyncio.wait_for(download_task, timeout=300)  # 5 минут для больших файлов
                    except asyncio.TimeoutError:
                        await progress_message.edit_text(
                            f"❌ Таймаут скачивания (5 минут)!\n\n"
                            f"📁 Файл слишком большой: {file.file_size / (1024*1024):.1f}MB\n"
                            f"💡 Попробуйте файл меньшего размера"
                        )
                        return
                else:
                    await file.download_to_drive(temp_input_path)
                
                # Логируем размер скачанного файла
                if temp_input_path.exists():
                    downloaded_size = temp_input_path.stat().st_size
                    downloaded_size_mb = downloaded_size / (1024*1024)
                    logger.info(f"✅ Файл скачан:")
                    logger.info(f"   📏 Реальный размер: {downloaded_size_mb:.2f}MB ({downloaded_size} bytes)")
                    logger.info(f"   📂 Путь: {temp_input_path}")
                    
                    # Сравниваем размеры
                    if abs(downloaded_size - file.file_size) > 1024:  # Разница больше 1KB
                        logger.warning(f"⚠️ Размеры не совпадают! API: {file.file_size} bytes, файл: {downloaded_size} bytes")
                else:
                    logger.error(f"❌ Файл не был скачан: {temp_input_path} не существует")
                
            except Exception as download_error:
                error_msg = str(download_error)
                logger.error(f"Ошибка скачивания файла: {error_msg}")
                
                if "File is too big" in error_msg or "too large" in error_msg or "Request Entity Too Large" in error_msg:
                    await progress_message.edit_text(
                        f"❌ Telegram не может скачать такой большой файл!\n\n"
                        f"🔍 Причины:\n"
                        f"• Файл больше лимитов Bot API\n"
                        f"• Отправлен как документ (без сжатия)\n"
                        f"• Проблемы с сетью\n\n"
                        f"💡 Решения:\n"
                        f"• Сожмите видео до 15-20MB\n"
                        f"• Отправьте с телефона как ВИДЕО (не документ)\n"
                        f"• Используйте более короткое видео\n\n"
                        f"📱 С телефона Telegram автоматически сжимает видео!"
                    )
                elif "timeout" in error_msg.lower():
                    await progress_message.edit_text(
                        f"❌ Таймаут при скачивании файла!\n\n"
                        f"📡 Возможные причины:\n"
                        f"• Медленное интернет-соединение\n"
                        f"• Файл слишком большой для скачивания\n\n"
                        f"💡 Попробуйте файл меньшего размера."
                    )
                else:
                    await progress_message.edit_text(
                        f"❌ Ошибка скачивания файла!\n\n"
                        f"🔍 Детали: {error_msg}\n\n"
                        f"💡 Попробуйте:\n"
                        f"• Отправить файл меньшего размера\n"
                        f"• Повторить попытку\n"
                        f"• Отправить с телефона"
                    )
                return
            
            await progress_message.edit_text("🔄 Обрабатываю видео...")
            
            # Получаем информацию о видео
            video_info = await video_processor.get_video_info(temp_input_path)
            input_size_mb = temp_input_path.stat().st_size / (1024 * 1024)
            
            # Всегда создаем 6 вариантов
            await progress_message.edit_text(f"🔄 Создаю {variant_count} вариантов видео...")
            
            variants = await video_processor.create_multiple_variants(
                temp_input_path, 
                settings.output_dir,
                variant_count
            )
            
            if not variants:
                await progress_message.edit_text("❌ Ошибка при создании вариантов")
                return
            
            # Отправляем все варианты
            await progress_message.edit_text("📤 Отправляю варианты...")
            
            for i, variant in enumerate(variants):
                try:
                    with open(variant['path'], 'rb') as video_file:
                        await message.reply_video(
                            video=video_file,
                            caption=f"✅ Вариант {i+1}/{len(variants)}: {variant['name']}\n\n"
                                   f"📐 Исходный размер: {video_info['width']}x{video_info['height']}\n"
                                   f"📐 Новый размер: 1080x1920 (Stories)\n"
                                   f"⏱ Длительность: {video_info['duration']:.1f}с\n"
                                   f"📁 Размер: {variant['size_mb']:.1f}MB\n"
                                   f"🎯 Качество: CRF {variant['quality']}\n"
                                   f"🎨 Цвет рамки: {variant['frame_color']}\n"
                                   f"🖼 Толщина рамки: {variant['frame_thickness']} ({variant['frame_thickness_px']}px)",
                            supports_streaming=True,
                            read_timeout=60,
                            write_timeout=60
                        )
                except Exception as upload_error:
                    logger.error(f"Ошибка отправки варианта {i+1}: {upload_error}")
            
            # Очищаем временные файлы вариантов
            for variant in variants:
                video_processor.cleanup_temp_files(variant['path'])
            
            # Очищаем временные данные пользователя
            context.user_data.clear()
            
            # Удаляем сообщение о прогрессе и завершаем
            await progress_message.delete()
            return
            
        except Exception as e:
            logger.error(f"Ошибка обработки видео для пользователя {user_id}: {e}")
            await message.reply_text(
                f"❌ Произошла ошибка при обработке видео: {str(e)}"
            )
        
        finally:
            # Небольшая задержка перед удалением файлов
            await asyncio.sleep(0.5)
            # Очищаем временные файлы
            video_processor.cleanup_temp_files(temp_input_path, temp_output_path)
    
    async def run(self):
        """Запуск бота"""
        logger.info("Запуск VideoBot...")
        
        # Создаем необходимые директории
        settings.temp_dir.mkdir(exist_ok=True)
        settings.output_dir.mkdir(exist_ok=True)
        
        # Инициализируем приложение
        await self.application.initialize()
        
        try:
            # Запускаем бота
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            # Ждем бесконечно
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
        finally:
            # Корректно останавливаем
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()


async def main():
    """Главная функция"""
    if not settings.bot_token:
        logger.error("BOT_TOKEN не установлен! Проверьте файл .env")
        return False
    
    bot = VideoBot()
    await bot.run()
    return True


if __name__ == "__main__":
    asyncio.run(main()) 