import os
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters from .env or defaults
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/vocalprint")

def seed_key_profiles():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Enable pgvector and register it with psycopg2
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        
        # Create table if not exists
        with open("schema_pgvector.sql", "r") as f:
            cur.execute(f.read())
        
        # Krumhansl-Schmuckler Profiles (C Major / C Minor)
        major_base = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_base = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        print("Seeding Major keys...")
        for i in range(12):
            # Roll RIGHT by i positions: shifts the C profile to represent key i
            # e.g., i=0 → C Major, i=1 → C# Major (profile[0] becomes the weight for C#)
            profile = np.roll(major_base, i)
            # Normalize with L2 norm for cosine similarity in pgvector
            norm = np.linalg.norm(profile)
            if norm > 0:
                profile = profile / norm
            name = f"{key_names[i]} Major"
            cur.execute(
                "INSERT INTO key_profiles (key_name, note, mode, profile_vector) VALUES (%s, %s, %s, %s) ON CONFLICT (key_name) DO UPDATE SET profile_vector = EXCLUDED.profile_vector",
                (name, key_names[i], "major", profile.tolist())
            )
            
        print("Seeding Minor keys...")
        for i in range(12):
            profile = np.roll(minor_base, i)
            # Normalize with L2 norm for cosine similarity in pgvector
            norm = np.linalg.norm(profile)
            if norm > 0:
                profile = profile / norm
            name = f"{key_names[i]} Minor"
            cur.execute(
                "INSERT INTO key_profiles (key_name, note, mode, profile_vector) VALUES (%s, %s, %s, %s) ON CONFLICT (key_name) DO UPDATE SET profile_vector = EXCLUDED.profile_vector",
                (name, key_names[i], "minor", profile.tolist())
            )
            
        conn.commit()
        print("Success: All 24 key profiles seeded into PostgreSQL!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    seed_key_profiles()
