import streamlit as st
import numpy as np

# ==========================================
# 1. FUNGSI KEANGGOTAAN TERPADU (SCALAR & ARRAY)
# ==========================================
def trapmf(x, abcd):
    a, b, c, d = abcd
    if isinstance(x, (list, np.ndarray)):
        y = np.zeros(len(x))
        for i in range(len(x)):
            if x[i] <= a or x[i] >= d: y[i] = 0.0
            elif a < x[i] < b: y[i] = (x[i] - a) / (b - a) if b != a else 1.0
            elif b <= x[i] <= c: y[i] = 1.0
            elif c < x[i] < d: y[i] = (d - x[i]) / (d - c) if d != c else 1.0
        return y
    else:
        if x <= a or x >= d: return 0.0
        elif a < x < b: return (x - a) / (b - a) if b != a else 1.0
        elif b <= x <= c: return 1.0
        elif c < x < d: return (d - x) / (d - c) if d != c else 1.0
        return 0.0

def trimf(x, abc):
    return trapmf(x, [abc[0], abc[1], abc[1], abc[2]])

# ==========================================
# 2. FUZZIFIKASI 5 INPUT
# ==========================================
def fuzzify_area(x): return {'Kecil': trapmf(x, [0, 0, 8, 15]), 'Sedang': trimf(x, [10, 20, 30]), 'Luas': trapmf(x, [20, 40, 160, 160])}
def fuzzify_bed(x): return {'Sedikit': trapmf(x, [0, 0, 2, 5]), 'Sedang': trimf(x, [3, 5, 8]), 'Banyak': trapmf(x, [6, 9, 28, 28])}
def fuzzify_bath(x): return {'Sedikit': trapmf(x, [0, 0, 2, 4]), 'Sedang': trimf(x, [3, 5, 7]), 'Banyak': trapmf(x, [6, 8, 14, 14])}
def fuzzify_prop(x): return {'Sederhana': trapmf(x, [0, 0, 3, 5]), 'Menengah': trimf(x, [4, 6, 8]), 'Mewah': trapmf(x, [7, 9, 10, 10])}
def fuzzify_loc(x): return {'Biasa': trapmf(x, [0, 0, 40, 50]), 'Strategis': trimf(x, [40, 65, 85]), 'Sangat Strategis': trapmf(x, [80, 90, 100, 100])}

# ==========================================
# 3. RULE BASE INFERENSI (20 RULES UMUM)
# ==========================================
def eval_rules(f_area, f_bed, f_bath, f_prop, f_loc):
    rules = []
    
    # JARING PENGAMAN: Evaluasi Berdasarkan Lokasi & Properti Saja
    rules.append( (min(f_loc['Sangat Strategis'], f_prop['Mewah']), 'Sangat Mahal') )
    rules.append( (min(f_loc['Biasa'], f_prop['Sederhana']), 'Sangat Murah') )
    rules.append( (min(f_loc['Biasa'], f_prop['Menengah']), 'Murah') )
    
    # KELOMPOK 1: Area Kecil
    rules.append( (min(f_area['Kecil'], f_bed['Sedikit'], f_loc['Biasa']), 'Sangat Murah') )
    rules.append( (min(f_area['Kecil'], f_bed['Sedikit'], f_loc['Strategis']), 'Murah') )
    rules.append( (min(f_area['Kecil'], f_bed['Sedang']), 'Murah') )
    rules.append( (min(f_area['Kecil'], f_prop['Menengah'], f_loc['Sangat Strategis']), 'Sedang') )
    rules.append( (min(f_area['Kecil'], f_bed['Banyak']), 'Sedang') )

    # KELOMPOK 2: Area Sedang
    rules.append( (min(f_area['Sedang'], f_bed['Sedikit'], f_prop['Sederhana']), 'Murah') )
    rules.append( (min(f_area['Sedang'], f_bed['Sedang'], f_loc['Biasa']), 'Murah') )
    rules.append( (min(f_area['Sedang'], f_bed['Sedang'], f_prop['Menengah']), 'Sedang') )
    rules.append( (min(f_area['Sedang'], f_prop['Menengah'], f_loc['Strategis']), 'Sedang') )
    rules.append( (min(f_area['Sedang'], f_bed['Banyak'], f_loc['Strategis']), 'Mahal') )
    rules.append( (min(f_area['Sedang'], f_bath['Banyak'], f_loc['Sangat Strategis']), 'Mahal') )

    # KELOMPOK 3: Area Luas
    rules.append( (min(f_area['Luas'], f_bed['Sedikit'], f_loc['Biasa']), 'Sedang') )
    rules.append( (min(f_area['Luas'], f_bed['Sedikit'], f_loc['Strategis']), 'Sedang') )
    rules.append( (min(f_area['Luas'], f_bed['Sedang'], f_prop['Menengah']), 'Mahal') )
    rules.append( (min(f_area['Luas'], f_prop['Mewah'], f_loc['Strategis']), 'Mahal') )
    rules.append( (min(f_area['Luas'], f_bed['Banyak'], f_prop['Mewah']), 'Sangat Mahal') )
    rules.append( (min(f_area['Luas'], f_bath['Banyak'], f_loc['Sangat Strategis']), 'Sangat Mahal') )

    agg = {'Sangat Murah': 0.0, 'Murah': 0.0, 'Sedang': 0.0, 'Mahal': 0.0, 'Sangat Mahal': 0.0}
    for w, out in rules:
        agg[out] = max(agg[out], w)
    return agg

