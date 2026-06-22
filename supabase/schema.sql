-- ADITI Phase 0 schema (Supabase Postgres)
-- Run in Supabase SQL Editor after creating your project.
--
-- If `vector` extension fails here, enable it first in Supabase Dashboard:
-- Database → Extensions → search "vector" → Enable

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    image_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    ocr_text TEXT,
    ocr_confidence DOUBLE PRECISION,
    subject TEXT,
    topic TEXT,
    question_type TEXT,
    retrieval_match_id UUID,
    solver_used TEXT CHECK (solver_used IN ('sympy', 'wolfram', 'llm_only')),
    verified BOOLEAN DEFAULT FALSE,
    confidence_flag TEXT DEFAULT 'needs_review'
        CHECK (confidence_flag IN ('verified', 'unverified', 'needs_review')),
    final_answer TEXT,
    explanation TEXT,
    error_message TEXT,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corpus_solutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT,
    question_text TEXT NOT NULL,
    solution_text TEXT,
    official_answer TEXT,
    embedding VECTOR(768)
);

CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    student_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reported_issue TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_questions_student_id ON questions(student_id);
CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status);
CREATE INDEX IF NOT EXISTS idx_questions_confidence_flag ON questions(confidence_flag);
CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at DESC);

ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Students can view own questions"
    ON questions FOR SELECT
    USING (auth.uid() = student_id);

CREATE POLICY "Students can insert own questions"
    ON questions FOR INSERT
    WITH CHECK (auth.uid() = student_id);

CREATE POLICY "Students can view own feedback"
    ON feedback FOR SELECT
    USING (auth.uid() = student_id);

CREATE POLICY "Students can insert feedback on own questions"
    ON feedback FOR INSERT
    WITH CHECK (
        auth.uid() = student_id
        AND EXISTS (
            SELECT 1 FROM questions q
            WHERE q.id = question_id AND q.student_id = auth.uid()
        )
    );

-- Storage bucket for question images (create in Supabase Dashboard or via API):
-- Bucket name: question-images (private)
-- Allowed MIME: image/jpeg, image/png, image/webp
