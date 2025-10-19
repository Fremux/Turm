-- Migration: Create organization_units, task_capability_mappings and tasks tables
-- Run this migration to add support for organization structure and task management

-- Create thread table for chat history (required for LangGraph checkpointer)
CREATE TABLE IF NOT EXISTS thread (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create organization_units table
CREATE TABLE IF NOT EXISTS organization_units (
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(200) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    position VARCHAR(500),
    unit_type VARCHAR(50) NOT NULL,
    description VARCHAR(2000),
    parent_id INTEGER REFERENCES organization_units(id),
    level INTEGER NOT NULL DEFAULT 0,
    path VARCHAR(2000),
    capabilities JSON DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Create indexes for organization_units
CREATE INDEX IF NOT EXISTS idx_org_unit_external_id ON organization_units(external_id);
CREATE INDEX IF NOT EXISTS idx_org_unit_type ON organization_units(unit_type);
CREATE INDEX IF NOT EXISTS idx_org_unit_parent_id ON organization_units(parent_id);
CREATE INDEX IF NOT EXISTS idx_org_unit_is_active ON organization_units(is_active);

-- Create task_capability_mappings table
CREATE TABLE IF NOT EXISTS task_capability_mappings (
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    action_type VARCHAR(200) NOT NULL,
    keywords JSON DEFAULT '[]',
    handled_by_unit_id INTEGER NOT NULL REFERENCES organization_units(id),
    escalate_to_unit_id INTEGER REFERENCES organization_units(id),
    priority INTEGER NOT NULL DEFAULT 5
);

-- Create indexes for task_capability_mappings
CREATE INDEX IF NOT EXISTS idx_task_cap_category ON task_capability_mappings(category);
CREATE INDEX IF NOT EXISTS idx_task_cap_handled_by ON task_capability_mappings(handled_by_unit_id);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    id SERIAL PRIMARY KEY,
    summary VARCHAR(200) NOT NULL,
    description VARCHAR(2000) NOT NULL,
    assignee VARCHAR(100) NOT NULL DEFAULT 'сотрудник',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    category_id INTEGER REFERENCES categories(id),
    assigned_role_id INTEGER REFERENCES organization_units(id),
    created_by INTEGER,
    original_message VARCHAR(1000),
    completed_at TIMESTAMP,
    completed_by VARCHAR(100),
    notes VARCHAR(2000),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for tasks
CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_category_id ON tasks(category_id);
CREATE INDEX IF NOT EXISTS idx_task_assigned_role_id ON tasks(assigned_role_id);

-- Create a trigger to automatically update updated_at on tasks
CREATE OR REPLACE FUNCTION update_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_tasks_updated_at ON tasks;
CREATE TRIGGER trigger_update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_tasks_updated_at();

