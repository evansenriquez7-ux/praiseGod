import sqlite3

def main():
    conn = sqlite3.connect("backend/app/ccmed.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM question_flags ORDER BY created_at DESC LIMIT 10")
    for row in cur.fetchall():
        print(dict(row))

if __name__ == "__main__":
    main()
