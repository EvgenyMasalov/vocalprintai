"""
VocalSeparator — разделение вокала от инструментов через Demucs (Meta).

Используется только при обнаружении feat/collaboration в треке.
Demucs разделяет аудио на 4 стема: vocals, drums, bass, other.
Мы извлекаем только vocals для дальнейшей классификации по полу.
"""

import os
import tempfile
import subprocess
import shutil
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VocalSeparator:
    """
    Разделение вокала от инструментов с помощью Demucs.
    
    Demucs (htdemucs) — state-of-the-art модель от Meta для source separation.
    Разделяет на 4 стема: vocals, drums, bass, other.
    Модель загружается при первом вызове и кэшируется.
    """

    def __init__(self, model_name: str = "htdemucs", device: str = "cpu"):
        """
        Args:
            model_name: Название модели Demucs. 
                        'htdemucs' — лучшее качество/скорость на CPU.
                        'htdemucs_ft' — fine-tuned, чуть лучше, но медленнее.
            device: 'cpu' или 'cuda' (если есть GPU).
        """
        self.model_name = model_name
        self.device = device
        self._model = None

    def _ensure_model_loaded(self):
        """Ленивая загрузка модели Demucs при первом использовании."""
        if self._model is not None:
            return

        try:
            import demucs.api
            self._separator = demucs.api.Separator(
                model=self.model_name,
                device=self.device,
                progress=False,
            )
            self._model = True
            logger.info(f"[VocalSeparator] Модель {self.model_name} загружена на {self.device}")
        except ImportError:
            logger.warning("[VocalSeparator] demucs.api не найден, используем CLI fallback")
            self._separator = None
            self._model = "cli"
        except Exception as e:
            logger.error(f"[VocalSeparator] Ошибка загрузки модели: {e}")
            self._separator = None
            self._model = "cli"

    def separate_vocals(self, wav_path: str) -> Optional[str]:
        """
        Извлекает вокальный стем из аудиофайла.
        
        Args:
            wav_path: Путь к WAV файлу (моно или стерео).
            
        Returns:
            Путь к WAV файлу с чистым вокалом, или None при ошибке.
            Вызывающий код отвечает за удаление временного файла.
        """
        if not os.path.exists(wav_path):
            logger.error(f"[VocalSeparator] Файл не найден: {wav_path}")
            return None

        self._ensure_model_loaded()

        if self._model == "cli":
            return self._separate_via_cli(wav_path)
        else:
            return self._separate_via_api(wav_path)

    def _separate_via_api(self, wav_path: str) -> Optional[str]:
        """Разделение через Python API Demucs."""
        try:
            import torch
            import soundfile as sf
            
            # Demucs API: separate_audio_file возвращает dict стемов
            origin, separated = self._separator.separate_audio_file(wav_path)
            
            # separated — dict: {'vocals': tensor, 'drums': tensor, 'bass': tensor, 'other': tensor}
            vocals = separated["vocals"]
            
            # Конвертируем tensor в numpy
            if isinstance(vocals, torch.Tensor):
                vocals_np = vocals.cpu().numpy()
            else:
                vocals_np = vocals
            
            # vocals_np shape: (channels, samples) — берём среднее для моно
            if vocals_np.ndim == 2:
                vocals_mono = vocals_np.mean(axis=0)
            else:
                vocals_mono = vocals_np
            
            # Сохраняем во временный файл
            fd, vocal_path = tempfile.mkstemp(suffix="_vocals.wav", prefix="vocalprint_")
            os.close(fd)
            
            # Demucs работает с sr=44100 по умолчанию
            sf.write(vocal_path, vocals_mono, samplerate=44100)
            
            logger.info(f"[VocalSeparator] Вокал извлечён (API): {vocal_path}")
            return vocal_path
            
        except Exception as e:
            logger.error(f"[VocalSeparator] Ошибка API разделения: {e}")
            return self._separate_via_cli(wav_path)

    def _separate_via_cli(self, wav_path: str) -> Optional[str]:
        """
        Fallback: разделение через CLI команду demucs.
        Работает даже если API недоступен.
        """
        try:
            # Создаём временную директорию для выходных файлов
            output_dir = tempfile.mkdtemp(prefix="demucs_output_")
            
            cmd = [
                "python", "-m", "demucs",
                "--two-stems", "vocals",  # Разделяем только на vocals + accompaniment
                "-n", self.model_name,
                "-d", self.device,
                "--out", output_dir,
                wav_path
            ]
            
            logger.info(f"[VocalSeparator] Запуск CLI: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 минут максимум
            )
            
            if result.returncode != 0:
                logger.error(f"[VocalSeparator] CLI ошибка: {result.stderr}")
                shutil.rmtree(output_dir, ignore_errors=True)
                return None
            
            # Demucs сохраняет в: output_dir/htdemucs/filename/vocals.wav
            base_name = os.path.splitext(os.path.basename(wav_path))[0]
            vocals_path = os.path.join(output_dir, self.model_name, base_name, "vocals.wav")
            
            if not os.path.exists(vocals_path):
                # Попробуем найти файл рекурсивно
                for root, dirs, files in os.walk(output_dir):
                    for f in files:
                        if f == "vocals.wav":
                            vocals_path = os.path.join(root, f)
                            break
            
            if not os.path.exists(vocals_path):
                logger.error(f"[VocalSeparator] vocals.wav не найден в {output_dir}")
                shutil.rmtree(output_dir, ignore_errors=True)
                return None
            
            # Копируем vocals.wav во временный файл и чистим директорию demucs
            fd, final_path = tempfile.mkstemp(suffix="_vocals.wav", prefix="vocalprint_")
            os.close(fd)
            shutil.copy2(vocals_path, final_path)
            
            # Удаляем директорию demucs output
            shutil.rmtree(output_dir, ignore_errors=True)
            
            logger.info(f"[VocalSeparator] Вокал извлечён (CLI): {final_path}")
            return final_path
            
        except subprocess.TimeoutExpired:
            logger.error("[VocalSeparator] CLI таймаут (>5 мин)")
            shutil.rmtree(output_dir, ignore_errors=True)
            return None
        except Exception as e:
            logger.error(f"[VocalSeparator] CLI ошибка: {e}")
            if 'output_dir' in locals():
                shutil.rmtree(output_dir, ignore_errors=True)
            return None


# Синглтон для переиспользования модели между запросами
_separator_instance = None

def get_vocal_separator(device: str = "cpu") -> VocalSeparator:
    """Возвращает синглтон VocalSeparator для переиспользования загруженной модели."""
    global _separator_instance
    if _separator_instance is None:
        _separator_instance = VocalSeparator(device=device)
    return _separator_instance


if __name__ == "__main__":
    # Тест
    separator = VocalSeparator()
    # result = separator.separate_vocals("test.wav")
    # print(f"Vocals path: {result}")
