import os
import psutil
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def get_file_size_formatted(file_path: Path) -> str:
    """Возвращает размер файла в читаемом формате"""
    if not file_path.exists():
        return "0 B"
    
    size = file_path.stat().st_size
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_system_info() -> Dict[str, Any]:
    """Возвращает информацию о системе"""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения информации о системе: {e}")
        return {}


def validate_video_file(file_path: Path) -> Dict[str, Any]:
    """Валидирует видео файл"""
    result = {
        'is_valid': False,
        'error': None,
        'info': {}
    }
    
    try:
        if not file_path.exists():
            result['error'] = "Файл не существует"
            return result
        
        if file_path.stat().st_size == 0:
            result['error'] = "Файл пустой"
            return result
        
        # Проверяем расширение
        from config import SUPPORTED_VIDEO_FORMATS
        if file_path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
            result['error'] = f"Неподдерживаемый формат: {file_path.suffix}"
            return result
        
        result['is_valid'] = True
        result['info'] = {
            'size': get_file_size_formatted(file_path),
            'extension': file_path.suffix.lower(),
            'name': file_path.name
        }
        
    except Exception as e:
        result['error'] = f"Ошибка валидации: {str(e)}"
        logger.error(f"Ошибка валидации файла {file_path}: {e}")
    
    return result


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """Удаляет старые файлы из директории"""
    if not directory.exists():
        return
    
    current_time = datetime.now().timestamp()
    max_age_seconds = max_age_hours * 3600
    
    for file_path in directory.iterdir():
        try:
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    logger.info(f"Удален старый файл: {file_path}")
        except Exception as e:
            logger.warning(f"Не удалось удалить файл {file_path}: {e}")


def create_error_response(error_message: str, user_friendly: bool = True) -> str:
    """Создает сообщение об ошибке для пользователя"""
    if user_friendly:
        error_map = {
            'ffmpeg': "🔧 Ошибка обработки видео. Попробуйте другой файл.",
            'size': "📏 Файл слишком большой для обработки.",
            'format': "📋 Неподдерживаемый формат видео.",
            'download': "📥 Ошибка скачивания файла.",
            'upload': "📤 Ошибка отправки результата.",
            'permission': "🔒 Недостаточно прав для обработки.",
            'network': "🌐 Проблемы с сетевым соединением."
        }
        
        for key, message in error_map.items():
            if key in error_message.lower():
                return message
        
        return "❌ Произошла ошибка. Попробуйте позже."
    
    return f"❌ Ошибка: {error_message}"


def log_user_action(user_id: int, action: str, details: str = ""):
    """Логирует действия пользователя"""
    logger.info(f"Пользователь {user_id}: {action} | {details}")


def get_processing_stats() -> Dict[str, Any]:
    """Возвращает статистику обработки"""
    from config import settings
    
    stats = {
        'temp_files': 0,
        'output_files': 0,
        'temp_size': 0,
        'output_size': 0
    }
    
    try:
        # Подсчитываем файлы во временной директории
        if settings.temp_dir.exists():
            temp_files = list(settings.temp_dir.glob('*'))
            stats['temp_files'] = len(temp_files)
            stats['temp_size'] = sum(f.stat().st_size for f in temp_files if f.is_file())
        
        # Подсчитываем файлы в выходной директории
        if settings.output_dir.exists():
            output_files = list(settings.output_dir.glob('*'))
            stats['output_files'] = len(output_files)
            stats['output_size'] = sum(f.stat().st_size for f in output_files if f.is_file())
    
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
    
    return stats 