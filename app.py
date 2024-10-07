from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = '12345678'


def get_db_connection():
    conn = sqlite3.connect('new_user_data.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('copylog.html')


@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        return "Passwords do not match"

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                     (username, email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return "Email already exists"
    finally:
        conn.close()

    return render_template("copylog.html")


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['pswd']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user is None:
        return "Email not found"

    if not check_password_hash(user['password'], password):
        return "Incorrect password"

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['is_admin'] = user['is_admin']

    if user['is_admin']:
        return redirect(url_for('admin'))
    else:
        return render_template('index.html')


@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('index'))

    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    orders = conn.execute('SELECT orders.*, users.username FROM orders JOIN users ON orders.user_id = users.id').fetchall()

    # Fetch completed orders and cancelled orders
    completed_orders = conn.execute('''
        SELECT orders.*, users.username, completed_orders.completed_time 
        FROM orders 
        JOIN users ON orders.user_id = users.id 
        JOIN completed_orders ON orders.id = completed_orders.order_id
    ''').fetchall()

    # Convert completed_time strings to datetime objects
    completed_orders = [dict(order) for order in completed_orders]
    for order in completed_orders:
        completed_time_str = order.get('completed_time')
        if completed_time_str:

            format_str = '%Y-%m-%d %H:%M:%S'
            order['completed_time'] = datetime.strptime(completed_time_str.split('.')[0], format_str)
        else:
            order['completed_time'] = None  # Handle None values
    cancelled_orders = conn.execute('''
        SELECT orders.*, users.username, cancelled_orders.cancelled_time
        FROM orders 
        JOIN users ON orders.user_id = users.id 
        JOIN cancelled_orders ON orders.id = cancelled_orders.order_id
    ''').fetchall()

    # Convert cancelled_time strings to datetime objects
    cancelled_orders = [dict(order) for order in cancelled_orders]
    for order in cancelled_orders:
        cancelled_time_str = order.get('cancelled_time')
        if cancelled_time_str:

            format_str = '%Y-%m-%d %H:%M:%S'
            order['cancelled_time'] = datetime.strptime(cancelled_time_str.split('.')[0], format_str)
        else:
            order['cancelled_time'] = None

    conn.close()

    return render_template('admin.html', users=users, orders=orders, completed_orders=completed_orders, cancelled_orders=cancelled_orders)


@app.route('/logout')
def logout():
    session.clear()
    return render_template('copylog.html')

@app.route('/one')
def one():
    return render_template('1.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/buy')
def buy():
    return render_template('buy.html')

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    conn = get_db_connection()
    cart_items = conn.execute('SELECT * FROM cart WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()

    return render_template('cart.html', cart_items=cart_items)


@app.route('/details')
def details():
    return render_template('order_details.html')

@app.route('/submit_order', methods=['POST'])
def submit_order():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    product_name = request.form['product_name']
    total_amount = request.form['total_amount']
    payment_method = request.form['payment_method']
    shipping_method = request.form['shipping_method']
    delivery_address = request.form['delivery_address']

    delivery_time = datetime.now() + timedelta(minutes=random.randint(1, 3))

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO orders (user_id, product_name, total_amount, payment_method, shipping_method, delivery_address, delivery_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, product_name, total_amount, payment_method, shipping_method, delivery_address, delivery_time.strftime('%Y-%m-%d %H:%M:%S'), 'pending'))
    conn.commit()
    conn.close()

    return redirect(url_for('order_details'))

@app.route('/order_details')
def order_details():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE user_id = ? AND status = "pending"', (user_id,))
    pending_orders = cursor.fetchall()

    cursor.execute('''
        SELECT orders.*, completed_orders.order_id as comp_order_id 
        FROM orders 
        JOIN completed_orders 
        ON orders.id = completed_orders.order_id 
        WHERE orders.user_id = ?
    ''', (user_id,))
    completed_orders = cursor.fetchall()

    cursor.execute('''
        SELECT orders.*, cancelled_orders.order_id as canc_order_id 
        FROM orders 
        JOIN cancelled_orders 
        ON orders.id = cancelled_orders.order_id 
        WHERE orders.user_id = ?
    ''', (user_id,))
    cancelled_orders = cursor.fetchall()

    conn.close()

    return render_template('order_details.html', pending_orders=pending_orders, completed_orders=completed_orders, cancelled_orders=cancelled_orders)

@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    if 'user_id' not in session:
        return 'Unauthorized', 403

    order_id = request.form['order_id']
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        current_time = datetime.now() # Adjusted current time
        conn.execute('UPDATE orders SET status = "cancelled" WHERE id = ? AND user_id = ?', (order_id, user_id))
        conn.execute('INSERT INTO cancelled_orders (user_id, order_id, cancelled_time) VALUES (?, ?, ?)', (user_id, order_id, current_time))
        conn.commit()
        conn.close()
        return 'Order cancelled successfully', 200
    except sqlite3.Error as e:
        print("Error cancelling order:", e)
        return 'Error cancelling order', 500

@app.route('/receive_order', methods=['POST'])
def receive_order():
    if 'user_id' not in session:
        return 'Unauthorized', 403

    order_id = request.form['order_id']
    user_id = session['user_id']

    conn = get_db_connection()
    try:
        current_time = datetime.now() # Adjusted current time
        conn.execute('UPDATE orders SET status = "completed" WHERE id = ? AND user_id = ?', (order_id, user_id))
        conn.execute('INSERT INTO completed_orders (user_id, order_id, completed_time) VALUES (?, ?, ?)', (user_id, order_id, current_time))
        conn.commit()
        conn.close()
        return 'Order received successfully', 200
    except sqlite3.Error as e:
        print("Error marking order as completed:", e)
        return 'Error marking order as completed', 500


@app.route('/delete_order', methods=['POST'])
def delete_order():
    order_id = request.form['order_id']

    # Assuming you have a function to get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete the order from the orders table
        cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))

        # Commit the transaction
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error deleting order: {e}")
        return jsonify({'status': 'failed', 'reason': 'Server error'}), 500



@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    product_name = request.form.get('product_name')
    price = request.form.get('price')
    image_url = request.form.get('image_url')  # Get the image URL from the form data

    print(f"Adding to cart: user_id={user_id}, product_name={product_name}, price={price}, image_url={image_url}")  # Debugging statement

    if not product_name or not price or not image_url:
        return 'Missing product name, price, or image URL', 400

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO cart (user_id, product_name, price, image_url) VALUES (?, ?, ?, ?)', (user_id, product_name, price, image_url))
        conn.commit()
        return redirect(url_for('cart'))
    except sqlite3.Error as e:
        print("Error adding product to cart:", e)
        return 'Failed to add product to cart', 500
    finally:
        conn.close()


@app.route('/checkout/<product_id>', methods=['GET'])
def checkout_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    # Retrieve product information from the database based on product_id
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM cart WHERE id = ?', (product_id,)).fetchone()
    conn.close()

    if not product:
        return 'Product not found', 404

    return render_template('buy.html', product=product)


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    product_id = request.form.get('product_id')

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM cart WHERE id = ? AND user_id = ?', (product_id, user_id))
        conn.commit()
        return redirect(url_for('cart'))
    except sqlite3.Error as e:
        print("Error removing product from cart:", e)
        return 'Failed to remove product from cart', 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
