import json
import sqlite3
import random
import string
import datetime
from pathlib import Path

# CONFIG
OPENFDA_JSON = 'drug-label-0001-of-0013.json'  # Path to your openFDA sample (full or partial JSON)
DB_PATH = 'pharmacy_sim.db'
NUM_USERS = 10
NUM_ORDERS = 20
MAX_ORDER_ITEMS = 4
LKR_PRICE_RANGE = (100, 5000)

# --- Helper functions ---
def random_string(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def random_phone():
    return '07' + ''.join(random.choices(string.digits, k=8))

def random_date(start, end):
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))

def random_address():
    return f"{random.randint(1, 200)}, {random.choice(['Colombo', 'Kandy', 'Galle', 'Jaffna', 'Kurunegala'])}, Sri Lanka"

# --- Schema ---
def create_schema(conn):
    c = conn.cursor()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        full_name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        role TEXT,
        created_at DATE
    );
    CREATE TABLE IF NOT EXISTS drugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ndc TEXT,
        brand_name TEXT,
        generic_name TEXT,
        manufacturer TEXT,
        product_type TEXT,
        route TEXT,
        substance_name TEXT,
        dosage_form TEXT,
        strength TEXT,
        openfda_json TEXT
    );
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drug_id INTEGER,
        stock_count INTEGER,
        location TEXT,
        expiry_date DATE,
        batch_number TEXT,
        price_lkr REAL,
        last_restocked DATE,
        FOREIGN KEY(drug_id) REFERENCES drugs(id)
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_date DATE,
        status TEXT,
        total_price_lkr REAL,
        shipping_address TEXT,
        payment_method TEXT,
        notes TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        inventory_id INTEGER,
        quantity INTEGER,
        unit_price_lkr REAL,
        subtotal_lkr REAL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(inventory_id) REFERENCES inventory(id)
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inventory_id INTEGER,
        type TEXT,
        quantity INTEGER,
        transaction_date DATE,
        user_id INTEGER,
        notes TEXT,
        FOREIGN KEY(inventory_id) REFERENCES inventory(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        drug_id INTEGER,
        rating INTEGER,
        comment TEXT,
        created_at DATE,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(drug_id) REFERENCES drugs(id)
    );
    CREATE TABLE IF NOT EXISTS deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        delivery_status TEXT,
        courier_name TEXT,
        tracking_number TEXT,
        shipped_at DATE,
        delivered_at DATE,
        estimated_delivery DATE,
        delivery_address TEXT,
        delivery_notes TEXT,
        last_update DATE,
        FOREIGN KEY(order_id) REFERENCES orders(id)
    );
    ''')
    conn.commit()

# --- Data Generation ---
def parse_openfda_drugs(json_path, max_drugs=10000000):
    # Try to load as JSON, else fallback to extracting objects manually
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        results = data.get('results', [])
    except Exception as e:
        # Fallback: extract objects from partial/truncated file
        print(f"[WARN] JSON load failed: {e}\nTrying to extract objects from partial file...")
        results = []
        obj_lines = []
        in_results = False
        obj_count = 0
        with open(json_path, 'r') as f:
            for line in f:
                if '"results"' in line:
                    in_results = True
                    continue
                if in_results:
                    if line.strip().startswith('{'):
                        obj_lines = [line]
                    elif obj_lines:
                        obj_lines.append(line)
                        if line.strip().startswith('},') or line.strip().startswith('}'):  # end of object
                            # Remove trailing comma if present
                            obj_str = ''.join(obj_lines).rstrip(',\n')
                            try:
                                obj = json.loads(obj_str)
                                results.append(obj)
                                obj_count += 1
                                if obj_count >= max_drugs:
                                    break
                            except Exception:
                                continue
        print(f"[INFO] Extracted {len(results)} objects from partial file.")
    drugs = []
    for entry in results[:max_drugs]:
        openfda = entry.get('openfda', {})
        brand_name = (openfda.get('brand_name') or [''])[0]
        generic_name = (openfda.get('generic_name') or [''])[0]
        if not brand_name.strip() and not generic_name.strip():
            continue  # skip drugs with both brand and generic name empty
        drugs.append({
            'ndc': (openfda.get('product_ndc') or [''])[0],
            'brand_name': brand_name,
            'generic_name': generic_name,
            'manufacturer': (openfda.get('manufacturer_name') or [''])[0],
            'product_type': (openfda.get('product_type') or [''])[0],
            'route': (openfda.get('route') or [''])[0],
            'substance_name': (openfda.get('substance_name') or [''])[0],
            'dosage_form': entry.get('dosage_forms_and_strengths', [''])[0],
            'strength': '',
            'openfda_json': json.dumps(openfda)
        })
    return drugs

def generate_users(conn, num_users):
    c = conn.cursor()
    users = []
    for i in range(num_users):
        username = f'user{i+1}'
        user = (
            username,
            random_string(32),
            f"User {i+1}",
            f"user{i+1}@example.com",
            random_phone(),
            random_address(),
            random.choice(['customer', 'pharmacist', 'admin']),
            datetime.date.today().isoformat()
        )
        c.execute('''INSERT INTO users (username, password_hash, full_name, email, phone, address, role, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', user)
        users.append(c.lastrowid)
    conn.commit()
    return users

def generate_inventory(conn, drugs):
    c = conn.cursor()
    drug_ids = []
    for drug in drugs:
        c.execute('''INSERT INTO drugs (ndc, brand_name, generic_name, manufacturer, product_type, route, substance_name, dosage_form, strength, openfda_json)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (drug['ndc'], drug['brand_name'], drug['generic_name'], drug['manufacturer'], drug['product_type'], drug['route'], drug['substance_name'], drug['dosage_form'], drug['strength'], drug['openfda_json']))
        drug_id = c.lastrowid
        drug_ids.append(drug_id)
        # 1-3 inventory records per drug
        for _ in range(random.randint(1, 3)):
            stock = random.randint(0, 200)
            location = random.choice(['A1', 'A2', 'B1', 'B2', 'C1', 'C2'])
            expiry = (datetime.date.today() + datetime.timedelta(days=random.randint(180, 1080))).isoformat()
            batch = random_string(10)
            price = round(random.uniform(*LKR_PRICE_RANGE), 2)
            last_restocked = (datetime.date.today() - datetime.timedelta(days=random.randint(0, 90))).isoformat()
            c.execute('''INSERT INTO inventory (drug_id, stock_count, location, expiry_date, batch_number, price_lkr, last_restocked)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (drug_id, stock, location, expiry, batch, price, last_restocked))
    conn.commit()
    return drug_ids

def generate_orders(conn, user_ids, inventory_ids, num_orders):
    c = conn.cursor()
    for i in range(num_orders):
        user_id = random.choice(user_ids)
        order_date = (datetime.date.today() - datetime.timedelta(days=random.randint(0, 30))).isoformat()
        status = random.choice(['pending', 'paid', 'shipped', 'delivered', 'cancelled'])
        shipping_address = random_address()
        payment_method = random.choice(['cash', 'card', 'mobile'])
        notes = ''
        c.execute('''INSERT INTO orders (user_id, order_date, status, total_price_lkr, shipping_address, payment_method, notes)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, order_date, status, 0, shipping_address, payment_method, notes))
        order_id = c.lastrowid
        # 1-N items per order
        total = 0
        for _ in range(random.randint(1, MAX_ORDER_ITEMS)):
            inv_id = random.randint(1, len(inventory_ids))
            quantity = random.randint(1, 5)
            c.execute('SELECT price_lkr FROM inventory WHERE id=?', (inv_id,))
            price = c.fetchone()[0]
            subtotal = round(price * quantity, 2)
            c.execute('''INSERT INTO order_items (order_id, inventory_id, quantity, unit_price_lkr, subtotal_lkr)
                         VALUES (?, ?, ?, ?, ?)''',
                      (order_id, inv_id, quantity, price, subtotal))
            total += subtotal
        c.execute('UPDATE orders SET total_price_lkr=? WHERE id=?', (total, order_id))
        # Delivery
        if status in ['shipped', 'delivered']:
            delivery_status = 'in_transit' if status == 'shipped' else 'delivered'
            courier = random.choice(['Domex', 'DHL', 'Aramex', 'PickMe'])
            tracking = random_string(12)
            shipped_at = (datetime.date.today() - datetime.timedelta(days=random.randint(1, 5))).isoformat()
            delivered_at = (datetime.date.today() if delivery_status == 'delivered' else None)
            estimated_delivery = (datetime.date.today() + datetime.timedelta(days=random.randint(1, 5))).isoformat()
            delivery_address = shipping_address
            delivery_notes = ''
            last_update = datetime.date.today().isoformat()
            c.execute('''INSERT INTO deliveries (order_id, delivery_status, courier_name, tracking_number, shipped_at, delivered_at, estimated_delivery, delivery_address, delivery_notes, last_update)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (order_id, delivery_status, courier, tracking, shipped_at, delivered_at, estimated_delivery, delivery_address, delivery_notes, last_update))
    conn.commit()

def main():
    # Remove old db
    if Path(DB_PATH).exists():
        Path(DB_PATH).unlink()
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    # Parse drugs
    drugs = parse_openfda_drugs(OPENFDA_JSON, max_drugs=10000000)
    # Users
    user_ids = generate_users(conn, NUM_USERS)
    # Inventory
    drug_ids = generate_inventory(conn, drugs)
    # Inventory ids for order_items
    c = conn.cursor()
    c.execute('SELECT id FROM inventory')
    inventory_ids = [row[0] for row in c.fetchall()]
    # Orders, order_items, deliveries
    generate_orders(conn, user_ids, inventory_ids, NUM_ORDERS)
    print(f"Database generated: {DB_PATH}")

if __name__ == '__main__':
    main()
