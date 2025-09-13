CREATE TABLE IF NOT EXISTS hands (
    id UUID PRIMARY KEY,
    board TEXT[],
    hole_cards JSONB,
    actions_log TEXT[],
    stacks_start JSONB,
    status TEXT
);