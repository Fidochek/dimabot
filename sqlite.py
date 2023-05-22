#!/bin/python3

import sqlite3 as sq
import datetime
from config import SUPER_ADMIN

async def start_db():
    global db, cur

    db = sq.connect('dima.db')
    cur = db.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT)')
    user = cur.execute("SELECT 1 FROM admins WHERE user_id == '{}'".format(SUPER_ADMIN[0])).fetchone()
    if not user:
        cur.execute("INSERT INTO admins(user_id, name) VALUES(?, ?)", SUPER_ADMIN)
    db.commit()

    cur.execute('CREATE TABLE IF NOT EXISTS number(num INTEGER PRIMARY KEY)')
    number = cur.execute("SELECT 1 FROM number").fetchone()
    if not number:
        cur.execute("INSERT INTO number VALUES(?)", ('1'))
    db.commit()

    cur.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, first_name TEXT, username TEXT)')
    db.commit()

    cur.execute('CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, message_id INTEGER UNIQUE, text TEXT, user_id INTEGER, first_name TEXT, username TEXT, date_time TEXT, is_post INTEGER)')
    db.commit()

    cur.execute('CREATE TABLE IF NOT EXISTS votes(id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, user_id INTEGER, vote INTEGER)')
    db.commit()

    cur.execute('CREATE TABLE IF NOT EXISTS comment(comm INTEGER PRIMARY KEY)')
    comm = cur.execute("SELECT 1 FROM comment").fetchone()
    if not comm:
        cur.execute("INSERT INTO comment VALUES(?)", ('1'))
    db.commit()

async def check_rights():
    users = cur.execute("SELECT user_id FROM admins").fetchall()
    user = [i[0] for i in users]
    db.commit()
    return user

async def add_admin(state):
    async with state.proxy() as data:
        user = cur.execute("SELECT 1 FROM admins WHERE user_id == '{}'".format(data['user_id'])).fetchone()
        if not user:
            cur.execute("INSERT INTO admins(user_id, name) VALUES(?, ?)", (data['user_id'], data['name']))
        db.commit()

async def add_message(message_id, text, user_id, first_name, username, is_post):
    message = cur.execute("SELECT 1 FROM messages WHERE message_id == '{}'".format(message_id)).fetchone()
    if not message:
        cur.execute("INSERT INTO messages(message_id, text, user_id, first_name, username, date_time, is_post) VALUES(?, ?, ?, ?, ?, ?, ?)", (message_id, text, user_id, first_name, username, datetime.datetime.now(), is_post))
    db.commit()

async def add_user(user_id, first_name, username):
    user = cur.execute("SELECT 1 FROM users WHERE user_id == '{}'".format(user_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO users(user_id, first_name, username) VALUES(?, ?, ?)", (user_id, first_name, f'@{username}'))
    db.commit()

async def set_vote(post_id, user_id, vote):
    vot = cur.execute("SELECT 1 FROM votes WHERE post_id == '{}' AND user_id == '{}'".format(post_id, user_id)).fetchone()
    if vot:
        cur.execute("UPDATE votes SET vote = '{}' WHERE post_id = '{}' AND user_id = '{}'".format(vote, post_id, user_id))
    else:
        cur.execute("INSERT INTO votes(post_id, user_id, vote) VALUES(?, ?, ?)",(post_id, user_id, vote))
    db.commit()

async def check_if_voted(post_id, user_id, vote):
    vote = cur.execute("SELECT 1 FROM votes WHERE post_id == '{}' AND user_id == '{}' AND vote == '{}'".format(post_id, user_id, vote)).fetchone()
    if vote:
        return True
    db.commit()

async def like_count(post_id):
    count = cur.execute("SELECT COUNT(*) FROM votes WHERE post_id == '{}' AND vote == '1'".format(post_id)).fetchone()
    db.commit()
    return count[0]

async def dislike_count(post_id):
    count = cur.execute("SELECT COUNT(*) FROM votes WHERE post_id == '{}' AND vote == '0'".format(post_id)).fetchone()
    db.commit()
    return count[0]

async def get_num():
    num = cur.execute("SELECT num FROM number").fetchone()
    db.commit()
    return num[0]

async def set_num(num: int):
    cur.execute("UPDATE number SET num = '{}'".format(num))
    db.commit()

async def check_top():
    tops = cur.execute("select first_name, count(username) from messages where is_post = 1 group by first_name order by count(username) desc limit 3").fetchall()
    return tops

async def check_comment():
    comm = cur.execute("SELECT comm FROM comment").fetchone()
    db.commit()
    return comm[0]

async def set_comment(comm):
    cur.execute("UPDATE comment SET comm = '{}'".format(comm))
    db.commit()