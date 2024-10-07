import sqlite3
from werkzeug.security import generate_password_hash


def initialize_db():
    try:
        connection = sqlite3.connect('new_user_data.db')
        with connection:
            connection.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    is_admin BOOLEAN NOT NULL DEFAULT 0
                );
            ''')
            connection.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_name TEXT,
                    total_amount REAL,
                    payment_method TEXT,
                    shipping_method TEXT,
                    delivery_address TEXT,
                    delivery_time TEXT,
                    status TEXT DEFAULT 'Pending',  
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
            ''')
            connection.execute('''
                CREATE TABLE IF NOT EXISTS completed_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_id INTEGER,
                    completed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(order_id) REFERENCES orders(id)
                );
            ''')

            connection.execute('''
                CREATE TABLE IF NOT EXISTS cancelled_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_id INTEGER,
                    cancelled_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(order_id) REFERENCES orders(id)
                );
            ''')

            connection.execute('DROP TABLE IF EXISTS cart;')
            connection.execute('''
                CREATE TABLE cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    image_url TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
            ''')
            print("Table 'cart' created successfully.")

        print("Database initialized successfully.")
    except sqlite3.Error as e:
        print("Error initializing database:", e)
    finally:
        connection.close()


def add_delivery_time_column():
    try:
        conn = sqlite3.connect('new_user_data.db')
        with conn:
            conn.execute('''
                ALTER TABLE orders ADD COLUMN delivery_time TEXT;
            ''')
        print("Column 'delivery_time' added successfully.")
    except sqlite3.Error as e:
        if "duplicate column name" in str(e):
            print("Column 'delivery_time' already exists.")
        else:
            print("Error adding 'delivery_time' column:", e)
    finally:
        conn.close()


def create_admin_user():
    try:
        conn = sqlite3.connect('new_user_data.db')
        with conn:
            conn.execute('''
                INSERT INTO users (username, email, password, is_admin)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'qwerty@gmail.com', generate_password_hash('0987654321', method='pbkdf2:sha256'), True))
        print("Admin user created successfully.")
    except sqlite3.IntegrityError:
        print("Admin user already exists")
    except sqlite3.Error as e:
        print("Error creating admin user:", e)
    finally:
        conn.close()


def mark_order_as_completed(user_id, order_id):
    try:
        conn = sqlite3.connect('new_user_data.db')
        with conn:
            conn.execute('''
                INSERT INTO completed_orders (user_id, order_id, completed_time)
                VALUES (?, ?, CURRENT_TIMESTAMP)  -- Explicitly setting completed_time
            ''', (user_id, order_id))
        print("Order marked as completed successfully.")
    except sqlite3.Error as e:
        print("Error marking order as completed:", e)
    finally:
        conn.close()


def mark_order_as_cancelled(user_id, order_id):
    try:
        conn = sqlite3.connect('new_user_data.db')
        with conn:
            conn.execute('''
                INSERT INTO cancelled_orders (user_id, order_id, cancelled_time)
                VALUES (?, ?, CURRENT_TIMESTAMP)  -- Explicitly setting cancelled_time
            ''', (user_id, order_id))
        print("Order marked as cancelled successfully.")
    except sqlite3.Error as e:
        print("Error marking order as cancelled:", e)
    finally:
        conn.close()

def add_status_column():
    try:
        conn = sqlite3.connect('new_user_data.db')
        with conn:
            conn.execute('''
                ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'Pending';
            ''')
        print("Column 'status' added successfully.")
    except sqlite3.Error as e:
        if "duplicate column name" in str(e):
            print("Column 'status' already exists.")
        else:
            print("Error adding 'status' column:", e)
    finally:
        conn.close()


def add_completed_time_column():
    try:
        conn = sqlite3.connect('new_user_data.db')
        with conn:
            conn.execute('''
                ALTER TABLE completed_orders ADD COLUMN completed_time TIMESTAMP;
            ''')
            conn.execute('''
                UPDATE completed_orders SET completed_time = CURRENT_TIMESTAMP;
            ''')
        print("Column 'completed_time' added successfully.")
    except sqlite3.Error as e:
        if "duplicate column name" in str(e):
            print("Column 'completed_time' already exists.")
        else:
            print("Error adding 'completed_time' column:", e)
    finally:
        conn.close()


def add_cancelled_time_column():
    try:
        conn = sqlite3.connect('new_user_data.db')
        with conn:
            conn.execute('''
                ALTER TABLE cancelled_orders ADD COLUMN cancelled_time TIMESTAMP;
            ''')
            conn.execute('''
                UPDATE cancelled_orders SET cancelled_time = CURRENT_TIMESTAMP;
            ''')
        print("Column 'cancelled_time' added successfully.")
    except sqlite3.Error as e:
        if "duplicate column name" in str(e):
            print("Column 'cancelled_time' already exists.")
        else:
            print("Error adding 'cancelled_time' column:", e)
    finally:
        conn.close()




if __name__ == "__main__":
    initialize_db()
    add_status_column()
    create_admin_user()
    add_completed_time_column()
    add_cancelled_time_column()

