DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id  INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL    UNIQUE,
    duration  TEXT    NOT NULL DEFAULT 'any',
    search_for  TEXT    NOT NULL DEFAULT 'video',
    forward TEXT    NOT NULL    DEFAULT 'NO'
)