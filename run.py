#!/usr/bin/env python3
"""
VideoBot - Телеграм бот для сжатия видео
Запуск основного приложения
"""

import asyncio
import sys
import logging
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot import main
from config import settings
from utils import cleanup_old_files

logger = logging.getLogger(__name__)


def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    try:
        import ffmpeg
        import telegram
        logger.info("✅ Все зависимости найдены")
        return True
    except ImportError as e:
        logger.error(f"❌ Отсутствует зависимость: {e}")
        return False


def check_ffmpeg():
    """Проверяет доступность FFmpeg"""
    try:
        import ffmpeg
        # Пробуем выполнить простую команду
        ffmpeg.probe('non_existent_file.mp4')
    except ffmpeg.Error:
        # Это ожидаемо для несуществующего файла
        logger.info("✅ FFmpeg доступен")
        return True
    except Exception as e:
        logger.error(f"❌ FFmpeg недоступен: {e}")
        logger.error("Установите FFmpeg: https://ffmpeg.org/download.html")
        return False


def setup_directories():
    """Создает необходимые директории"""
    try:
        settings.temp_dir.mkdir(exist_ok=True)
        settings.output_dir.mkdir(exist_ok=True)
        logger.info(f"✅ Директории созданы: {settings.temp_dir}, {settings.output_dir}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания директорий: {e}")
        return False


def cleanup_startup():
    """Очистка при запуске"""
    try:
        # Очищаем старые временные файлы
        cleanup_old_files(settings.temp_dir, max_age_hours=1)
        cleanup_old_files(settings.output_dir, max_age_hours=24)
        logger.info("✅ Очистка временных файлов завершена")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка очистки: {e}")


def run_bot():
    """Запускает бота с проверками"""
    
    # Проверяем конфигурацию
    if not settings.bot_token:
        logger.error("❌ BOT_TOKEN не установлен!")
        logger.error("Создайте файл .env с токеном бота")
        return False
    
    # Проверяем зависимости
    if not check_dependencies():
        return False
    
    # Проверяем FFmpeg
    if not check_ffmpeg():
        return False
    
    # Создаем директории
    if not setup_directories():
        return False
    
    # Очистка при запуске
    cleanup_startup()
    
    logger.info("🚀 Запускаем VideoBot...")
    logger.info(f"📊 Максимальный размер файла: {settings.max_file_size_mb}MB")
    logger.info(f"📁 Временные файлы: {settings.temp_dir}")
    logger.info(f"📁 Выходные файлы: {settings.output_dir}")
    
    # Запускаем основное приложение
    try:
        asyncio.run(main())
        return True
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
        return True
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return False


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('videobot.log', encoding='utf-8')
        ]
    )
    
    logger.info("=" * 50)
    logger.info("🎬 VideoBot Starting...")
    logger.info("=" * 50)
    
    # Запускаем бота
    success = run_bot()
    
    if success:
        logger.info("✅ Бот завершен успешно")
    else:
        logger.error("❌ Бот завершен с ошибкой")
        sys.exit(1) 