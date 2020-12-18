import sqlite3
import io

def init_db():
    db = sqlite3.connect("chatroom.db",
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = sqlite3.Row

    with io.open('schema.sql', mode="r", encoding="utf-8") as f:
        db.executescript(f.read())
    
    db.close()

init_db()