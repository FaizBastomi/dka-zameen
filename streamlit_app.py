import streamlit as st
import numpy as np

# 1. FUNGSI KEANGGOTAAN (FROM SCRATCH)
def trapmf(x, abcd):
    a, b, c, d = abcd
    y = np.zeros_like(x)
    for i in range(len(x)):
        if x[i] <= a or x[i] >= d: y[i] = 0.0
        elif a < x[i] < b: y[i] = (x[i] - a) / (b - a) if b != a else 1.0
        elif b <= x[i] <= c: y[i] = 1.0
        elif c < x[i] < d: y[i] = (d - x[i]) / (d - c) if d != c else 1.0
    return y

def trimf(x, abc):
    a, b, c = abc
    return trapmf(x, [a, b, b, c])

def fuzzify_area(x): 
    return {'Kecil': trapmf([x], [0, 0, 8, 15])[0], 'Sedang': trimf([x], [10, 20, 30])[0], 'Luas': trapmf([x], [20, 40, 160, 160])[0]}
def fuzzify_bed(x): 
    return {'Sedikit': trapmf([x], [0, 0, 2, 5])[0], 'Sedang': trimf([x], [3, 5, 8])[0], 'Banyak': trapmf([x], [6, 9, 28, 28])[0]}
def fuzzify_bath(x): 
    return {'Sedikit': trapmf([x], [0, 0, 2, 4])[0], 'Sedang': trimf([x], [3, 5, 7])[0], 'Banyak': trapmf([x], [6, 8, 14, 14])[0]}
def fuzzify_prop(x): 
    return {'Sederhana': trapmf([x], [0, 0, 3, 5])[0], 'Menengah': trimf([x], [4, 6, 8])[0], 'Mewah': trapmf([x], [7, 9, 10, 10])[0]}
def fuzzify_loc(x): 
    return {'Biasa': trapmf([x], [0, 0, 40, 50])[0], 'Strategis': trimf([x], [40, 65, 85])[0], 'Sangat Strategis': trapmf([x], [80, 90, 100, 100])[0]}

# 2. RULE BASE INFERENSI (20 RULES)
def eval_rules(f_area, f_bed, f_bath, f_prop, f_loc):
    rules = []
    
    # Jika lokasinya sangat elit dan properti mewah, pasti Sangat Mahal (apapun ukuran tanahnya)
    rules.append( (min(f_loc['Sangat Strategis'], f_prop['Mewah']), 'Sangat Mahal') )
    # Jika lokasinya biasa dan properti sederhana, pasti Sangat Murah / Murah
    rules.append( (min(f_loc['Biasa'], f_prop['Sederhana']), 'Sangat Murah') )
    rules.append( (min(f_loc['Biasa'], f_prop['Menengah']), 'Murah') )
    
    # --- KELOMPOK 1: Area Kecil ---
    rules.append( (min(f_area['Kecil'], f_bed['Sedikit'], f_loc['Biasa']), 'Sangat Murah') )
    rules.append( (min(f_area['Kecil'], f_bed['Sedikit'], f_loc['Strategis']), 'Murah') )
    rules.append( (min(f_area['Kecil'], f_bed['Sedang']), 'Murah') )
    rules.append( (min(f_area['Kecil'], f_prop['Menengah'], f_loc['Sangat Strategis']), 'Sedang') )
    rules.append( (min(f_area['Kecil'], f_bed['Banyak']), 'Sedang') )

    # --- KELOMPOK 2: Area Sedang ---
    rules.append( (min(f_area['Sedang'], f_bed['Sedikit'], f_prop['Sederhana']), 'Murah') )
    rules.append( (min(f_area['Sedang'], f_bed['Sedang'], f_loc['Biasa']), 'Murah') )
    rules.append( (min(f_area['Sedang'], f_bed['Sedang'], f_prop['Menengah']), 'Sedang') )
    rules.append( (min(f_area['Sedang'], f_prop['Menengah'], f_loc['Strategis']), 'Sedang') )
    rules.append( (min(f_area['Sedang'], f_bed['Banyak'], f_loc['Strategis']), 'Mahal') )
    rules.append( (min(f_area['Sedang'], f_bath['Banyak'], f_loc['Sangat Strategis']), 'Mahal') )

    # --- KELOMPOK 3: Area Luas ---
    rules.append( (min(f_area['Luas'], f_bed['Sedikit'], f_loc['Biasa']), 'Sedang') )
    rules.append( (min(f_area['Luas'], f_bed['Sedikit'], f_loc['Strategis']), 'Sedang') )
    rules.append( (min(f_area['Luas'], f_bed['Sedang'], f_prop['Menengah']), 'Mahal') )
    rules.append( (min(f_area['Luas'], f_prop['Mewah'], f_loc['Strategis']), 'Mahal') )
    rules.append( (min(f_area['Luas'], f_bed['Banyak'], f_prop['Mewah']), 'Sangat Mahal') )
    rules.append( (min(f_area['Luas'], f_bath['Banyak'], f_loc['Sangat Strategis']), 'Sangat Mahal') )

    # Agregasi (Max)
    agg = {'Sangat Murah': 0.0, 'Murah': 0.0, 'Sedang': 0.0, 'Mahal': 0.0, 'Sangat Mahal': 0.0}
    for w, out in rules:
        agg[out] = max(agg[out], w)
        
    return agg

