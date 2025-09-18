import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Dict, Tuple

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Токен бота
    bot_token: str = ""
    
    # Ограничения файлов
    max_file_size_mb: int = 50  # Максимальный размер файла в MB
    
    # Директории
    temp_dir: Path = Path("temp")
    output_dir: Path = Path("output")
    
    # Настройки FFmpeg
    ffmpeg_timeout: int = 300  # 5 минут
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Создаем экземпляр настроек
settings = Settings()

# Поддерживаемые форматы видео
SUPPORTED_VIDEO_FORMATS = {
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', 
    '.wmv', '.3gp', '.m4v', '.mpg', '.mpeg', '.ogv'
}

# Соотношения сторон для видео
VIDEO_ASPECT_RATIOS: Dict[str, Tuple[int, int]] = {
    "stories": (1080, 1920),    # Instagram/TikTok Stories
    "square": (1080, 1080),     # Квадратное
    "landscape": (1920, 1080),  # Ландшафтное
    "portrait": (1080, 1440),   # Портретное
    "classic": (1280, 720),     # Классическое HD
} 