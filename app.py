import streamlit as st
import sqlite3
import pandas as pd
import re
import hashlib

# ---------------------------------------------------------
# 1. БЕТТІҢ КОНФИГУРАЦИЯСЫ ЖӘНЕ СТИЛЬДЕР
# ---------------------------------------------------------
st.set_page_config(page_title="Alatau Travel — Туристік агенттік", page_icon="✈️", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    div[data-testid="stVerticalBlock"] > div.stElementContainer div[data-testid="stContainer"] {
        background-color: #161b22 !important;
        color: #ffffff !important;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    div.stButton > button {
        background-color: #1f6beb;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
        font-weight: 600;
        width: 100%;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #388bfd;
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. ДЕРЕКҚОРДЫ ИНИЦИАЛИЗАЦИЯЛАУ (Alatau Travel DB)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect('alatau_travel_system.db')
    cursor = conn.cursor()
    
    # Пайдаланушылар кестесі
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT
        )
    ''')
    
    # Брондаулар кестесі
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            tour_title TEXT NOT NULL,
            country TEXT NOT NULL,
            price REAL NOT NULL,
            duration_nights INTEGER NOT NULL,
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Турлар кестесі
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tours'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE tours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                country TEXT NOT NULL,
                city TEXT NOT NULL,
                price REAL NOT NULL,
                duration_nights INTEGER NOT NULL,
                meals_type TEXT NOT NULL,
                hotel_rating TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        sample_tours = [
            ("Анталья сәулеті & Демалысы", "Түркия", "Анталья", 350000.0, 7, "Ultra All Inclusive", "5★ Rixos Hotel", "Жерорта теңізі жағасындағы 5 жұлдызды сәнді отель, бірінші жағалау сызығы."),
            ("Стамбул тарихи саяхаты", "Түркия", "Стамбул", 280000.0, 5, "BB (Таңғы ас)", "4★ Grand Hotel", "Босфор бұғазы мен көрікті тарихи орындарға жақын жайлы мейманхана."),
            ("Дубай ғажайыптары", "БАӘ", "Дубай", 480000.0, 6, "BB (Таңғы ас)", "5★ Marina Suites", "Бурдж-Халифа мен Дубай Молл маңындағы заманауи люкс отель."),
            ("Абу-Даби демалысы", "БАӘ", "Абу-Даби", 420000.0, 7, "HB (Екі мезгіл)", "5★ Yas Island Resort", "Феррари Парк пен су паркіне тегін кіру мүмкіндігі бар шипажай."),
            ("Шарм-эль-Шейх су асты әлемі", "Египет", "Шарм-эль-Шейх", 310000.0, 8, "All Inclusive", "5★ Coral Beach Resort", "Қызыл теңіздің ең әдемі маржан рифтері мен жеке жағажайы."),
            ("Хургада отбасылық туры", "Египет", "Хургада", 290000.0, 7, "All Inclusive", "4★ Jasmine Beach", "Балаларға арналған аквапарк пен отбасылық ойын-сауық орталығы."),
            ("Пхукет экзотикалық аралы", "Таиланд", "Пхукет", 550000.0, 10, "BB (Таңғы ас)", "4★ Patong Paradise", "Патонг жағажайында орналасқан, экзотикалық табиғаты бар арал."),
            ("Патайя белсенді демалысы", "Таиланд", "Патайя", 460000.0, 9, "BB (Таңғы ас)", "4★ Ocean View Resort", "Кешкі ойын-сауықтар мен экскурсияларға ыңғайлы орталық отель."),
            ("Мальдив жұмақ аралы", "Мальдив аралдары", "Мале", 950000.0, 7, "FB (3 мезгіл)", "5★ Water Villas Resort", "Мұхит үстіндегі жеке вилла, романтикалық демалыс пен мөлдір су."),
            ("Бали рухани демалысы", "Индонезия", "Бали", 680000.0, 10, "BB (Таңғы ас)", "5★ Ubud Jungle Resort", "Убуд джунглиіндегі панорамалық бассейн мен СПА орталығы."),
            ("Алакөл емдік суы", "Қазақстан", "Алакөл", 120000.0, 5, "FB (3 мезгіл)", "3★ Алакөл Резорт", "Қара тасты емдік жағажай мен жайлы коттедждер."),
            ("Бурабай табиғат құшағында", "Қазақстан", "Бурабай", 150000.0, 4, "FB (3 мезгіл)", "4★ Rixos Borovoe", "Көл жағасындағы қарағайлы орман ішіндегі шипажай."),
            ("Тбилиси және Кахетия", "Грузия", "Тбилиси", 270000.0, 6, "BB (Таңғы ас)", "4★ Old Tbilisi Hotel", "Грузин асханасы мен шарап турлары енгізілген тарихи саяхат."),
            ("Батуми қара теңіз жағалауы", "Грузия", "Батуми", 320000.0, 7, "BB (Таңғы ас)", "5★ Batumi Boulevard", "Теңіз жағалауындағы заманауи бульвар мен заманауи қонақүй."),
            ("Фукуок аралы", "Вьетнам", "Фукуок", 520000.0, 9, "BB (Таңғы ас)", "5★ Vinpearl Resort", "Ақ шағыл жағажайлар мен тропикалық парктер аймағы.")
        ]

        cursor.executemany('''
            INSERT INTO tours (title, country, city, price, duration_nights, meals_type, hotel_rating, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_tours)
        conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------------------------------------
# 3. СЕССИЯ КҮЙЛЕРІН БАСҚАРУ
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "full_name" not in st.session_state:
    st.session_state.full_name = ""
if "chat_query" not in st.session_state:
    st.session_state.chat_query = ""

def get_tours():
    conn = sqlite3.connect('alatau_travel_system.db')
    df = pd.read_sql_query("SELECT * FROM tours", conn)
    conn.close()
    return df

df = get_tours()

# ---------------------------------------------------------
# 4. БҮЙІРЛІК ПАНЕЛЬ — Авторизация және ИИ Ассистент
# ---------------------------------------------------------
st.sidebar.markdown("## 👤 Жеке Кабинет")

if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("Мәзір:", ["Кіру", "Тіркелу"])
    
    if auth_mode == "Тіркелу":
        st.sidebar.subheader("Жаңа аккаунт ашу")
        reg_user = st.sidebar.text_input("Логин (Email немесе Nick):", key="reg_u")
        reg_pass = st.sidebar.text_input("Құпия сөз:", type="password", key="reg_p")
        reg_name = st.sidebar.text_input("Аты-жөніңіз:", key="reg_n")
        reg_phone = st.sidebar.text_input("Телефон нөміріңіз:", key="reg_ph")
        
        if st.sidebar.button("Тіркелуді аяқтау"):
            if reg_user and reg_pass and reg_name:
                conn = sqlite3.connect('alatau_travel_system.db')
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users (username, password, full_name, phone) VALUES (?, ?, ?, ?)",
                                   (reg_user, hash_password(reg_pass), reg_name, reg_phone))
                    conn.commit()
                    st.sidebar.success("✅ Сәтті тіркелдіңіз! Енді 'Кіру' арқылы кіріңіз.")
                except sqlite3.IntegrityError:
                    st.sidebar.error("⚠ Бұл логин қазірдің өзінде тіркелген!")
                conn.close()
            else:
                st.sidebar.warning("Барлық міндетті өрістерді толтырыңыз!")
    else:
        st.sidebar.subheader("Аккаунтқа кіру")
        log_user = st.sidebar.text_input("Логин:", key="log_u")
        log_pass = st.sidebar.text_input("Құпия сөз:", type="password", key="log_p")
        
        if st.sidebar.button("Жүйеге кіру"):
            conn = sqlite3.connect('alatau_travel_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT full_name, password FROM users WHERE username = ?", (log_user,))
            user = cursor.fetchone()
            conn.close()
            
            if user and user[1] == hash_password(log_pass):
                st.session_state.logged_in = True
                st.session_state.username = log_user
                st.session_state.full_name = user[0]
                st.sidebar.success(f"Қош келдіңіз, {user[0]}!")
                st.rerun()
            else:
                st.sidebar.error("❌ Логин немесе пароль қате!")
else:
    st.sidebar.success(f"Қош келдіңіз, **{st.session_state.full_name}**!")
    
    st.sidebar.markdown("### 📋 Менің брондауларым:")
    conn = sqlite3.connect('alatau_travel_system.db')
    user_bookings = pd.read_sql_query("SELECT tour_title, country, price, duration_nights, booking_date FROM bookings WHERE username = ?", conn, params=(st.session_state.username,))
    conn.close()
    
    if not user_bookings.empty:
        for idx, row in user_bookings.iterrows():
            st.sidebar.info(f"✈️ **{row['tour_title']}** ({row['country']})\n💰 Бағасы: {row['price']:,.0f} ₸\n🌙 Ұзақтығы: {row['duration_nights']} түн\n📅 Күні: {str(row['booking_date'])[:10]}")
    else:
        st.sidebar.write("Әзірге брондалған турларыңыз жоқ.")
        
    if st.sidebar.button("Шығу (Logout)"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.full_name = ""
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("## 🤖 ИИ Ассистент Чаты")
st.sidebar.write("Қажеттілігіңізді жазыңыз (мысалы: *'Түркия'*, *'Дубай'*, *'арзан'*, *'All Inclusive'*, *'7 түн'*):")

user_input = st.sidebar.text_input("Сұраныс енгізу:", value=st.session_state.chat_query)

if st.sidebar.button("Іздеуді орындау"):
    st.session_state.chat_query = user_input

if st.sidebar.button("Барлық турларды көрсету"):
    st.session_state.chat_query = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Қосымша сүзгілер")
selected_country = st.sidebar.selectbox("Елді таңдаңыз:", ["Барлығы"] + sorted(list(df['country'].unique())))
selected_meals = st.sidebar.selectbox("Тамақтану түрі:", ["Барлығы"] + sorted(list(df['meals_type'].unique())))
max_price = st.sidebar.slider("Максималды баға (₸):", 100000, 1000000, 1000000, step=50000)

# ---------------------------------------------------------
# 5. НЕГІЗГІ БЕТ — Турлар каталогы
# ---------------------------------------------------------
st.title("✈️ Alatau Travel — Туристік агенттігі")
st.write("Әлемнің ең әдемі бұрыштарына саяхаттаңыз! Ыңғайлы іздеу, сенімді брондау және сапалы демалыс.")

filtered = df[df['price'] <= max_price]

if selected_country != "Барлығы":
    filtered = filtered[filtered['country'] == selected_country]

if selected_meals != "Барлығы":
    filtered = filtered[filtered['meals_type'] == selected_meals]

active_query = st.session_state.chat_query.lower()
if active_query:
    # Елдер мен қалаларды іздеу
    countries = ['түркия', 'баә', 'дубай', 'египет', 'таиланд', 'мальдив', 'индонезия', 'бали', 'қазақстан', 'грузия', 'вьетнам']
    for c in countries:
        if c in active_query:
            if c in ['баә', 'дубай']:
                filtered = filtered[filtered['country'] == 'БАӘ']
            elif c in ['индонезия', 'бали']:
                filtered = filtered[filtered['country'] == 'Индонезия']
            elif c == 'мальдив':
                filtered = filtered[filtered['country'] == 'Мальдив аралдары']
            elif c == 'түркия':
                filtered = filtered[filtered['country'] == 'Түркия']
            elif c == 'египет':
                filtered = filtered[filtered['country'] == 'Египет']
            elif c == 'таиланд':
                filtered = filtered[filtered['country'] == 'Таиланд']
            elif c == 'қазақстан':
                filtered = filtered[filtered['country'] == 'Қазақстан']
            elif c == 'грузия':
                filtered = filtered[filtered['country'] == 'Грузия']
            elif c == 'вьетнам':
                filtered = filtered[filtered['country'] == 'Вьетнам']

    # Баға бойынша
    if 'арзан' in active_query or 'бюджет' in active_query or 'тиімді' in active_query:
        filtered = filtered[filtered['price'] <= 300000]
    elif 'қымбат' in active_query or 'люкс' in active_query or 'премиум' in active_query or 'жұмақ' in active_query:
        filtered = filtered[filtered['price'] >= 500000]

    # Тамақтану бойынша
    if 'all inclusive' in active_query or 'бәрі енгізілген' in active_query:
        filtered = filtered[filtered['meals_type'].str.lower().str.contains('all inclusive')]
    elif 'таңғы ас' in active_query or 'bb' in active_query:
        filtered = filtered[filtered['meals_type'].str.lower().str.contains('bb')]

    # Түн саны
    nights_match = re.search(r'(\d+)\s*(түн|күн)', active_query)
    if nights_match:
        n_val = int(nights_match.group(1))
        filtered = filtered[filtered['duration_nights'] == n_val]

    st.info(f"🤖 ИИ Ассистент талдады: «{st.session_state.chat_query}» бойынша турлар сүзілді.")

st.write(f"### 🎯 Табылған турлар саны: {len(filtered)}")

# ---------------------------------------------------------
# 6. ТУРЛАРДЫ КАРТОЧКАЛАР ТҮРІНДЕ ШЫҒАРУ ЖӘНЕ БРОНДАУ
# ---------------------------------------------------------
if not filtered.empty:
    cols = st.columns(2)
    for index, row in filtered.reset_index().iterrows():
        col = cols[index % 2]
        with col:
            with st.container(border=True):
                st.markdown(f"### 🏝️ {row['title']}")
                st.markdown(f"📍 **Орналасуы:** {row['country']}, {row['city']} ({row['hotel_rating']})")
                st.markdown(f"📝 **Сипаттамасы:** {row['description']}")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Бағасы", f"{row['price']:,.0f} ₸")
                m2.metric("Ұзақтығы", f"{row['duration_nights']} түн")
                m3.metric("Тамақтану", row['meals_type'])
                
                if st.button(f"Турды брондау ({row['title']})", key=f"book_{row['id']}"):
                    if st.session_state.logged_in:
                        conn = sqlite3.connect('alatau_travel_system.db')
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO bookings (username, tour_title, country, price, duration_nights) VALUES (?, ?, ?, ?, ?)",
                                       (st.session_state.username, row['title'], row['country'], row['price'], row['duration_nights']))
                        conn.commit()
                        conn.close()
                        st.success(f"🎉 Құттықтаймыз, {st.session_state.full_name}! Сіз **{row['title']}** турын сәтті брондадыңыз. Мәліметтер жеке кабинетіңізге сақталды.")
                    else:
                        st.warning("⚠️ Брондау үшін алдымен бүйірлік панельден **Тіркеліп** немесе **Жүйеге кіріңіз**!")
else:
    st.warning("Өкінішке қарай, бұл талаптарға сай ешқандай тур табылмады. Іздеу шарттарын өзгертіп көріңіз.")