# 3. DEFUZZIFIKASI MAMDANI & SUGENO
z_points = np.linspace(0, 2.25e6, 2251)

def mf_price(x, category):
    val = [x]
    if category == 'Sangat Murah': return trapmf(val, [0, 0, 3e5, 6e5])[0]
    elif category == 'Murah': return trimf(val, [4e5, 8e5, 1.2e6])[0]
    elif category == 'Sedang': return trimf(val, [1e6, 1.4e6, 1.8e6])[0]
    elif category == 'Mahal': return trimf(val, [1.5e6, 1.8e6, 2.1e6])[0]
    elif category == 'Sangat Mahal': return trapmf(val, [1.9e6, 2.25e6, 2.25e6, 2.25e6])[0]

def defuzz_mamdani_manual(agg):
    num = 0.0
    den = 0.0
    for z in z_points:
        mu = max(
            min(agg['Sangat Murah'], mf_price(z, 'Sangat Murah')),
            min(agg['Murah'], mf_price(z, 'Murah')),
            min(agg['Sedang'], mf_price(z, 'Sedang')),
            min(agg['Mahal'], mf_price(z, 'Mahal')),
            min(agg['Sangat Mahal'], mf_price(z, 'Sangat Mahal'))
        )
        num += z * mu
        den += mu
    return num / den if den != 0 else 0.0

sugeno_const = {'Sangat Murah': 3e5, 'Murah': 8e5, 'Sedang': 1.4e6, 'Mahal': 1.8e6, 'Sangat Mahal': 2.15e6}

def defuzz_sugeno(agg):
    num = sum(w * sugeno_const[cat] for cat, w in agg.items())
    den = sum(agg.values())
    return num / den if den != 0 else 0.0

def get_crisp_category(price):
    cats = {
        'Sangat Murah': mf_price(price, 'Sangat Murah'),
        'Murah': mf_price(price, 'Murah'),
        'Sedang': mf_price(price, 'Sedang'),
        'Mahal': mf_price(price, 'Mahal'),
        'Sangat Mahal': mf_price(price, 'Sangat Mahal')
    }
    max_cat = max(cats, key=cats.get)
    if cats[max_cat] == 0:
        if price <= 3e5: return 'Sangat Murah'
        elif price >= 1.9e6: return 'Sangat Mahal'
    return max_cat


