import asyncio
import random
import logging
from pathlib import Path
from typing import Tuple, Optional
import ffmpeg
from config import VIDEO_ASPECT_RATIOS, settings

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Класс для обработки видео с использованием FFmpeg"""
    
    def __init__(self):
        self.temp_dir = settings.temp_dir
        self.output_dir = settings.output_dir
    
    async def get_video_info(self, video_path: Path) -> dict:
        """Получает информацию о видео"""
        try:
            probe = ffmpeg.probe(str(video_path))
            video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
            
            return {
                'width': int(video_info['width']),
                'height': int(video_info['height']),
                'duration': float(video_info.get('duration', 0)),
                'codec': video_info['codec_name'],
                'fps': eval(video_info.get('r_frame_rate', '30/1'))
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о видео: {e}")
            raise
    
    def get_random_aspect_ratio(self) -> Tuple[int, int]:
        """Возвращает случайное соотношение сторон"""
        ratio_name = random.choice(list(VIDEO_ASPECT_RATIOS.keys()))
        width, height = VIDEO_ASPECT_RATIOS[ratio_name]
        logger.info(f"Выбрано соотношение сторон: {ratio_name} ({width}x{height})")
        return width, height
    
    def get_random_frame_color(self) -> str:
        """Возвращает случайный цвет для рамки"""
        colors = [
            'black',      # Чёрный
            'white',      # Белый  
            'red',        # Красный
            'blue',       # Синий
            'green',      # Зелёный
            'yellow',     # Жёлтый
            'purple',     # Фиолетовый
            'orange',     # Оранжевый
            'pink',       # Розовый
            'gray',       # Серый
            'navy',       # Тёмно-синий
            'brown',      # Коричневый
            '#FF6B6B',    # Коралловый
            '#4ECDC4',    # Бирюзовый
            '#45B7D1',    # Голубой
            '#96CEB4',    # Мятный
            '#FECA57',    # Жёлтый персик
            '#FF9FF3',    # Светло-розовый
            '#54A0FF',    # Ярко-синий
            '#5F27CD'     # Фиолетовый тёмный
        ]
        selected_color = random.choice(colors)
        logger.info(f"Выбран цвет рамки: {selected_color}")
        return selected_color
    
    def get_random_frame_thickness(self) -> dict:
        """Возвращает случайную толщину рамки"""
        # Варианты толщины рамки в пикселях и их описания
        thickness_options = [
            {'pixels': 10, 'name': 'Ультратонкая', 'description': '10px'},
            {'pixels': 20, 'name': 'Тонкая', 'description': '20px'},
            {'pixels': 35, 'name': 'Средняя', 'description': '35px'},
            {'pixels': 50, 'name': 'Толстая', 'description': '50px'},
            {'pixels': 75, 'name': 'Очень толстая', 'description': '75px'},
            {'pixels': 100, 'name': 'Сверхтолстая', 'description': '100px'},
            {'pixels': 150, 'name': 'Мега-рамка', 'description': '150px'},
        ]
        
        selected = random.choice(thickness_options)
        logger.info(f"Выбрана толщина рамки: {selected['name']} ({selected['description']})")
        return selected
    
    def calculate_resize_params(self, original_width: int, original_height: int, 
                              target_width: int, target_height: int, frame_thickness: int = 20) -> dict:
        """Вычисляет параметры для изменения размера с сохранением пропорций и рамкой"""
        
        # Учитываем толщину рамки при расчёте доступного пространства
        available_width = target_width - (frame_thickness * 2)
        available_height = target_height - (frame_thickness * 2)
        
        # Вычисляем соотношения сторон
        original_ratio = original_width / original_height
        available_ratio = available_width / available_height
        
        if original_ratio > available_ratio:
            # Видео шире доступного пространства - масштабируем по ширине
            scale_width = available_width
            scale_height = int(available_width / original_ratio)
            # Центрируем по вертикали в доступном пространстве
            vertical_space = available_height - scale_height
            pad_top = frame_thickness + (vertical_space // 2)
            pad_bottom = target_height - scale_height - pad_top
            pad_left = pad_right = frame_thickness
        else:
            # Видео выше доступного пространства - масштабируем по высоте
            scale_height = available_height
            scale_width = int(available_height * original_ratio)
            # Центрируем по горизонтали в доступном пространстве
            horizontal_space = available_width - scale_width
            pad_left = frame_thickness + (horizontal_space // 2)
            pad_right = target_width - scale_width - pad_left
            pad_top = pad_bottom = frame_thickness
        
        return {
            'scale_width': scale_width,
            'scale_height': scale_height,
            'pad_top': pad_top,
            'pad_bottom': pad_bottom,
            'pad_left': pad_left,
            'pad_right': pad_right,
            'frame_thickness': frame_thickness
        }
    
    async def compress_and_resize_video(self, input_path: Path, output_path: Path,
                                      target_width: Optional[int] = None, 
                                      target_height: Optional[int] = None) -> dict:
        """
        Сжимает видео без потери качества и применяет случайные рамки
        ОПТИМИЗИРОВАНО ДЛЯ СКОРОСТИ
        """
        try:
            # Получаем информацию о исходном видео
            video_info = await self.get_video_info(input_path)
            original_width = video_info['width']
            original_height = video_info['height']
            
            # Если размеры не указаны, используем финальный размер Stories
            if not target_width or not target_height:
                target_width, target_height = 1080, 1920
            
            # Получаем случайную толщину рамки
            frame_thickness_info = self.get_random_frame_thickness()
            frame_thickness = frame_thickness_info['pixels']
            
            # Вычисляем параметры изменения размера с учетом рамки
            resize_params = self.calculate_resize_params(
                original_width, original_height, target_width, target_height, frame_thickness
            )
            
            logger.info(f"Обработка видео: {original_width}x{original_height} -> {target_width}x{target_height}")
            logger.info(f"Толщина рамки: {frame_thickness_info['name']} ({frame_thickness_info['description']})")
            
            # Создаем FFmpeg pipeline с оптимизацией для скорости
            input_stream = ffmpeg.input(str(input_path))
            
            # Берём только видео поток
            video_stream = input_stream['v']
            audio_stream = input_stream['a']
            
            # Масштабируем видео
            scaled = ffmpeg.filter(video_stream, 'scale', 
                                 resize_params['scale_width'], 
                                 resize_params['scale_height'])
            
            # Добавляем цветные рамки (padding) до финального размера 1080x1920
            frame_color = self.get_random_frame_color()
            padded = ffmpeg.filter(scaled, 'pad',
                                 target_width, target_height,  # Финальный размер всегда 1080x1920
                                 resize_params['pad_left'],   # Отступ слева (с учетом рамки)
                                 resize_params['pad_top'],    # Отступ сверху (с учетом рамки)
                                 color=frame_color)
            
            # ОПТИМИЗИРОВАННЫЕ настройки для скорости
            try:
                # Пытаемся с аудио
                output = ffmpeg.output(
                    padded, audio_stream,
                    str(output_path),
                    vcodec='libx264',
                    crf=25,  # Немного снижено качество для скорости (было 23)
                    preset='fast',  # УСКОРЕНИЕ: было 'medium'
                    acodec='aac',  # Кодек для аудио
                    audio_bitrate='128k',  # Качественное аудио
                    pix_fmt='yuv420p',  # Совместимость с большинством плееров
                    movflags='faststart',  # Быстрый старт воспроизведения
                    tune='fastdecode',  # УСКОРЕНИЕ: оптимизация для быстрого декодирования
                    **{'b:v': '1800k'},  # Увеличен битрейт для компенсации быстрого preset
                    maxrate='2200k',  # Максимальный битрейт
                    bufsize='4400k',   # Размер буфера
                    threads='0'  # УСКОРЕНИЕ: использовать все доступные ядра
                )
            except:
                # Если ошибка с аудио, то только видео
                output = ffmpeg.output(
                    padded,
                    str(output_path),
                    vcodec='libx264',
                    crf=25,  # Немного снижено качество для скорости
                    preset='fast',  # УСКОРЕНИЕ
                    pix_fmt='yuv420p',
                    movflags='faststart',
                    tune='fastdecode',  # УСКОРЕНИЕ
                    **{'b:v': '1800k'},
                    maxrate='2200k',
                    bufsize='4400k',
                    threads='0'  # УСКОРЕНИЕ
                )
            
            # Запускаем обработку
            process = await asyncio.create_subprocess_exec(
                *ffmpeg.compile(output, overwrite_output=True),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Ждём завершения процесса
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Неизвестная ошибка FFmpeg"
                logger.error(f"FFmpeg завершился с ошибкой: {error_msg}")
                return False
            
            logger.info(f"Видео успешно обработано: {output_path}")
            return {
                'success': True, 
                'frame_color': frame_color,
                'frame_thickness': frame_thickness_info['name'],
                'frame_thickness_px': frame_thickness_info['pixels']
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке видео: {e}")
            return {'success': False, 'frame_color': None, 'frame_thickness': None, 'frame_thickness_px': None}
    
    async def create_multiple_variants(self, input_path: Path, output_dir: Path, count: int = 3) -> list:
        """
        Создает несколько вариантов видео с разным качеством/размером
        ОПТИМИЗИРОВАНО ДЛЯ СКОРОСТИ И ПАРАЛЛЕЛЬНОСТИ
        """
        
        # ОПТИМИЗИРОВАННЫЕ настройки качества для быстрой обработки
        quality_settings = [
            {"name": "Высокое", "crf": 20, "bitrate": "2000k", "maxrate": "2500k", "preset": "fast"},
            {"name": "Среднее", "crf": 23, "bitrate": "1500k", "maxrate": "2000k", "preset": "fast"},
            {"name": "Компактное", "crf": 26, "bitrate": "1000k", "maxrate": "1300k", "preset": "fast"},
            {"name": "Минимальное", "crf": 28, "bitrate": "700k", "maxrate": "900k", "preset": "faster"},
            {"name": "Ультра-компактное", "crf": 30, "bitrate": "500k", "maxrate": "600k", "preset": "faster"},
            {"name": "Максимальное", "crf": 18, "bitrate": "2500k", "maxrate": "3000k", "preset": "fast"}
        ]
        
        # Ограничиваем количество вариантов
        count = min(count, len(quality_settings))
        selected_settings = quality_settings[:count]
        
        results = []
        
        for i, settings in enumerate(selected_settings):
            output_path = output_dir / f"variant_{i+1}_{settings['name'].lower()}.mp4"
            
            try:
                logger.info(f"Создаю вариант {i+1}/{count}: {settings['name']} (preset: {settings['preset']})")
                
                # Получаем информацию о видео
                video_info = await self.get_video_info(input_path)
                original_width = video_info['width']
                original_height = video_info['height']
                
                # Всегда 1080x1920 финальный размер
                target_width, target_height = 1080, 1920
                
                # Получаем уникальную толщину рамки для каждого варианта
                frame_thickness_info = self.get_random_frame_thickness()
                frame_thickness = frame_thickness_info['pixels']
                
                # Вычисляем параметры изменения размера с учетом рамки
                resize_params = self.calculate_resize_params(
                    original_width, original_height, target_width, target_height, frame_thickness
                )
                
                # Создаем FFmpeg pipeline
                input_stream = ffmpeg.input(str(input_path))
                video_stream = input_stream['v']
                
                try:
                    audio_stream = input_stream['a']
                    has_audio = True
                except:
                    has_audio = False
                
                # Масштабируем видео
                scaled = ffmpeg.filter(video_stream, 'scale', 
                                     resize_params['scale_width'], 
                                     resize_params['scale_height'])
                
                # Добавляем цветные рамки до финального размера 1080x1920
                frame_color = self.get_random_frame_color()
                padded = ffmpeg.filter(scaled, 'pad',
                                     target_width, target_height,  # Финальный размер всегда 1080x1920
                                     resize_params['pad_left'],   # Отступ слева (с учетом рамки)
                                     resize_params['pad_top'],    # Отступ сверху (с учетом рамки)
                                     color=frame_color)
                
                # Создаем выходной поток с ОПТИМИЗИРОВАННЫМИ настройками качества
                if has_audio:
                    output = ffmpeg.output(
                        padded, audio_stream,
                        str(output_path),
                        vcodec='libx264',
                        crf=settings['crf'],
                        preset=settings['preset'],  # Используем оптимизированный preset
                        acodec='aac',
                        audio_bitrate='128k',
                        pix_fmt='yuv420p',
                        movflags='faststart',
                        tune='fastdecode',  # УСКОРЕНИЕ
                        **{'b:v': settings['bitrate']},
                        maxrate=settings['maxrate'],
                        bufsize=f"{int(settings['maxrate'][:-1]) * 2}k",
                        threads='0'  # УСКОРЕНИЕ: использовать все ядра
                    )
                else:
                    output = ffmpeg.output(
                        padded,
                        str(output_path),
                        vcodec='libx264',
                        crf=settings['crf'],
                        preset=settings['preset'],  # Используем оптимизированный preset
                        pix_fmt='yuv420p',
                        movflags='faststart',
                        tune='fastdecode',  # УСКОРЕНИЕ
                        **{'b:v': settings['bitrate']},
                        maxrate=settings['maxrate'],
                        bufsize=f"{int(settings['maxrate'][:-1]) * 2}k",
                        threads='0'  # УСКОРЕНИЕ
                    )
                
                # Запускаем обработку
                process = await asyncio.create_subprocess_exec(
                    *ffmpeg.compile(output, overwrite_output=True),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Неизвестная ошибка FFmpeg"
                    logger.error(f"FFmpeg завершился с ошибкой для варианта {i+1}: {error_msg}")
                    continue
                
                # Добавляем информацию о созданном файле
                if output_path.exists():
                    file_size = output_path.stat().st_size / (1024 * 1024)
                    results.append({
                        'path': output_path,
                        'name': settings['name'],
                        'size_mb': file_size,
                        'quality': settings['crf'],
                        'frame_color': frame_color,
                        'frame_thickness': frame_thickness_info['name'],
                        'frame_thickness_px': frame_thickness_info['pixels']
                    })
                    logger.info(f"Вариант {i+1} готов: {file_size:.1f}MB, рамка: {frame_thickness_info['name']}, preset: {settings['preset']}")
                
            except Exception as e:
                logger.error(f"Ошибка создания варианта {i+1}: {e}")
                continue
        
        return results
    
    async def get_video_thumbnail(self, video_path: Path, output_path: Path, 
                                time_offset: float = 1.0) -> bool:
        """Создает превью видео"""
        try:
            (
                ffmpeg
                .input(str(video_path), ss=time_offset)
                .output(str(output_path), vframes=1, format='image2', vcodec='png')
                .overwrite_output()
                .run_async()
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка создания превью: {e}")
            return False
    
    def cleanup_temp_files(self, *file_paths: Path):
        """Удаляет временные файлы с повторными попытками"""
        import time
        
        for file_path in file_paths:
            if not file_path.exists():
                continue
                
            # Пытаемся удалить файл несколько раз с задержкой
            for attempt in range(3):
                try:
                    file_path.unlink()
                    logger.info(f"Удален временный файл: {file_path}")
                    break
                except PermissionError:
                    if attempt < 2:  # Не последняя попытка
                        logger.info(f"Файл занят, ждём... попытка {attempt + 1}/3")
                        time.sleep(1)  # Ждём 1 секунду
                    else:
                        logger.warning(f"Не удалось удалить файл {file_path} после 3 попыток")
                except Exception as e:
                    logger.warning(f"Ошибка удаления файла {file_path}: {e}")
                    break


# Создаем глобальный экземпляр процессора
video_processor = VideoProcessor() 