import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def read_users():
    conn = get_db_connection()
    users = conn.execute('SELECT username, user_id, role FROM users').fetchall()
    conn.close()
    
    print("\n--- Users in Database ---")
    if users:
        for user in users:
            print(f"Username: {user['username']}, User ID: {user['user_id']}, Role: {user['role']}")
    else:
        print("No users found.")
    print("-------------------------")

if __name__ == '__main__':
    read_users() 