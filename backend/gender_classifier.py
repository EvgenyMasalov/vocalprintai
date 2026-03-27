"""
VocalGenderClassifier — классификация вокальных сегментов по полу
через анализ основного тона (F0) с помощью librosa.

Лёгкий подход без нейросетей (pyannote.audio не нужен):
1. Разрезаем вокальную дорожку на сегменты по тишине
2. Для каждого сегмента вычисляем медианную частоту F0
3. Классифицируем: F0 > порога → женский, F0 < порога → мужской
4. Склеиваем только нужные сегменты

Типичные диапазоны F0:
- Мужской голос: 85–180 Hz
- Женский голос: 165–255 Hz
- Порог разделения: ~165 Hz (с гистерезисом)
"""

import os
import tempfile
import numpy as np
import librosa
import soundfile as sf
from typing import Optional, List, Tuple, Literal
import logging

logger = logging.getLogger(__name__)

# Пороги классификации F0 (в Hz)
FEMALE_F0_THRESHOLD = 165.0   # Выше этого — скорее женский
MALE_F0_THRESHOLD = 155.0     # Ниже этого — скорее мужской
# Между 155 и 165 — зона неопределённости, классифицируем по контексту

# Минимальная длина сегмента для анализа (в секундах)
MIN_SEGMENT_DURATION = 0.3

# Минимальная доля озвученных фреймов в сегменте для надёжной классификации
MIN_VOICED_RATIO = 0.3


