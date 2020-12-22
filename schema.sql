CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    nickname TEXT,
    hash TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS friends_add(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,
    UNIQUE(from_id,to_id)
);


CREATE TABLE IF NOT EXISTS friends_list(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    fone INTEGER NOT NULL,
    ftwo INTEGER NOT NULL,
    UNIQUE(fone,ftwo)
);


CREATE TABLE IF NOT EXISTS group_user(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status_show INTEGER NOT NULL DEFAULT 1 CHECK(status_show IN (0,1)),
    UNIQUE(group_id,user_id)
);


CREATE TABLE IF NOT EXISTS group_ids(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    group_name TEXT
);


CREATE INDEX IF NOT EXISTS idx_group_user_user_id ON group_user(user_id);
CREATE INDEX IF NOT EXISTS idx_group_user_group_id ON group_user(group_id);


CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    time INTEGER NOT NULL
);


