-- Migration: Add MATATAG support columns
-- Run this SQL manually on the PostgreSQL database to add MATATAG support

-- Add MATATAG ELO and placement columns to student_profiles
ALTER TABLE student_profiles 
ADD COLUMN IF NOT EXISTS elo_matatag FLOAT DEFAULT 1200.0;

ALTER TABLE student_profiles 
ADD COLUMN IF NOT EXISTS placement_done_matatag BOOLEAN DEFAULT FALSE;

-- Verify columns were added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'student_profiles' 
AND column_name IN ('elo_matatag', 'placement_done_matatag');
