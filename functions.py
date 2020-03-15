import sqlite3 as sql

def user_exists(chat_id):
    con = sql.connect('data.db')
    cur = con.cursor()
    cur.execute('SELECT chat_id FROM users')
    result = cur.fetchall()
    con.close()
    if result:
        return True
    return False

def add_user_record(chat_id):
    con = sql.connect('data.db')
    cur = con.cursor()
    try:
        cur.execute('INSERT INTO users (chat_id, duration) VALUES (?, ?)', (chat_id, 'any'))
    except Exception as e:
        print(e)
    con.commit()
    con.close()

def get_duration(chat_id):
    if not user_exists(chat_id):
        add_user_record(chat_id)
    con = sql.connect('data.db')
    cur = con.cursor()
    cur.execute('SELECT duration FROM users WHERE chat_id = ?', (chat_id,))
    duration = cur.fetchall()
    con.close()
    return duration[0][0]

def set_duration(chat_id, duration):
    if not user_exists(chat_id):
        add_user_record(chat_id)
    con = sql.connect('data.db')
    cur = con.cursor()
    cur.execute('UPDATE users SET duration = ? WHERE chat_id = ?', (duration, chat_id))
    con.commit()
    con.close()