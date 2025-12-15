"""
=================================================================================
SISTEM PENDUKUNG KEPUTUSAN TAT BNN - V4.0 (AI & ANALYTICS EDITION)
=================================================================================
Fitur Baru (v4.0):
1. Optional Comprehensive Module (ACEs, Quality of Life, Social Support)
2. AI-Based Case Complexity Assessment (Heuristic Expert System)
3. Predictive Analytics for Relapse Risk (Probabilistic Model)

Fitur Core :
- Rule-Based Decision (SEMA 4/2010)
- Input Validation
- User Manual

Dasar Hukum: SEMA No. 4 Tahun 2010 & UU 35/2009
=================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# =============================================================================
# 1. KONFIGURASI DATA
# =============================================================================

st.set_page_config(
    page_title="TAT DSS v4.0 - AI & Analytics",
    page_icon="🧠",
    layout="wide"
)

GRAMATUR_LIMITS = {
    "Ganja/Cannabis": 5.0,
    "Metamfetamin/Sabu": 1.0,
    "Heroin": 1.8,
    "Kokain": 1.8,
    "Ekstasi/MDMA": 2.4,
    "Morfin": 1.8,
    "Kodein": 72.0,
    "Lainnya": 0.0
}

ASAM_DIMENSIONS = {
    1: "Intoksikasi Akut/Withdrawal",
    2: "Kondisi Biomedis",
    3: "Emosional/Perilaku/Kognitif",
    4: "Kesiapan Berubah",
    5: "Potensi Relapse",
    6: "Lingkungan Pemulihan"
}

# =============================================================================
# 2. LOGIC ENGINE (BACKEND)
# =============================================================================

class TATLogicEngine:
    """Mesin Logika Keputusan & AI Analytics"""

    @staticmethod
    def validate_inputs(inputs: Dict[str, Any]) -> List[str]:
        errors = []
        if not inputs.get('nama') or len(inputs['nama'].strip()) < 3:
            errors.append("Nama Klien wajib diisi (min. 3 karakter).")
        if inputs.get('usia', 0) < 10 or inputs.get('usia', 0) > 90:
            errors.append("Usia tidak valid (Range: 10-90 tahun).")
        if inputs.get('bb_amount', 0.0) <= 0:
            errors.append("Barang bukti harus lebih besar dari 0 gram.")
        return errors

    @staticmethod
    def calculate_asam_profile(scores: Dict[int, int]) -> Tuple[str, List[str]]:
        high_severity_dims = [k for k, v in scores.items() if v >= 3]
        avg_score = sum(scores.values()) / 6
        
        if 1 in high_severity_dims or 2 in high_severity_dims or 3 in high_severity_dims:
            if any(scores[d] >= 4 for d in [1, 2, 3]):
                return "Level 4 (Medically Managed)", high_severity_dims
            return "Level 3 (Inpatient/Residential)", high_severity_dims
        
        if avg_score < 1.5 and max(scores.values()) <= 2:
            return "Level 1 (Outpatient)", high_severity_dims
        return "Level 2 (Intensive Outpatient)", high_severity_dims

    @staticmethod
    def check_legal_red_flags(bb: float, limit: float, peran: str, residivis: bool) -> List[str]:
        flags = []
        if limit > 0 and bb > limit:
            flags.append(f"Barang bukti ({bb}g) melebihi batas SEMA ({limit}g)")
        if bb > limit * 15 and limit > 0:
            flags.append("Barang bukti sangat besar (>15x SEMA) - Indikasi Sindikat")
        if peran in ["Bandar", "Pengedar", "Kurir"]:
            flags.append(f"Peran tersangka sebagai {peran}")
        if residivis:
            flags.append("Status Residivis kasus narkotika")
        return flags

    # --- AI MODULE: CASE COMPLEXITY ---
    @staticmethod
    def calculate_case_complexity(
        legal_flags: List[str], 
        asam_scores: Dict[int, int], 
        comprehensive_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AI Heuristic untuk menentukan kompleksitas kasus.
        Digunakan untuk menentukan apakah perlu Case Conference tingkat tinggi.
        """
        score = 0
        factors = []
        
        # Faktor Hukum (Bobot Tinggi)
        if legal_flags: 
            score += 30
            factors.append("Konflik Hukum (Red Flags)")
            
        # Faktor Medis (Dual Diagnosis)
        if asam_scores.get(2, 0) >= 3 or asam_scores.get(3, 0) >= 3:
            score += 25
            factors.append("Komorbiditas Medis/Psikiatris")
            
        # Faktor Sosial (Comprehensive)
        aces = comprehensive_data.get('aces_score', 0)
        support = comprehensive_data.get('social_support', 'Baik')
        
        if aces >= 4:
            score += 15
            factors.append(f"Trauma Masa Kecil Tinggi (ACEs: {aces})")
        
        if support == 'Buruk/Tidak Ada':
            score += 20
            factors.append("Tidak Ada Dukungan Sosial")
            
        # Klasifikasi
        if score >= 60:
            return {"level": "EXTREME", "color": "black", "action": "WAJIB Case Conference Gabungan (Jaksa/Hakim/Dokter)", "factors": factors}
        elif score >= 40:
            return {"level": "HIGH", "color": "red", "action": "Sangat Disarankan Case Conference", "factors": factors}
        elif score >= 20:
            return {"level": "MODERATE", "color": "orange", "action": "Review Tim TAT Standard", "factors": factors}
        else:
            return {"level": "LOW", "color": "green", "action": "Prosedur Standard", "factors": factors}

    # --- ANALYTICS MODULE: RELAPSE PREDICTION ---
    @staticmethod
    def predict_relapse_risk(
        dsm_count: int, 
        asam_scores: Dict[int, int], 
        comprehensive_data: Dict[str, Any],
        usia: int
    ) -> Dict[str, Any]:
        """
        Model probabilitas untuk memprediksi risiko kekambuhan (Relapse).
        Based on Matrix Model & ASAM Risk Factors.
        """
        base_risk = 20 # Baseline risk
        risk_factors = []
        
        # 1. Severity of Use
        if dsm_count >= 6: 
            base_risk += 20
            risk_factors.append("Adiksi Berat (DSM-5)")
            
        # 2. Craving & Relapse Potential (ASAM Dim 5)
        asam_5 = asam_scores.get(5, 0)
        if asam_5 >= 3:
            base_risk += 25
            risk_factors.append("Potensi Relapse Tinggi (ASAM D5)")
            
        # 3. Early Onset / Age Factor
        if usia < 20:
            base_risk += 10
            risk_factors.append("Usia Muda (<20 thn)")
            
        # 4. Route of Administration (IV Use)
        if comprehensive_data.get('route') == 'Suntik/IV':
            base_risk += 15
            risk_factors.append("Penggunaan Jarum Suntik")
            
        # 5. Protective Factors (Subtractor)
        if comprehensive_data.get('social_support') == 'Baik':
            base_risk -= 10
            risk_factors.append("(Protektif) Dukungan Sosial Baik")
            
        final_prob = min(max(base_risk, 5), 99)
        
        return {
            "probability": final_prob,
            "factors": risk_factors,
            "category": "High Risk" if final_prob > 60 else "Moderate Risk" if final_prob > 30 else "Low Risk"
        }

    @staticmethod
    def determine_recommendation(inputs: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "rekomendasi": "", "tipe": "", "alasan": [], 
            "status_warna": "grey", "urgency": "Normal",
            "ai_analysis": {}, "prediction": {}
        }

        # Unpack
        asam_scores = inputs['asam_scores']
        dsm5_count = inputs['dsm_count']
        suicide_risk = inputs['suicide_risk']
        assist_risk = inputs['assist_risk']
        bb_amount = inputs['bb_amount']
        bb_limit = inputs['bb_limit']
        peran = inputs['peran']
        is_residivis = inputs['is_residivis']
        comprehensive = inputs.get('comprehensive', {})

        # 1. EMERGENCY
        if suicide_risk >= 4 or asam_scores.get(1, 0) == 4 or asam_scores.get(2, 0) == 4:
            result.update({
                "rekomendasi": "REHABILITASI RAWAT INAP (MEDIS/PSIKIATRIS SEGERA)",
                "tipe": "Medis", "status_warna": "red", "urgency": "IMMEDIATE",
                "alasan": ["🚨 INDIKASI GAWAT DARURAT: Risiko bunuh diri tinggi atau Withdrawal berat.", "Wajib intervensi medis sebelum proses hukum lanjut."]
            })
            return result

        # 2. LEGAL FILTER
        legal_flags = TATLogicEngine.check_legal_red_flags(bb_amount, bb_limit, peran, is_residivis)
        
        # 3. RUN AI & ANALYTICS
        complexity = TATLogicEngine.calculate_case_complexity(legal_flags, asam_scores, comprehensive)
        prediction = TATLogicEngine.predict_relapse_risk(dsm5_count, asam_scores, comprehensive, inputs['usia'])
        
        result['ai_analysis'] = complexity
        result['prediction'] = prediction

        # 4. DETERMINE MAIN REC
        if legal_flags:
            is_addict = (dsm5_count >= 4) or (assist_risk == "High")
            if is_addict and bb_amount > bb_limit:
                result.update({
                    "rekomendasi": "PROSES HUKUM (+ REKOMENDASI REHABILITASI)",
                    "tipe": "Dual Track", "status_warna": "orange",
                    "alasan": legal_flags + ["⚠️ Terkonfirmasi pecandu (DSM-5/ASSIST High).", "Disarankan penerapan Pasal 103 (Vonis Rehab di Lapas)."]
                })
            else:
                result.update({
                    "rekomendasi": "PROSES HUKUM (PIDANA PENJARA)",
                    "tipe": "Hukum", "status_warna": "red",
                    "alasan": legal_flags + ["❌ Tidak memenuhi kriteria rehabilitasi SEMA 4/2010."]
                })
        else:
            asam_profile, _ = TATLogicEngine.calculate_asam_profile(asam_scores)
            if dsm5_count >= 6 or assist_risk == "High" or "Inpatient" in asam_profile or prediction['probability'] > 70:
                result.update({
                    "rekomendasi": "REHABILITASI RAWAT INAP",
                    "tipe": "Medis", "status_warna": "blue",
                    "alasan": ["✓ Barang bukti di bawah SEMA & bukan jaringan.", f"✓ Tingkat Adiksi Berat (DSM-5: {dsm5_count}).", f"✓ Risiko Relapse: {prediction['probability']}%."]
                })
            else:
                result.update({
                    "rekomendasi": "REHABILITASI RAWAT JALAN",
                    "tipe": "Medis", "status_warna": "green",
                    "alasan": ["✓ Barang bukti di bawah SEMA & bukan jaringan.", "✓ Tingkat Adiksi Ringan/Sedang.", "✓ Masih memiliki fungsi sosial."]
                })

        return result

