-- Database schema for the application
-- Generated from SQLModel classes

-- Create user table
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create session table
CREATE TABLE IF NOT EXISTS session (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

-- Create thread table
CREATE TABLE IF NOT EXISTS thread (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create user_entity table for storing extracted entities
CREATE TABLE IF NOT EXISTS user_entity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_value TEXT NOT NULL,
    context TEXT,
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

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

-- Create indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_session_user_id ON session(user_id);
CREATE INDEX IF NOT EXISTS idx_entity_user_id ON user_entity(user_id);
CREATE INDEX IF NOT EXISTS idx_entity_session_id ON user_entity(session_id);
CREATE INDEX IF NOT EXISTS idx_entity_type ON user_entity(entity_type);
CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON agent_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_session_id ON agent_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_analysis_category ON agent_analysis(category);
CREATE INDEX IF NOT EXISTS idx_analysis_priority ON agent_analysis(priority);
