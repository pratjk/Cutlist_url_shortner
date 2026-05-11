CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code TEXT UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    clicks INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_id INTEGER,
    click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    country TEXT,
    city TEXT,
    referrer TEXT,
    FOREIGN KEY(url_id) REFERENCES urls(id)
);
