import re
from typing import Dict, Optional, List

def parse_artist_name(name_str: str) -> Dict[str, Optional[str]]:
    """
    Parses an artist name string that may contain a group in parentheses.
    Examples:
    - "Freddie Mercury (Queen)" -> primary="Freddie Mercury", secondary="Queen"
    - "Queen (Freddie Mercury)" -> primary="Queen", secondary="Freddie Mercury"
    - "The Beatles" -> primary="The Beatles", secondary=None
    
    Returns a dictionary with:
    - primary: The part outside parentheses
    - secondary: The part inside parentheses
    - search_query: A combined string for search engines
    - safe_filename: A sanitized string for filenames
    """
    if not name_str:
        return {
            "primary": "Unknown",
            "secondary": None,
            "search_query": "Unknown",
            "safe_filename": "Unknown"
        }
    
    # Find parentheses content
    match = re.search(r'\((.*?)\)', name_str)
    
    if match:
        secondary = match.group(1).strip()
        # Remove parentheses and content from original
        primary = re.sub(r'\(.*?\)', '', name_str).strip()
    else:
        primary = name_str.strip()
        secondary = None
    
    # Generate search query (joining with space)
    search_query = f"{primary} {secondary}" if secondary else primary
    
    # Generate safe filename
    # Remove characters illegal in Windows/Linux filenames
    filename_base = f"{primary}_{secondary}" if secondary else primary
    safe_filename = re.sub(r'[<>:"/\\|?*\(\)]', '', filename_base)
    safe_filename = safe_filename.replace(" ", "_").strip("_")
    
    return {
        "primary": primary,
        "secondary": secondary,
        "search_query": search_query,
        "safe_filename": safe_filename
    }

def estimate_key(y, sr):
    """
    Estimates the musical key using Krumhansl-Schmuckler correlation.
    Uses HPSS to isolate harmonic content and CQT for chromagram.
    Attempts PostgreSQL pgvector search if available, otherwise falls back to manual.
    """
    import numpy as np
    import librosa
    import os
    import psycopg2
    from pgvector.psycopg2 import register_vector

    # 1. HPSS & Chromagram
    y_harmonic = librosa.effects.harmonic(y)
    chromagram = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
    chroma_vals = np.sum(chromagram, axis=1)
    
    # Normalize chroma vector
    if np.max(chroma_vals) > 0:
        chroma_vals = chroma_vals / np.max(chroma_vals)

    # 2. Try PostgreSQL pgvector search
    db_url = os.getenv("DATABASE_URL")
    if db_url and "postgresql" in db_url:
        try:
            conn = psycopg2.connect(db_url)
            register_vector(conn)
            cur = conn.cursor()
            
            # Use cosine distance (<=>) to find the closest match
            cur.execute(
                "SELECT key_name FROM key_profiles ORDER BY profile_vector <=> %s LIMIT 1",
                (chroma_vals.tolist(),)
            )
            res = cur.fetchone()
            conn.close()
            if res:
                print(f"[KeyDetection] Found in DB: {res[0]}")
                return res[0]
        except Exception as e:
            print(f"[KeyDetection] DB search failed, falling back to manual: {e}")

    # 3. Manual Fallback: Krumhansl-Schmuckler Profiles (C Major / C Minor)
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    # Normalize profiles too for fair correlation
    major_profile = major_profile / np.max(major_profile)
    minor_profile = minor_profile / np.max(minor_profile)
    
    major_corrs = []
    minor_corrs = []
    
    for i in range(12):
        major_corrs.append(np.corrcoef(major_profile, np.roll(chroma_vals, -i))[0, 1])
        minor_corrs.append(np.corrcoef(minor_profile, np.roll(chroma_vals, -i))[0, 1])
        
    best_major_idx = np.argmax(major_corrs)
    best_minor_idx = np.argmax(minor_corrs)
    
    key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    if major_corrs[best_major_idx] > minor_corrs[best_minor_idx]:
        return f"{key_names[best_major_idx]} Major"
    else:
        return f"{key_names[best_minor_idx]} Minor"

