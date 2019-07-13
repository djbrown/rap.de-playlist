import sqlite3
from typing import List, Tuple

from flask import g

DATABASE = "database.sqlite3"


def _get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    db = _get_db()
    db.execute("CREATE TABLE posts (id, name, url)")
    # db.commit()


def insert_posts(posts: List[Tuple[int, str, str]]):
    db = _get_db()
    db.cursor().executemany("INSERT INTO posts (id, name, url) VALUES (?, ?, ?)", posts)
    db.commit()