# =============================================================================
# 3. UI COMPONENTS (FRONTEND)
# =============================================================================

class TATUI:
    @staticmethod
    def render_css():
        st.markdown("""
        <style>
            .main-header { font-size: 2.5rem; color: #1e3a8a; text-align: center; font-weight: bold; margin-bottom: 1rem; }
            .section-card { background-color: #f8fafc; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 1rem; }
            .result-box { padding: 2rem; border-radius: 15px; text-align: center; color: white; margin: 2rem 0; }
            .status-red { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
            .status-orange { background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); }
            .status-blue { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
            .status-green { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); }
            .status-black { background: linear-gradient(135deg, #1f2937 0%, #000000 100%); }
            .ai-card { background-color: #f0fdf4; border: 1px solid #86efac; padding: 1rem; border-radius: 8px; }
            .pred-card { background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 1rem; border-radius: 8px; }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def input_section_legal():
        st.markdown("### ⚖️ 1. Parameter Hukum")
        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                jenis_narkotika = st.selectbox("Jenis Narkotika", list(GRAMATUR_LIMITS.keys()))
                limit = GRAMATUR_LIMITS[jenis_narkotika]
                bb_amount = st.number_input("Barang Bukti (Gram)", min_value=0.0, step=0.01, format="%.2f", help=f"Batas SEMA: {limit}g")
                if limit > 0 and bb_amount > 0:
                    ratio = bb_amount / limit
                    if ratio > 1: st.error(f"⚠️ Melebihi Batas SEMA ({ratio:.1f}x)")
                    else: st.success("✅ Di bawah Batas SEMA")
            with col2:
                peran = st.selectbox("Peran Tersangka", ["Pengguna", "Kurir", "Pengedar", "Bandar"])
                residivis = st.checkbox("Status Residivis?")
            st.markdown('</div>', unsafe_allow_html=True)
            return jenis_narkotika, limit, bb_amount, peran, residivis

    @staticmethod
    def input_section_medical():
        st.markdown("### 🏥 2. Parameter Klinis")
        
        with st.expander("📝 DSM-5 Checklist", expanded=False):
            dsm_criteria = ["Lebih banyak/lama", "Ingin berhenti gagal", "Waktu habis utk zat", "Craving", "Gagal kewajiban", "Masalah sosial", "Melepas aktivitas", "Situasi bahaya", "Masalah fisik/psiko", "Toleransi", "Withdrawal"]
            dsm_selected = []
            cols = st.columns(2)
            for i, crit in enumerate(dsm_criteria):
                if cols[i % 2].checkbox(f"{i+1}. {crit}", key=f"dsm_{i}"): dsm_selected.append(crit)
            dsm_count = len(dsm_selected)
            st.caption(f"Total: {dsm_count}/11")

        st.markdown("#### ASAM Severity (0-4)")
        asam_scores = {}
        cols_asam = st.columns(3)
        for dim_id, dim_name in ASAM_DIMENSIONS.items():
            idx = (dim_id - 1) % 3
            with cols_asam[idx]:
                val = st.slider(f"D{dim_id}: {dim_name}", 0, 4, 0, key=f"asam_{dim_id}")
                asam_scores[dim_id] = val

        col_r1, col_r2 = st.columns(2)
        with col_r1: assist_risk = st.selectbox("Risiko ASSIST", ["Low", "Moderate", "High"])
        with col_r2: suicide_risk = st.slider("Risiko Bunuh Diri (C-SSRS)", 0, 5, 0)
        return dsm_count, asam_scores, assist_risk, suicide_risk

    @staticmethod
    def input_section_comprehensive():
        """Modul Input Tambahan (Borderline/Advanced)"""
        st.markdown("### 🔍 3. Asesmen Lanjutan (Optional)")
        with st.expander("Buka Modul Komprehensif (Untuk Kasus Kompleks/Borderline)", expanded=False):
            st.info("Input ini akan mempengaruhi analisis AI Complexity & Relapse Prediction.")
            col1, col2 = st.columns(2)
            
            with col1:
                aces_score = st.number_input("Skor ACEs (0-10)", 0, 10, 0, help="Adverse Childhood Experiences")
                route = st.selectbox("Cara Penggunaan Utama", ["Oral/Hisap/Rokok", "Suntik/IV"], help="Penggunaan jarum suntik meningkatkan risiko medis & relapse.")
            
            with col2:
                social_support = st.selectbox("Dukungan Sosial/Keluarga", ["Baik", "Cukup", "Buruk/Tidak Ada"])
                employment = st.selectbox("Status Pekerjaan", ["Bekerja/Sekolah", "Menganggur/Putus Sekolah"])
                
            return {
                "aces_score": aces_score,
                "route": route,
                "social_support": social_support,
                "employment": employment
            }

    @staticmethod
    def render_ai_dashboard(decision: Dict):
        """Visualisasi AI & Analytics"""
        ai = decision.get('ai_analysis', {})
        pred = decision.get('prediction', {})
        
        st.divider()
        st.header("🧠 AI INTELLIGENCE & ANALYTICS")
        
        col_ai, col_pred = st.columns(2)
        
        # 1. AI Complexity Card
        with col_ai:
            st.markdown(f"""
            <div class="ai-card">
                <h3>🤖 Case Complexity Analysis</h3>
                <h2 style="color: {ai['color']};">{ai['level']}</h2>
                <p><b>Action:</b> {ai['action']}</p>
                <hr>
                <p><small><b>Detected Factors:</b></small></p>
                <ul>{"".join([f"<li>{f}</li>" for f in ai['factors']])}</ul>
            </div>
            """, unsafe_allow_html=True)
            
        # 2. Predictive Analytics Card
        with col_pred:
            st.markdown(f"""
            <div class="pred-card">
                <h3>📉 Relapse Predictive Model</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Gauge Chart
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = pred['probability'],
                title = {'text': "Probabilitas Kambuh (Relapse)"},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 30], 'color': "#bbf7d0"},
                        {'range': [30, 70], 'color': "#fef08a"},
                        {'range': [70, 100], 'color': "#fca5a5"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': pred['probability']}
                }
            ))
            fig.update_layout(height=250, margin=dict(t=30, b=10, l=30, r=30), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(f"**Faktor Risiko Utama:** {', '.join(pred['factors']) if pred['factors'] else 'Minimal'}")

    @staticmethod
    def render_results(decision: Dict, inputs: Dict):
        # ... (Result box code same as v5 but added AI dashboard call)
        color_class = f"status-{decision['status_warna']}"
        st.markdown(f"""
        <div class="result-box {color_class}">
            <h2 style="margin:0">REKOMENDASI:</h2>
            <h1 style="margin:0.5rem 0; font-size: 2.5rem;">{decision['rekomendasi']}</h1>
            <p style="opacity: 0.9">Prioritas: {decision.get('urgency', 'Normal')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Render AI Dashboard
        TATUI.render_ai_dashboard(decision)

# =============================================================================
# 4. MAIN CONTROLLER
# =============================================================================

def main():
    TATUI.render_css()
    st.markdown('<div class="main-header">⚖️ TAT DSS v4.0 (AI Edition)</div>', unsafe_allow_html=True)
    
    if 'analyzed' not in st.session_state:
        st.session_state['analyzed'] = False

    tab_input, tab_result, tab_manual = st.tabs(["📝 Input Data", "🧠 Hasil & AI", "📘 Panduan"])

    with tab_input:
        with st.form("tat_form_v6"):
            col1, col2 = st.columns(2)
            with col1: nama = st.text_input("Nama Klien")
            with col2: usia = st.number_input("Usia", 10, 90, 25)
            st.divider()
            
            # Legal & Medical Inputs
            jenis_narkotika, limit, bb_amount, peran, residivis = TATUI.input_section_legal()
            st.divider()
            dsm_count, asam_scores, assist_risk, suicide_risk = TATUI.input_section_medical()
            
            # NEW: Comprehensive Module
            st.divider()
            comprehensive_data = TATUI.input_section_comprehensive()
            
            submitted = st.form_submit_button("🚀 JALANKAN ANALISIS AI", type="primary", use_container_width=True)

            if submitted:
                # Validation & Logic Execution
                raw_inputs = {"nama": nama, "usia": usia, "bb_amount": bb_amount}
                errors = TATLogicEngine.validate_inputs(raw_inputs)
                
                if errors:
                    for e in errors: st.error(e)
                else:
                    logic_inputs = {
                        'asam_scores': asam_scores, 'dsm_count': dsm_count,
                        'suicide_risk': suicide_risk, 'assist_risk': assist_risk,
                        'bb_amount': bb_amount, 'bb_limit': limit,
                        'peran': peran, 'is_residivis': residivis, 'usia': usia,
                        'comprehensive': comprehensive_data # Pass advanced data
                    }
                    decision = TATLogicEngine.determine_recommendation(logic_inputs)
                    
                    st.session_state['analyzed'] = True
                    st.session_state['decision'] = decision
                    st.session_state['inputs'] = logic_inputs
                    st.session_state['inputs']['nama'] = nama
                    st.rerun()

    with tab_result:
        if st.session_state['analyzed']:
            TATUI.render_results(st.session_state['decision'], st.session_state['inputs'])
        else:
            st.info("Silakan lakukan analisis data terlebih dahulu.")

    with tab_manual:
        st.markdown("## 🧠 Panduan Fitur AI & Analytics")
        st.markdown("""
        **1. AI Case Complexity:**
        Sistem menggunakan algoritma heuristik untuk mendeteksi konflik antara indikator hukum dan medis.
        - **Extreme:** Konflik berat (BB besar tapi Medis Parah). Wajib Case Conference.
        - **Low:** Kasus standar (Pengguna murni, BB kecil).
        
        **2. Relapse Prediction:**
        Menggunakan model probabilistik berdasarkan faktor risiko:
        - Usia muda (<20 thn)
        - Penggunaan suntik (IV)
        - Trauma masa kecil (ACEs)
        - Keparahan Adiksi
        """)

if __name__ == "__main__":
    main()