def detect_feat_collaboration(track_title: str, artist: str = "") -> Dict[str, Optional[str]]:
    """
    Определяет наличие feat/ft./featuring/& в названии трека или артисте.
    Это триггер для запуска разделения вокала (Demucs + F0 классификация).
    
    Паттерны:
    - "Song feat. Artist2"
    - "Song ft. Artist2"  
    - "Song (feat. Artist2)"
    - "Song featuring Artist2"
    - "Artist1 & Artist2 - Song"
    - "Artist1 x Artist2"
    - "Artist1, Artist2"
    
    Args:
        track_title: Название трека.
        artist: Строка с артистом(ами).
        
    Returns:
        {
            "is_feat": bool,
            "primary_artist": str | None,
            "featured_artists": list[str],
            "clean_title": str,  # Название без feat-части
            "trigger": str | None,  # Какой паттерн сработал
        }
    """
    combined = f"{artist} {track_title}".strip()
    is_feat = False
    featured_artists: List[str] = []
    clean_title = track_title.strip()
    trigger = None
    primary_artist = artist.strip() if artist else None

    # Паттерн 1: feat./ft./featuring в названии трека
    feat_pattern = re.compile(
        r'[\(\[\s]*(feat\.?|ft\.?|featuring)\s+(.+?)[\)\]\s]*$',
        re.IGNORECASE
    )
    match = feat_pattern.search(track_title)
    if match:
        is_feat = True
        trigger = match.group(1).lower()
        feat_part = match.group(2).strip().rstrip(')')
        # Разделяем нескольких featured артистов
        featured_artists = [a.strip() for a in re.split(r'[,&]', feat_part) if a.strip()]
        # Убираем feat-часть из названия
        clean_title = track_title[:match.start()].strip()

    # Паттерн 2: feat./ft./featuring в строке артиста
    if not is_feat and artist:
        match_artist = feat_pattern.search(artist)
        if match_artist:
            is_feat = True
            trigger = match_artist.group(1).lower()
            feat_part = match_artist.group(2).strip().rstrip(')')
            featured_artists = [a.strip() for a in re.split(r'[,&]', feat_part) if a.strip()]
            primary_artist = artist[:match_artist.start()].strip()

    # Паттерн 3: "&" или "x" между артистами (Artist1 & Artist2)
    if not is_feat and artist:
        collab_pattern = re.compile(r'^(.+?)\s*(?:&|×|x|X|\+)\s*(.+)$')
        match_collab = collab_pattern.match(artist)
        if match_collab:
            is_feat = True
            trigger = "&"
            primary_artist = match_collab.group(1).strip()
            featured_artists = [a.strip() for a in re.split(r'[,&×xX\+]', match_collab.group(2)) if a.strip()]

    # Паттерн 4: Запятая в артисте (Artist1, Artist2, Artist3)
    if not is_feat and artist and ',' in artist:
        parts = [a.strip() for a in artist.split(',') if a.strip()]
        if len(parts) >= 2:
            is_feat = True
            trigger = ","
            primary_artist = parts[0]
            featured_artists = parts[1:]

    return {
        "is_feat": is_feat,
        "primary_artist": primary_artist,
        "featured_artists": featured_artists,
        "clean_title": clean_title,
        "trigger": trigger,
    }


if __name__ == "__main__":
    # Tests — parse_artist_name
    test_cases = [
        "Freddie Mercury (Queen)",
        "Queen (Freddie Mercury)",
        "The Beatles",
        "(Solo) Artist Name",
        "Artist Name ()"
    ]
    for tc in test_cases:
        print(f"Input: {tc} -> {parse_artist_name(tc)}")

    # Tests — detect_feat_collaboration
    print("\n--- Feat Detection Tests ---")
    feat_tests = [
        ("Flowers", "Miley Cyrus"),
        ("Under Pressure", "Queen & David Bowie"),
        ("HUMBLE. feat. Rihanna", "Kendrick Lamar"),
        ("Beautiful Liar", "Beyoncé, Shakira"),
        ("Señorita (ft. Camila Cabello)", "Shawn Mendes"),
        ("Lady Marmalade (feat. Christina Aguilera, Lil' Kim, Mýa & P!nk)", "Moulin Rouge"),
        ("Numb/Encore", "Linkin Park x Jay-Z"),
    ]
    for title, artist in feat_tests:
        result = detect_feat_collaboration(title, artist)
        print(f"  '{artist} - {title}' -> feat={result['is_feat']}, "
              f"trigger={result['trigger']}, featured={result['featured_artists']}")