# ==========================================
# 4. DEFUZZIFIKASI MAMDANI & SUGENO
# ==========================================
z_points_list = list(np.linspace(0, 2.25e6, 2251))

def defuzz_mamdani_manual(agg):
    num = 0.0
    den = 0.0
    for z in z_points_list:
        mu_z = max(
            min(agg['Sangat Murah'], trapmf(z, [0, 0, 3e5, 6e5])),
            min(agg['Murah'], trimf(z, [4e5, 8e5, 1.2e6])),
            min(agg['Sedang'], trimf(z, [1e6, 1.4e6, 1.8e6])),
            min(agg['Mahal'], trimf(z, [1.5e6, 1.8e6, 2.1e6])),
            min(agg['Sangat Mahal'], trapmf(z, [1.9e6, 2.25e6, 2.25e6, 2.25e6]))
        )
        num += z * mu_z
        den += mu_z
    return num / den if den != 0 else 0.0

sugeno_const = {'Sangat Murah': 3e5, 'Murah': 8e5, 'Sedang': 1.4e6, 'Mahal': 1.8e6, 'Sangat Mahal': 2.15e6}

def defuzz_sugeno(agg):
    num = sum(w * sugeno_const[cat] for cat, w in agg.items())
    den = sum(agg.values())
    return num / den if den != 0 else 0.0

def get_crisp_category(price):
    cats = {
        'Sangat Murah': trapmf(price, [0, 0, 3e5, 6e5]),
        'Murah': trimf(price, [4e5, 8e5, 1.2e6]),
        'Sedang': trimf(price, [1e6, 1.4e6, 1.8e6]),
        'Mahal': trimf(price, [1.5e6, 1.8e6, 2.1e6]),
        'Sangat Mahal': trapmf(price, [1.9e6, 2.25e6, 2.25e6, 2.25e6])
    }
    max_cat = max(cats, key=cats.get)
    if cats[max_cat] == 0:
        if price <= 3e5: return 'Sangat Murah'
        elif price >= 1.9e6: return 'Sangat Mahal'
    return max_cat

# ==========================================
# 5. APLIKASI STREAMLIT (UI)
# ==========================================
st.set_page_config(page_title="Estimasi Harga Properti", layout="wide", page_icon="🏠")

st.title("🏠 Estimasi Harga Properti (Mamdani vs Sugeno)")
st.markdown("Aplikasi Fuzzy Logic dari awal (*from scratch*) untuk mengestimasi harga properti berdasarkan 5 variabel input.")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Detail Fisik Bangunan")
    area_input = st.number_input("Luas Tanah (Dalam Marla)", min_value=1.0, max_value=160.0, value=10.0, step=1.0)
    bed_input = st.number_input("Jumlah Kamar Tidur", min_value=0, max_value=28, value=3, step=1)
    bath_input = st.number_input("Jumlah Kamar Mandi", min_value=0, max_value=14, value=2, step=1)

with col2:
    st.subheader("Kualitas & Lokasi")
    
    prop_options = {
        "Sederhana (Room / Portion)": 3,
        "Menengah (Flat / Apartment)": 6,
        "Mewah (House / Villa)": 8,
        "Sangat Mewah (Farm House / Penthouse)": 10
    }
    prop_choice = st.selectbox("Tipe Properti", list(prop_options.keys()))
    prop_score = prop_options[prop_choice]
    
    loc_options = {
        "Sangat Strategis (Islamabad / Elite)": 90,
        "Strategis (Lahore / Karachi)": 80,
        "Biasa (Rawalpindi / Faisalabad)": 60,
        "Sangat Biasa (Kota Lainnya)": 40
    }
    loc_choice = st.selectbox("Lokasi / Kota", list(loc_options.keys()))
    loc_score = loc_options[loc_choice]

st.markdown("---")

if st.button("🔍 Estimasi Harga", type="primary", use_container_width=True):
    
    with st.spinner('Memproses Inferensi Fuzzy...'):
        f_area = fuzzify_area(area_input)
        f_bed = fuzzify_bed(bed_input)
        f_bath = fuzzify_bath(bath_input)
        f_prop = fuzzify_prop(prop_score)
        f_loc = fuzzify_loc(loc_score)
        
        agg = eval_rules(f_area, f_bed, f_bath, f_prop, f_loc)
        
        m_pred = defuzz_mamdani_manual(agg)
        s_pred = defuzz_sugeno(agg)
        
        m_cat = get_crisp_category(m_pred)
        s_cat = get_crisp_category(s_pred)
    
    # 1. Menampilkan Bobot Agregasi
    st.subheader("⚙️ Nilai Bobot Agregasi Rule (Max)")
    st.markdown("Bobot ini menunjukkan seberapa kuat properti tersebut masuk ke masing-masing kategori harga berdasarkan *Rule Base* yang telah dievaluasi.")
    
    # Menampilkan bar chart sederhana bawaan Streamlit agar visualnya menarik
    st.bar_chart(agg)
    
    st.markdown("---")
    st.subheader("📊 Hasil Akhir Estimasi")
    
    # 2. Menampilkan Prediksi Harga & Kategori
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.info("### Metode MAMDANI")
        st.metric(label="Kategori Harga", value=m_cat)
        st.markdown(f"**Estimasi Angka (Centroid):**")
        st.subheader(f"Rs {m_pred:,.2f} PKR")
        
    with res_col2:
        st.success("### Metode SUGENO")
        st.metric(label="Kategori Harga", value=s_cat)
        st.markdown(f"**Estimasi Angka (Weighted Avg):**")
        st.subheader(f"Rs {s_pred:,.2f} PKR")
