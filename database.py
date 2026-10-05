import sqlite3

def init_db():
    # 'alatau_travel.db' атты деректер базасы файлы жасалады (егер жоқ болса)
    conn = sqlite3.connect('alatau_travel.db')
    cursor = conn.cursor()

    # 外键 (Foreign Key) қолдауын қосу
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Турлар кестесін құру (Tours)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,              -- Тур атауы (мысалы: Анталья, Турция)
            country TEXT NOT NULL,            -- Ел
            price REAL NOT NULL,              -- Бағасы (тенгемен)
            duration_nights INTEGER NOT NULL, -- Түн саны
            meals_type TEXT NOT NULL,         -- Тамақтану түрі (All Inclusive, BB, FB)
            description TEXT                  -- Сипаттамасы
        )
    ''')

    # 2. Клиенттер кестесін құру (Clients)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,          -- Клиенттің аты-жөні
            phone TEXT NOT NULL,              -- Телефон нөмірі
            passport_number TEXT NOT NULL     -- Төлқұжат нөмірі
        )
    ''')

    # 3. Брондаулар кестесін құру (Bookings)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tour_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,       -- Брондау жасалған күн
            status TEXT NOT NULL DEFAULT 'Күтуде', -- Мәртебесі: 'Күтуде', 'Төленді', 'Болдырманды'
            FOREIGN KEY (tour_id) REFERENCES tours (id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
        )
    ''')

    # Мысал ретінде базаға алғашқы турларды қосу (тек база бос болса қосылады)
    cursor.execute("SELECT COUNT(*) FROM tours")
    if cursor.fetchone()[0] == 0:
        sample_tours = [
            ('Анталья демалысы', 'Түркия', 350000.0, 7, 'All Inclusive', 'Жерорта теңізі жағалауындағы 5 жұлдызды отель'),
            ('Дубай ғажайыптары', 'БАӘ', 480000.0, 5, 'BB (Таңғы ас)', 'Бурдж-Халифа маңындағы заманауи қонақүй'),
            ('Алакөл жазы', 'Қазақстан', 120000.0, 4, 'FB (3 мезгіл тамақ)', 'Емдік су жағасындағы жайлы коттедж')
        ]
        cursor.executemany('''
            INSERT INTO tours (title, country, price, duration_nights, meals_type, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_tours)

        # Мысал ретінде клиент пен алғашқы бронды да қосу
        cursor.execute('''
            INSERT INTO clients (full_name, phone, passport_number)
            VALUES ('Асан ЕРМЕКОВ', '+77071234567', 'N12345678')
        ''')

        cursor.execute('''
            INSERT INTO bookings (tour_id, client_id, booking_date, status)
            VALUES (1, 1, '2026-05-10', 'Төленді')
        ''')

    conn.commit()
    conn.close()
    print("«Alatau Travel» деректер базасы сәтті құрылып, бастапқы турлар енгізілді!")

if __name__ == '__main__':
    init_db()
