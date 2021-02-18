import sqlite3 as sql


def user_exists(chat_id):
    con = sql.connect("data.db")
    cur = con.cursor()
    cur.execute("SELECT chat_id FROM users")
    result = cur.fetchall()
    con.close()
    if result:
        return True
    return False


def add_user_record(chat_id):
    # TODO use ORM
    con = sql.connect("data.db")
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO users (chat_id) VALUES (?)", (chat_id,))
    except Exception as e:
        print(e)
    con.commit()
    con.close()


def set_forward(chat_id, forward_to):
    if not user_exists(chat_id):
        add_user_record(chat_id)
    con = sql.connect("data.db")
    cur = con.cursor()
    cur.execute("UPDATE users SET forward = ? WHERE chat_id = ?", (forward_to, chat_id))
    con.commit()
    con.close()


def get_forward(chat_id):
    con = sql.connect("data.db")
    cur = con.cursor()
    cur.execute("SELECT forward FROM users WHERE chat_id = ?", (chat_id,))
    forward = cur.fetchall()
    con.close()
    if forward[0][0] == "NO":
        return False
    return forward[0][0]