class VocalGenderClassifier:
    """
    Классификация вокальных сегментов по полу через анализ F0 (librosa.yin).
    Минимальная нагрузка на сервер — только numpy + librosa, без GPU.
    """

    def __init__(
        self,
        female_threshold: float = FEMALE_F0_THRESHOLD,
        male_threshold: float = MALE_F0_THRESHOLD,
        sr: int = 22050,
    ):
        """
        Args:
            female_threshold: F0 выше этого значения → женский голос.
            male_threshold: F0 ниже этого значения → мужской голос.
            sr: Sample rate для загрузки аудио.
        """
        self.female_threshold = female_threshold
        self.male_threshold = male_threshold
        self.sr = sr

    def classify_segments(
        self, vocal_path: str
    ) -> List[dict]:
        """
        Разрезает вокальную дорожку на сегменты и классифицирует каждый.
        
        Args:
            vocal_path: Путь к WAV файлу с чистым вокалом (после Demucs).
            
        Returns:
            Список словарей:
            [
                {
                    "start_sample": int,
                    "end_sample": int,
                    "start_sec": float,
                    "end_sec": float,
                    "median_f0": float,
                    "gender": "female" | "male" | "unknown",
                    "confidence": float  # 0.0–1.0
                },
                ...
            ]
        """
        try:
            y, sr = librosa.load(vocal_path, sr=self.sr)
        except Exception as e:
            logger.error(f"[GenderClassifier] Ошибка загрузки {vocal_path}: {e}")
            return []

        # Разрезаем по тишине
        # top_db=25 — порог тишины (dB ниже пика)
        intervals = librosa.effects.split(y, top_db=25, frame_length=2048, hop_length=512)

        if len(intervals) == 0:
            logger.warning("[GenderClassifier] Не найдено вокальных сегментов")
            return []

        segments = []
        for start, end in intervals:
            duration = (end - start) / sr
            if duration < MIN_SEGMENT_DURATION:
                continue

            segment_audio = y[start:end]
            gender, median_f0, confidence = self._classify_segment(segment_audio, sr)

            segments.append({
                "start_sample": int(start),
                "end_sample": int(end),
                "start_sec": round(start / sr, 3),
                "end_sec": round(end / sr, 3),
                "median_f0": round(median_f0, 1) if median_f0 > 0 else 0.0,
                "gender": gender,
                "confidence": round(confidence, 2),
            })

        logger.info(
            f"[GenderClassifier] Найдено {len(segments)} сегментов: "
            f"{sum(1 for s in segments if s['gender'] == 'female')} женских, "
            f"{sum(1 for s in segments if s['gender'] == 'male')} мужских, "
            f"{sum(1 for s in segments if s['gender'] == 'unknown')} неопределённых"
        )

        return segments

    def _classify_segment(
        self, segment: np.ndarray, sr: int
    ) -> Tuple[str, float, float]:
        """
        Классифицирует один аудио-сегмент по полу.
        
        Returns:
            (gender, median_f0, confidence)
        """
        try:
            # Вычисляем F0 через YIN (быстрее чем pYIN, достаточно точный)
            f0 = librosa.yin(
                segment,
                fmin=librosa.note_to_hz('C2'),   # ~65 Hz
                fmax=librosa.note_to_hz('C6'),    # ~1047 Hz
                sr=sr,
                frame_length=2048,
                hop_length=512,
            )

            # Фильтруем невалидные значения
            # YIN может возвращать fmax при отсутствии тона
            fmax = librosa.note_to_hz('C6')
            fmin = librosa.note_to_hz('C2')
            valid_f0 = f0[(f0 > fmin) & (f0 < fmax * 0.95)]

            voiced_ratio = len(valid_f0) / len(f0) if len(f0) > 0 else 0

            if voiced_ratio < MIN_VOICED_RATIO or len(valid_f0) < 3:
                return "unknown", 0.0, 0.0

            median_f0 = float(np.median(valid_f0))

            # Классификация с уверенностью
            if median_f0 >= self.female_threshold:
                # Чем выше F0 над порогом, тем увереннее
                distance = median_f0 - self.female_threshold
                confidence = min(1.0, 0.6 + distance / 100.0)
                return "female", median_f0, confidence
            elif median_f0 <= self.male_threshold:
                distance = self.male_threshold - median_f0
                confidence = min(1.0, 0.6 + distance / 100.0)
                return "male", median_f0, confidence
            else:
                # Зона неопределённости (155–165 Hz)
                # Склоняемся к ближайшему порогу
                dist_to_female = median_f0 - self.male_threshold
                dist_to_male = self.female_threshold - median_f0
                total = dist_to_female + dist_to_male
                if dist_to_female >= dist_to_male:
                    return "female", median_f0, 0.5 + 0.1 * (dist_to_female / total)
                else:
                    return "male", median_f0, 0.5 + 0.1 * (dist_to_male / total)

        except Exception as e:
            logger.error(f"[GenderClassifier] Ошибка классификации сегмента: {e}")
            return "unknown", 0.0, 0.0

    def extract_female_vocal(self, vocal_path: str) -> Optional[str]:
        """
        Извлекает только женские вокальные сегменты из дорожки.
        
        Args:
            vocal_path: Путь к WAV с чистым вокалом.
            
        Returns:
            Путь к WAV файлу с только женским вокалом, или None если
            женских сегментов не найдено.
        """
        try:
            y, sr = librosa.load(vocal_path, sr=self.sr)
        except Exception as e:
            logger.error(f"[GenderClassifier] Ошибка загрузки: {e}")
            return None

        segments = self.classify_segments(vocal_path)
        
        if not segments:
            logger.warning("[GenderClassifier] Нет сегментов для фильтрации")
            return None

        female_segments = [s for s in segments if s["gender"] == "female"]

        if not female_segments:
            logger.warning("[GenderClassifier] Женские сегменты не обнаружены")
            return None

        # Собираем женские сегменты с плавными переходами (fade)
        fade_samples = int(0.01 * sr)  # 10ms fade для избежания щелчков
        
        female_audio_parts = []
        for seg in female_segments:
            start = seg["start_sample"]
            end = seg["end_sample"]
            chunk = y[start:end].copy()
            
            # Применяем fade in/out
            if len(chunk) > 2 * fade_samples:
                chunk[:fade_samples] *= np.linspace(0, 1, fade_samples)
                chunk[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            female_audio_parts.append(chunk)
            
            # Добавляем короткую тишину между сегментами (50ms)
            silence = np.zeros(int(0.05 * sr), dtype=np.float32)
            female_audio_parts.append(silence)

        if not female_audio_parts:
            return None

        # Склеиваем
        female_audio = np.concatenate(female_audio_parts)

        # Сохраняем
        fd, output_path = tempfile.mkstemp(suffix="_female_vocal.wav", prefix="vocalprint_")
        os.close(fd)
        sf.write(output_path, female_audio, samplerate=sr)

        total_duration = len(female_audio) / sr
        logger.info(
            f"[GenderClassifier] Женский вокал извлечён: {output_path} "
            f"({total_duration:.1f} сек, {len(female_segments)} сегментов)"
        )

        return output_path

    def extract_male_vocal(self, vocal_path: str) -> Optional[str]:
        """
        Извлекает только мужские вокальные сегменты из дорожки.
        Аналогично extract_female_vocal, но для мужского голоса.
        """
        try:
            y, sr = librosa.load(vocal_path, sr=self.sr)
        except Exception as e:
            logger.error(f"[GenderClassifier] Ошибка загрузки: {e}")
            return None

        segments = self.classify_segments(vocal_path)
        
        if not segments:
            return None

        male_segments = [s for s in segments if s["gender"] == "male"]

        if not male_segments:
            logger.warning("[GenderClassifier] Мужские сегменты не обнаружены")
            return None

        fade_samples = int(0.01 * sr)
        
        male_audio_parts = []
        for seg in male_segments:
            start = seg["start_sample"]
            end = seg["end_sample"]
            chunk = y[start:end].copy()
            
            if len(chunk) > 2 * fade_samples:
                chunk[:fade_samples] *= np.linspace(0, 1, fade_samples)
                chunk[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            male_audio_parts.append(chunk)
            silence = np.zeros(int(0.05 * sr), dtype=np.float32)
            male_audio_parts.append(silence)

        if not male_audio_parts:
            return None

        male_audio = np.concatenate(male_audio_parts)

        fd, output_path = tempfile.mkstemp(suffix="_male_vocal.wav", prefix="vocalprint_")
        os.close(fd)
        sf.write(output_path, male_audio, samplerate=sr)

        logger.info(
            f"[GenderClassifier] Мужской вокал извлечён: {output_path} "
            f"({len(male_audio) / sr:.1f} сек, {len(male_segments)} сегментов)"
        )

        return output_path

    def get_gender_stats(self, vocal_path: str) -> dict:
        """
        Возвращает статистику по гендерному распределению вокала.
        
        Returns:
            {
                "total_segments": int,
                "female_segments": int,
                "male_segments": int,
                "unknown_segments": int,
                "female_duration_sec": float,
                "male_duration_sec": float,
                "dominant_gender": "female" | "male" | "mixed",
                "avg_female_f0": float,
                "avg_male_f0": float,
            }
        """
        segments = self.classify_segments(vocal_path)
        
        female_segs = [s for s in segments if s["gender"] == "female"]
        male_segs = [s for s in segments if s["gender"] == "male"]
        unknown_segs = [s for s in segments if s["gender"] == "unknown"]

        female_dur = sum(s["end_sec"] - s["start_sec"] for s in female_segs)
        male_dur = sum(s["end_sec"] - s["start_sec"] for s in male_segs)

        avg_female_f0 = (
            float(np.mean([s["median_f0"] for s in female_segs]))
            if female_segs else 0.0
        )
        avg_male_f0 = (
            float(np.mean([s["median_f0"] for s in male_segs]))
            if male_segs else 0.0
        )

        # Определяем доминирующий пол
        if female_dur > male_dur * 1.5:
            dominant = "female"
        elif male_dur > female_dur * 1.5:
            dominant = "male"
        else:
            dominant = "mixed"

        return {
            "total_segments": len(segments),
            "female_segments": len(female_segs),
            "male_segments": len(male_segs),
            "unknown_segments": len(unknown_segs),
            "female_duration_sec": round(female_dur, 2),
            "male_duration_sec": round(male_dur, 2),
            "dominant_gender": dominant,
            "avg_female_f0": round(avg_female_f0, 1),
            "avg_male_f0": round(avg_male_f0, 1),
        }


if __name__ == "__main__":
    # Тест
    classifier = VocalGenderClassifier()
    # stats = classifier.get_gender_stats("vocals.wav")
    # print(stats)
    # female_path = classifier.extract_female_vocal("vocals.wav")
    # print(f"Female vocal: {female_path}")
