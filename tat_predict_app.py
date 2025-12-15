"""
=================================================================================
SISTEM PENDUKUNG KEPUTUSAN TIM ASESMEN TERPADU (TAT) BNN - V4.0 (REGULATED)
=================================================================================
VERSI: 4.0.0 - REGULATORY COMPLIANT EDITION

Perubahan Utama dari v3.0:
1. Menghapus 'Medical Composite Score' (bobot %) yang tidak berdasar hukum.
2. Mengganti logika keputusan dengan Rule-Based Engine sesuai SEMA 4/2010.
3. Refactoring struktur kode menjadi modular (UI terpisah dari Logic).
4. Penambahan validasi "Red Flags" hukum yang lebih ketat.

Dasar Hukum:
- UU No. 35 Tahun 2009 tentang Narkotika
- SEMA No. 4 Tahun 2010 (Batasan Gramatur)
- Peraturan Bersama 7 Instansi 2014
=================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
from typing import Dict, List, Tuple, Any, Optional

# =============================================================================
# 1. KONFIGURASI & KONSTANTA DATA
# =============================================================================

st.set_page_config(
    page_title="TAT DSS v4.0 - Regulatory Compliant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SEMA No. 4 Tahun 2010 Limits (Gram)
GRAMATUR_LIMITS = {
    "Ganja/Cannabis": 5.0,
    "Metamfetamin/Sabu": 1.0,
    "Heroin": 1.8,
    "Kokain": 1.8,
    "Ekstasi/MDMA": 2.4, # Atau 8 butir
    "Morfin": 1.8,
    "Kodein": 72.0,
    "Lainnya": 0.0 # Perlu pertimbangan khusus
}

# Lab Cut-off (ng/mL) - Standard Screening
LAB_CUTOFFS = {
    "Metamfetamin (Sabu)": 1000,
    "Morfin (Heroin)": 300,
    "Kokain": 300,
    "Amfetamin": 1000,
    "Benzodiazepin": 300,
    "THC (Ganja)": 50,
    "MDMA (Ekstasi)": 500
}

# Data Instrumen (Static Data)
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
    """
    Kelas yang menangani semua perhitungan logika bisnis dan aturan hukum.
    Terpisah sepenuhnya dari UI Streamlit.
    """

    @staticmethod
    def calculate_asam_profile(scores: Dict[int, int]) -> Tuple[str, List[str]]:
        """Menentukan profil keparahan berdasarkan dimensi ASAM"""
        high_severity_dims = [k for k, v in scores.items() if v >= 3]
        avg_score = sum(scores.values()) / 6
        
        if 1 in high_severity_dims or 2 in high_severity_dims or 3 in high_severity_dims:
            # Dimensi 1, 2, 3 adalah indikator medis/psikiatris urgent
            if any(scores[d] >= 4 for d in [1, 2, 3]):
                return "Level 4 (Medically Managed)", high_severity_dims
            return "Level 3 (Inpatient/Residential)", high_severity_dims
        
        if avg_score < 1.5 and max(scores.values()) <= 2:
            return "Level 1 (Outpatient)", high_severity_dims
        
        return "Level 2 (Intensive Outpatient)", high_severity_dims

    @staticmethod
    def check_legal_red_flags(bb: float, limit: float, peran: str, residivis: bool) -> List[str]:
        """Mendeteksi indikator merah hukum (Diskualifikasi Rehab)"""
        flags = []
        if limit > 0 and bb > limit:
            flags.append(f"Barang bukti ({bb}g) melebihi batas SEMA ({limit}g)")
        if bb > limit * 15: # Heuristik developer untuk indikasi kuat
            flags.append("Barang bukti sangat besar (>15x SEMA) - Indikasi Sindikat")
        if peran in ["Bandar", "Pengedar", "Kurir"]:
            flags.append(f"Peran tersangka sebagai {peran}")
        if residivis:
            flags.append("Status Residivis kasus narkotika")
        return flags

    @staticmethod
    def determine_recommendation(
        # Medical Inputs
        asam_scores: Dict[int, int],
        dsm5_count: int,
        suicide_risk_level: int, # 0-5 from C-SSRS
        assist_risk: str,
        
        # Legal Inputs
        bb_amount: float,
        bb_limit: float,
        peran: str,
        is_residivis: bool
    ) -> Dict[str, Any]:
        """
        Decision Matrix TAT v4.0 (Rule-Based)
        """
        result = {
            "rekomendasi": "",
            "tipe": "", # Medis / Hukum / Dual
            "alasan": [],
            "status_warna": "grey",
            "urgency": "Normal"
        }

        # 1. CEK KEDARURATAN MEDIS (PRIORITAS TERTINGGI KEMANUSIAAN)
        if suicide_risk_level >= 4 or asam_scores.get(1, 0) == 4 or asam_scores.get(2, 0) == 4:
            result["rekomendasi"] = "REHABILITASI RAWAT INAP (MEDIS/PSIKIATRIS SEGERA)"
            result["tipe"] = "Medis"
            result["status_warna"] = "red"
            result["urgency"] = "IMMEDIATE"
            result["alasan"].append("🚨 INDIKASI GAWAT DARURAT: Risiko bunuh diri tinggi atau Withdrawal berat.")
            result["alasan"].append("Wajib intervensi medis sebelum proses hukum lanjut.")
            return result

        # 2. CEK FILTER HUKUM (SEMA 4/2010)
        legal_flags = TATLogicEngine.check_legal_red_flags(bb_amount, bb_limit, peran, is_residivis)
        
        if legal_flags:
            # Jika ada red flags hukum
            is_addict = (dsm5_count >= 4) or (assist_risk == "High")
            
            if is_addict and bb_amount > bb_limit:
                 # Dual Track (Hukum + Rehab) - Pasal 103
                result["rekomendasi"] = "PROSES HUKUM (+ REKOMENDASI REHABILITASI)"
                result["tipe"] = "Dual Track"
                result["status_warna"] = "orange"
                result["alasan"].extend(legal_flags)
                result["alasan"].append("⚠️ Namun terkonfirmasi pecandu (DSM-5/ASSIST High).")
                result["alasan"].append("Disarankan penerapan Pasal 103 (Vonis Rehab di Lapas/Lembaga).")
            else:
                # Murni Pidana
                result["rekomendasi"] = "PROSES HUKUM (PIDANA PENJARA)"
                result["tipe"] = "Hukum"
                result["status_warna"] = "red"
                result["alasan"].extend(legal_flags)
                result["alasan"].append("❌ Tidak memenuhi kriteria rehabilitasi SEMA 4/2010.")
            
            return result

        # 3. PENENTUAN LEVEL REHABILITASI (JIKA LOLOS FILTER HUKUM)
        asam_profile, high_dims = TATLogicEngine.calculate_asam_profile(asam_scores)
        
        if dsm5_count >= 6 or assist_risk == "High" or "Inpatient" in asam_profile:
            result["rekomendasi"] = "REHABILITASI RAWAT INAP"
            result["tipe"] = "Medis"
            result["status_warna"] = "blue"
            result["alasan"].append("✓ Barang bukti di bawah SEMA & bukan jaringan.")
            result["alasan"].append(f"✓ Tingkat Adiksi Berat (DSM-5: {dsm5_count} kriteria).")
            result["alasan"].append(f"✓ Profil ASAM: {asam_profile}.")
        else:
            result["rekomendasi"] = "REHABILITASI RAWAT JALAN"
            result["tipe"] = "Medis"
            result["status_warna"] = "green"
            result["alasan"].append("✓ Barang bukti di bawah SEMA & bukan jaringan.")
            result["alasan"].append("✓ Tingkat Adiksi Ringan/Sedang.")
            result["alasan"].append("✓ Masih memiliki fungsi sosial/dukungan lingkungan.")

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
            .section-card { background-color: #f8fafc; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .result-box { padding: 2rem; border-radius: 15px; text-align: center; color: white; margin: 2rem 0; }
            .status-red { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
            .status-orange { background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); }
            .status-blue { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
            .status-green { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); }
            .status-grey { background-color: #64748b; }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        st.markdown('<div class="main-header">⚖️ TAT DSS v4.0 (Regulated)</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #64748b;">Sistem Pendukung Keputusan Berbasis Aturan (SEMA 4/2010)</div>', unsafe_allow_html=True)
        st.warning("⚠️ DISCLAIMER: Sistem ini adalah alat bantu hitung & logika. Keputusan final tetap pada Tim Asesmen Terpadu.")

    @staticmethod
    def render_sidebar():
        with st.sidebar:
            st.header("📋 Status Input")
            # Progress bar dummy
            prog = 0
            if st.session_state.get('form_filled', False):
                prog = 100
            st.progress(prog)
            
            st.info("""
            **Panduan Singkat:**
            1. Isi data Identitas
            2. Isi data Hukum (BB, Peran)
            3. Isi data Medis (DSM-5, ASAM)
            4. Klik Analisis
            """)
            st.divider()
            st.caption("v4.0.0 - Compliance Edition")

    @staticmethod
    def input_section_legal():
        st.markdown("### ⚖️ 1. Parameter Hukum (SEMA 4/2010)")
        with st.container():
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                jenis_narkotika = st.selectbox("Jenis Narkotika", list(GRAMATUR_LIMITS.keys()))
                limit = GRAMATUR_LIMITS[jenis_narkotika]
                st.caption(f"Batas SEMA: **{limit} gram**")
                
                bb_amount = st.number_input("Barang Bukti (Gram)", min_value=0.0, step=0.01, format="%.2f")
                
                # Visual Check
                if limit > 0:
                    ratio = bb_amount / limit
                    if ratio > 1:
                        st.error(f"⚠️ Melebihi Batas ({ratio:.1f}x)")
                    else:
                        st.success("✅ Di bawah Batas SEMA")

            with col2:
                peran = st.selectbox("Peran Tersangka", ["Pengguna", "Kurir", "Pengedar", "Bandar"])
                residivis = st.checkbox("Status Residivis?")
                status_tangkap = st.radio("Status Penangkapan", ["Tertangkap Tangan", "Pengembangan/Target Ops", "Lapor Diri"])
            
            st.markdown('</div>', unsafe_allow_html=True)
            return jenis_narkotika, limit, bb_amount, peran, residivis, status_tangkap

    @staticmethod
    def input_section_medical():
        st.markdown("### 🏥 2. Parameter Klinis")
        
        # DSM-5 Simple Checklist
        with st.expander("📝 DSM-5 Checklist (12 Bulan Terakhir)", expanded=True):
            dsm_criteria = [
                "Menggunakan lebih banyak/lama dari rencana",
                "Ingin berhenti tapi gagal",
                "Banyak waktu habis untuk zat",
                "Craving (Sugesti kuat)",
                "Gagal memenuhi kewajiban (Kerja/Sekolah)",
                "Masalah sosial akibat zat",
                "Melepas aktivitas penting",
                "Menggunakan di situasi berbahaya",
                "Masalah fisik/psikologis lanjut",
                "Toleransi (Butuh dosis naik)",
                "Withdrawal (Sakau)"
            ]
            dsm_selected = []
            cols = st.columns(2)
            for i, crit in enumerate(dsm_criteria):
                if cols[i % 2].checkbox(crit, key=f"dsm_{i}"):
                    dsm_selected.append(crit)
            dsm_count = len(dsm_selected)
            st.caption(f"Total Kriteria Terpenuhi: **{dsm_count}/11**")

        # ASAM Dimensions
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ASAM 6 Dimensions Severity (0-4)")
        asam_scores = {}
        cols_asam = st.columns(3)
        for dim_id, dim_name in ASAM_DIMENSIONS.items():
            idx = (dim_id - 1) % 3
            with cols_asam[idx]:
                val = st.slider(f"D{dim_id}: {dim_name}", 0, 4, 0, help="0: None, 4: Severe/Danger")
                asam_scores[dim_id] = val

        # Additional Risk
        col_risk1, col_risk2 = st.columns(2)
        with col_risk1:
            assist_risk = st.selectbox("Risiko ASSIST (WHO)", ["Low", "Moderate", "High"])
        with col_risk2:
            suicide_risk = st.slider("Risiko Bunuh Diri (C-SSRS Level)", 0, 5, 0, help="4-5: High Risk")

        return dsm_count, asam_scores, assist_risk, suicide_risk

    @staticmethod
    def input_section_lab():
        st.markdown("### 🧪 3. Data Laboratorium")
        with st.expander("Input Hasil Tes Urine (Opsional)", expanded=False):
            lab_data = {}
            for zat, cutoff in LAB_CUTOFFS.items():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    val = st.number_input(f"Kadar {zat} (ng/mL)", 0.0, step=10.0, key=f"lab_{zat}")
                with col_b:
                    st.caption(f"Cutoff: {cutoff}")
                if val > 0:
                    lab_data[zat] = val
        return lab_data

    @staticmethod
    def render_results(decision: Dict, inputs: Dict):
        st.divider()
        st.header("📊 HASIL ANALISIS OTOMATIS")
        
        # 1. Main Recommendation Box
        color_class = f"status-{decision['status_warna']}"
        st.markdown(f"""
        <div class="result-box {color_class}">
            <h2 style="margin:0">REKOMENDASI:</h2>
            <h1 style="margin:0.5rem 0; font-size: 2.5rem;">{decision['rekomendasi']}</h1>
            <p style="opacity: 0.9">{decision.get('urgency', 'Normal Priority')}</p>
        </div>
        """, unsafe_allow_html=True)

        # 2. Reasoning Columns
        col_res1, col_res2 = st.columns([1, 1])
        
        with col_res1:
            st.subheader("🔍 Alasan Sistem")
            for reason in decision['alasan']:
                if "✓" in reason:
                    st.success(reason)
                elif "⚠️" in reason:
                    st.warning(reason)
                elif "🚨" in reason or "❌" in reason:
                    st.error(reason)
                else:
                    st.info(reason)

        with col_res2:
            st.subheader("📈 Profil Klinis")
            # Radar Chart for ASAM
            df_asam = pd.DataFrame({
                'Dimensi': [f"D{k}" for k in inputs['asam_scores'].keys()],
                'Score': list(inputs['asam_scores'].values())
            })
            fig = px.line_polar(df_asam, r='Score', theta='Dimensi', line_close=True, range_r=[0,4])
            fig.update_traces(fill='toself')
            fig.update_layout(title="Profil Keparahan ASAM", height=300)
            st.plotly_chart(fig, use_container_width=True)

        # 3. Legal Summary
        st.subheader("⚖️ Ringkasan Posisi Hukum")
        legal_df = pd.DataFrame({
            "Parameter": ["Barang Bukti", "Batas SEMA", "Selisih", "Peran", "Residivis"],
            "Nilai": [
                f"{inputs['bb_amount']} g",
                f"{inputs['bb_limit']} g",
                f"{inputs['bb_amount'] - inputs['bb_limit']:.2f} g ({'Melebihi' if inputs['bb_amount'] > inputs['bb_limit'] else 'Aman'})",
                inputs['peran'],
                "Ya" if inputs['is_residivis'] else "Tidak"
            ]
        })
        st.table(legal_df)

# =============================================================================
# 4. MAIN CONTROLLER
# =============================================================================

def main():
    TATUI.render_css()
    TATUI.render_header()
    TATUI.render_sidebar()

    # Initialize Session State
    if 'analyzed' not in st.session_state:
        st.session_state['analyzed'] = False
        st.session_state['decision'] = {}
        st.session_state['inputs'] = {}

    # Tabs Layout
    tab_input, tab_result, tab_report = st.tabs(["📝 Input Data", "📊 Hasil Analisis", "🖨️ Laporan"])

    # --- TAB 1: INPUT ---
    with tab_input:
        with st.form("tat_form"):
            # Section 1: Identity (Simplified)
            col_id1, col_id2 = st.columns(2)
            with col_id1:
                nama = st.text_input("Nama/Inisial Klien")
            with col_id2:
                usia = st.number_input("Usia", 10, 80, 25)

            st.divider()
            
            # Section 2: Legal
            jenis_narkotika, limit, bb_amount, peran, residivis, status_tangkap = TATUI.input_section_legal()
            
            st.divider()

            # Section 3: Medical
            dsm_count, asam_scores, assist_risk, suicide_risk = TATUI.input_section_medical()
            
            # Section 4: Lab
            lab_data = TATUI.input_section_lab()

            submitted = st.form_submit_button("🔍 ANALISIS SEKARANG", type="primary", use_container_width=True)

            if submitted:
                # Calculate
                decision = TATLogicEngine.determine_recommendation(
                    asam_scores=asam_scores,
                    dsm5_count=dsm_count,
                    suicide_risk_level=suicide_risk,
                    assist_risk=assist_risk,
                    bb_amount=bb_amount,
                    bb_limit=limit,
                    peran=peran,
                    is_residivis=residivis
                )
                
                # Store State
                st.session_state['analyzed'] = True
                st.session_state['decision'] = decision
                st.session_state['inputs'] = {
                    'nama': nama,
                    'usia': usia,
                    'bb_amount': bb_amount,
                    'bb_limit': limit,
                    'peran': peran,
                    'is_residivis': residivis,
                    'asam_scores': asam_scores,
                    'dsm_count': dsm_count,
                    'lab_data': lab_data
                }
                st.rerun()

    # --- TAB 2: RESULT ---
    with tab_result:
        if st.session_state['analyzed']:
            TATUI.render_results(st.session_state['decision'], st.session_state['inputs'])
        else:
            st.info("Silakan isi data dan klik Analisis pada tab Input Data.")

    # --- TAB 3: REPORT ---
    with tab_report:
        if st.session_state['analyzed']:
            inputs = st.session_state['inputs']
            decision = st.session_state['decision']
            
            report_text = f"""
            LAPORAN SEMENTARA HASIL ASESMEN
            ================================
            Tanggal: {datetime.now().strftime('%Y-%m-%d')}
            Nama: {inputs['nama']}
            
            A. KESIMPULAN REKOMENDASI
            {decision['rekomendasi']}
            
            B. DASAR PERTIMBANGAN
            1. Hukum:
               - Barang Bukti: {inputs['bb_amount']}g (Batas SEMA: {inputs['bb_limit']}g)
               - Peran: {inputs['peran']}
            
            2. Medis:
               - Tingkat Adiksi (DSM-5): {inputs['dsm_count']} kriteria
               - Profil ASAM: {list(inputs['asam_scores'].values())}
            
            C. ALASAN DETIL
            {chr(10).join(['- ' + r for r in decision['alasan']])}
            """
            
            st.text_area("Copy Laporan", report_text, height=400)
            st.download_button("Download TXT", report_text, file_name="laporan_tat.txt")
        else:
            st.warning("Data belum tersedia.")

if __name__ == "__main__":
    main()
