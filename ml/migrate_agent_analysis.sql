-- Migration: Add agent_analysis table
-- This migration adds the agent_analysis table for storing ReAct agent results

-- Create agent_analysis table for storing ReAct agent results
CREATE TABLE IF NOT EXISTS agent_analysis (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    problem TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.0,
    reasoning TEXT NOT NULL DEFAULT '',
    solution TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

-- Create indexes for agent_analysis table
CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON agent_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_session_id ON agent_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_analysis_category ON agent_analysis(category);
CREATE INDEX IF NOT EXISTS idx_analysis_priority ON agent_analysis(priority);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON agent_analysis(created_at);

