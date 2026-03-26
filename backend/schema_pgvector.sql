-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for Key Profiles
CREATE TABLE IF NOT EXISTS key_profiles (
    id SERIAL PRIMARY KEY,
    key_name TEXT NOT NULL UNIQUE, -- e.g., "C Major"
    note TEXT NOT NULL,           -- e.g., "C"
    mode TEXT NOT NULL,           -- "major" or "minor"
    profile_vector vector(12) NOT NULL -- pgvector(12)
);

-- Index for cosine similarity search
CREATE INDEX ON key_profiles USING ivfflat (profile_vector vector_cosine_ops) WITH (lists = 100);