# 4. APLIKASI STREAMLIT (UI)
# Konfigurasi Halaman
st.set_page_config(page_title="Estimasi Kategori Properti", layout="wide", page_icon="🏠")

st.title("🏠 Prediksi Kategori Harga Properti (Fuzzy Logic)")
st.markdown("Aplikasi ini membandingkan metode **Fuzzy Mamdani** dan **Sugeno** untuk memprediksi kategori harga properti berdasarkan 5 variabel masukan.")
st.markdown("---")

# Layout Input (Menggunakan Kolom)
col1, col2 = st.columns(2)

with col1:
    st.subheader("Detail Bangunan")
    area_input = st.number_input("Luas Tanah (Dalam Marla)", min_value=1.0, max_value=160.0, value=10.0, step=1.0)
    bed_input = st.number_input("Jumlah Kamar Tidur", min_value=0, max_value=28, value=3, step=1)
    bath_input = st.number_input("Jumlah Kamar Mandi", min_value=0, max_value=14, value=2, step=1)

with col2:
    st.subheader("Lokasi & Tipe Properti")
    
    # Dropdown untuk Tipe Properti
    prop_options = {
        "Sederhana (Room / Portion)": 3,
        "Menengah (Flat / Apartment)": 6,
        "Mewah (House / Villa)": 8,
        "Sangat Mewah (Farm House / Penthouse)": 10
    }
    prop_choice = st.selectbox("Tipe Properti", list(prop_options.keys()))
    prop_score = prop_options[prop_choice]
    
    # Dropdown untuk Lokasi/Kota
    loc_options = {
        "Islamabad (Sangat Strategis / Elite)": 90,
        "Lahore / Karachi (Metropolitan Besar)": 80,
        "Rawalpindi / Faisalabad (Kota Penyangga/Industri)": 60,
        "Kota Lainnya (Biasa)": 40
    }
    loc_choice = st.selectbox("Lokasi / Kota", list(loc_options.keys()))
    loc_score = loc_options[loc_choice]

st.markdown("---")

# Tombol Prediksi
if st.button("🔍 Estimasi Kategori Harga", type="primary", use_container_width=True):
    
    with st.spinner('Menghitung inferensi logika Fuzzy...'):
        # 1. Fuzzifikasi
        f_area = fuzzify_area(area_input)
        f_bed = fuzzify_bed(bed_input)
        f_bath = fuzzify_bath(bath_input)
        f_prop = fuzzify_prop(prop_score)
        f_loc = fuzzify_loc(loc_score)
        
        # 2. Evaluasi 20 Rules
        agg = eval_rules(f_area, f_bed, f_bath, f_prop, f_loc)
        
        # 3. Defuzzifikasi
        m_pred = defuzz_mamdani_manual(agg)
        s_pred = defuzz_sugeno(agg)
        
        # 4. Menentukan Kategori
        m_cat = get_crisp_category(m_pred)
        s_cat = get_crisp_category(s_pred)
    
    # Menampilkan Hasil
    st.subheader("📊 Hasil Evaluasi Fuzzy")
    
    # Tampilkan Box Hasil Mamdani dan Sugeno secara bersampingan
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.info("### Metode MAMDANI")
        st.metric(label="Kategori Harga Terestimasi", value=m_cat)
        st.markdown(f"**Titik Berat (Centroid):** {m_pred:,.2f} PKR")
        
    with res_col2:
        st.success("### Metode SUGENO")
        st.metric(label="Kategori Harga Terestimasi", value=s_cat)
        st.markdown(f"**Nilai Bobot (Weighted Avg):** {s_pred:,.2f} PKR")

    # Opsional: Tampilkan detail derajat keanggotaan/Rule yang aktif (berguna untuk demo)
    with st.expander("Lihat Detail Bobot Himpunan Output (Hasil Agregasi Rule)"):
        st.write("Nilai maksimum (Max) dari setiap kategori output berdasarkan 20 Rules:")
        st.json(agg)