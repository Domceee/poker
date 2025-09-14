CREATE TABLE IF NOT EXISTS hands (
                id TEXT PRIMARY KEY,
                stack TEXT NOT NULL,
                hands TEXT NOT NULL,
                actions TEXT NOT NULL,
                result TEXT NOT NULL
            );