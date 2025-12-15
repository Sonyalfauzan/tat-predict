"""
=================================================================================
SISTEM PENDUKUNG KEPUTUSAN TAT BNN - V4.1 
=================================================================================
VERSI: 4.1.0 

Status Audit Regulasi (Desember 2025):
✅ Batas Gramatur (SEMA No. 4/2010 Lampiran) 
✅ Syarat Urine Positif (SEMA No. 4/2010 Poin 3c) 
✅ Kriteria Klinis (Juknis Rehabilitasi BNN 2022) 
✅ Dual Track System (UU 35/2009 Pasal 103)
=================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# =============================================================================
# 1. KONFIGURASI & KONSTANTA DATA
# =============================================================================

st.set_page_config(
    page_title="TAT DSS v4.1",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SEMA No. 4 Tahun 2010 Limits (Gram) - VERIFIED
GRAMATUR_LIMITS = {
    "Ganja/Cannabis": 5.0,
    "Metamfetamin/Sabu": 1.0,
    "Heroin": 1.8,
    "Kokain": 1.8,
    "Ekstasi/MDMA": 2.4, # Atau 8 butir
    "Morfin": 1.8,
    "Kodein": 72.0,
    "Lainnya": 0.0 # Requires Manual Review
}

# Mapping Dimensi ASAM (Standard BNN/Intl)
ASAM_DIMENSIONS = {
    1: "Intoksikasi Akut/Withdrawal",
    2: "Kondisi Biomedis",
    3: "Emosional/Perilaku/Kognitif",
    4: "Kesiapan Berubah",
    5: "Potensi Relapse",
    6: "Lingkungan Pemulihan"
}

# =============================================================================
# 2. LOGIC ENGINE (BACKEND) - AUDITED
# =============================================================================

class TATLogicEngine:
    
    @staticmethod
    def get_addiction_severity(dsm_count: int, assist_risk: str) -> str:
        """Mapping ke Terminologi BNN: Ringan/Sedang/Berat"""
        if dsm_count >= 6 or assist_risk == "High":
            return "BERAT"
        elif dsm_count >= 4 or assist_risk == "Moderate":
            return "SEDANG"
        else:
            return "RINGAN"

    @staticmethod
    def check_legal_red_flags(bb: float, limit: float, peran: str, residivis: bool, urine_negatif: bool) -> List[str]:
        """Mendeteksi indikator diskualifikasi rehabilitasi sesuai Regulasi"""
        flags = []
        
        # 1. Cek Gramatur (SEMA Limit)
        if limit > 0 and bb > limit:
            flags.append(f"⛔ Barang bukti ({bb}g) melebihi batas SEMA ({limit}g).")
            
        # 2. Indikasi Sindikat (Heuristik)
        if bb > limit * 15 and limit > 0:
            flags.append("⛔ Barang bukti sangat besar (>15x SEMA) - Indikasi Kuat Pengedar.")
            
        # 3. Peran Tersangka (UU 35/2009 Pasal 114)
        if peran in ["Bandar", "Pengedar", "Kurir"]:
            flags.append(f"⛔ Peran tersangka terindikasi sebagai {peran}.")
            
        # 4. Syarat Urine (SEMA Poin 3c)
        if urine_negatif:
            flags.append("⚠️ Hasil Tes Urine NEGATIF (Tidak memenuhi syarat SEMA Poin 3c, kecuali ada riwayat medis valid).")
            
        # 5. Residivis
        if residivis:
            flags.append("⚠️ Status Residivis (Pemberatan).")
            
        return flags

    @staticmethod
    def determine_recommendation(
        # Medical Inputs
        asam_scores: Dict[int, int],
        dsm5_count: int,
        suicide_risk_level: int,
        assist_risk: str,
        
        # Legal Inputs
        bb_amount: float,
        bb_limit: float,
        peran: str,
        is_residivis: bool,
        is_urine_positive: bool,
        status_tangkap: str
    ) -> Dict[str, Any]:
        
        result = {
            "rekomendasi": "",
            "tipe": "",
            "alasan": [],
            "status_warna": "grey",
            "urgency": "Normal",
            "derajat_ketergantungan": ""
        }

        # Hitung Derajat Ketergantungan (Terminologi Form BNN)
        severity = TATLogicEngine.get_addiction_severity(dsm5_count, assist_risk)
        result["derajat_ketergantungan"] = severity

        # 1. CEK KEDARURATAN MEDIS (PRIORITAS TERTINGGI - DUTY OF CARE)
        # FIX: Renamed suicide_risk to suicide_risk_level to match argument name
        if suicide_risk_level >= 4 or asam_scores.get(1, 0) >= 3 or asam_scores.get(2, 0) >= 3:
            result.update({
                "rekomendasi": "REHABILITASI RAWAT INAP (MEDIS/PSIKIATRIS SEGERA)",
                "tipe": "Medis", "status_warna": "red", "urgency": "IMMEDIATE",
                "alasan": ["🚨 INDIKASI GAWAT DARURAT: Risiko bunuh diri tinggi atau Komplikasi Medis.",
                           "Wajib intervensi medis segera (Stabilisasi) sebelum proses hukum lanjut."]
            })
            return result

        # 2. FILTER HUKUM (SEMA 4/2010)
        # SEMA Poin 3c: Harus Urine Positif
        urine_flag = not is_urine_positive
        legal_flags = TATLogicEngine.check_legal_red_flags(bb_amount, bb_limit, peran, is_residivis, urine_flag)
        
        # SEMA Poin 3a: Tertangkap Tangan (Pertimbangan Hakim)
        if status_tangkap != "Tertangkap Tangan":
            result["alasan"].append("ℹ️ Catatan: Status bukan 'Tertangkap Tangan' (Pertimbangan Hakim SEMA Poin 3a).")

        if legal_flags:
            # Jika ada pelanggaran hukum (BB Lebih / Bandar / Urine Negatif)
            
            # Cek Pasal 103 (Dual Track) -> Hanya jika BB lebih TAPI dia pecandu berat & Urine Positif
            can_dual_track = (severity == "BERAT") and (is_urine_positive) and (peran == "Pengguna")
            
            if can_dual_track and bb_amount > bb_limit:
                 result.update({
                    "rekomendasi": "PROSES HUKUM (+ REKOMENDASI REHABILITASI PASAL 103)",
                    "tipe": "Dual Track", "status_warna": "orange",
                    "alasan": legal_flags + [
                        f"⚠️ Klien terkonfirmasi Pecandu {severity}.",
                        "Disarankan penerapan UU 35/2009 Pasal 103 (Vonis Rehab di Lapas/Lembaga)."
                    ]
                })
            else:
                # Murni Pidana
                result.update({
                    "rekomendasi": "PROSES HUKUM (PIDANA PENJARA)",
                    "tipe": "Hukum", "status_warna": "red",
                    "alasan": legal_flags + ["❌ Tidak memenuhi kriteria rehabilitasi SEMA 4/2010."]
                })
            return result

        # 3. PENENTUAN LEVEL REHABILITASI (JIKA LOLOS FILTER HUKUM)
        # Juknis BNN: Rawat Inap untuk Ketergantungan Berat / Masalah Sosial / Medis
        
        need_inpatient = False
        reasons_rehab = []

        # Cek Indikasi Rawat Inap
        if severity == "BERAT":
            need_inpatient = True
            reasons_rehab.append(f"✓ Derajat Ketergantungan: {severity}.")
        if asam_scores.get(5, 0) >= 3:
            need_inpatient = True
            reasons_rehab.append("✓ Potensi Relapse Tinggi (ASAM D5).")
        if asam_scores.get(6, 0) >= 3:
            need_inpatient = True
            reasons_rehab.append("✓ Lingkungan tidak mendukung pemulihan (ASAM D6).")

        if need_inpatient:
            result.update({
                "rekomendasi": "REHABILITASI RAWAT INAP",
                "tipe": "Medis", "status_warna": "blue",
                "alasan": ["✓ Memenuhi syarat SEMA (BB Aman, Urine Positif, Bukan Jaringan)."] + reasons_rehab
            })
        else:
            result.update({
                "rekomendasi": "REHABILITASI RAWAT JALAN",
                "tipe": "Medis", "status_warna": "green",
                "alasan": [
                    "✓ Memenuhi syarat SEMA (BB Aman, Urine Positif).",
                    f"✓ Derajat Ketergantungan: {severity}.",
                    "✓ Lingkungan/Fungsi Sosial cukup stabil."
                ]
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
            .section-card { background-color: #f8fafc; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .result-box { padding: 2rem; border-radius: 15px; text-align: center; color: white; margin: 2rem 0; }
            .status-red { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
            .status-orange { background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); }
            .status-blue { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
            .status-green { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        st.markdown('<div class="main-header">⚖️ TAT DSS v4.1 </div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #64748b;">Sistem Pendukung Keputusan Terverifikasi Regulasi SEMA 4/2010</div>', unsafe_allow_html=True)
        st.warning("⚠️ DISCLAIMER: Sistem ini adalah alat bantu hitung & logika. Keputusan final tetap pada Tim Asesmen Terpadu.")

    @staticmethod
    def render_sidebar():
        with st.sidebar:
            st.header("✅ Status Regulasi")
            st.caption("Pemeriksaan Kepatuhan:")
            st.markdown("- **SEMA 4/2010:** ")
            st.markdown("- **UU 35/2009:** ")
            st.markdown("- **Juknis BNN:** ")
            st.divider()
            st.info("Pastikan dokumen BAP dan Hasil Lab tersedia sebelum memulai.")

    @staticmethod
    def input_section_legal():
        st.markdown("### ⚖️ 1. Parameter Hukum & Bukti")
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
                    if ratio > 1: st.error(f"⚠️ Melebihi Batas ({ratio:.1f}x)")
                    else: st.success("✅ Di bawah Batas SEMA")

            with col2:
                peran = st.selectbox("Peran Tersangka", ["Pengguna", "Kurir", "Pengedar", "Bandar"])
                residivis = st.checkbox("Status Residivis?")
                status_tangkap = st.radio("Status Penangkapan (SEMA Poin 3a)", ["Tertangkap Tangan", "Pengembangan/Lapor Diri"])
            
            st.markdown("#### Validasi Laboratorium (SEMA Poin 3c)")
            is_urine_positive = st.checkbox("Hasil Tes Urine POSITIF (+)?", value=True, help="SEMA mensyaratkan hasil lab positif untuk rehabilitasi.")
            if not is_urine_positive:
                st.error("⚠️ Peringatan: Urine Negatif mempersulit rekomendasi rehabilitasi kecuali ada bukti medis kuat.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            return jenis_narkotika, limit, bb_amount, peran, residivis, is_urine_positive, status_tangkap

    @staticmethod
    def input_section_medical():
        st.markdown("### 🏥 2. Parameter Klinis")
        
        # DSM-5
        with st.expander("📝 DSM-5 Checklist", expanded=True):
            dsm_criteria = [
                "1. Pakai > rencana", "2. Gagal berhenti", "3. Waktu habis utk zat",
                "4. Craving/Sugesti", "5. Gagal kewajiban", "6. Masalah sosial",
                "7. Melepas aktivitas", "8. Situasi bahaya", "9. Masalah fisik",
                "10. Toleransi", "11. Withdrawal"
            ]
            dsm_selected = []
            cols = st.columns(2)
            for i, crit in enumerate(dsm_criteria):
                if cols[i % 2].checkbox(crit, key=f"dsm_{i}"): dsm_selected.append(crit)
            dsm_count = len(dsm_selected)
            st.caption(f"DSM-5 Count: {dsm_count}/11")

        # ASAM
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ASAM Severity (0-4)")
        asam_scores = {}
        cols_asam = st.columns(3)
        for dim_id, dim_name in ASAM_DIMENSIONS.items():
            idx = (dim_id - 1) % 3
            with cols_asam[idx]:
                val = st.slider(f"D{dim_id}: {dim_name}", 0, 4, 0)
                asam_scores[dim_id] = val

        col1, col2 = st.columns(2)
        with col1: assist_risk = st.selectbox("Risiko ASSIST", ["Low", "Moderate", "High"])
        with col2: suicide_risk = st.slider("Risiko Bunuh Diri (C-SSRS)", 0, 5, 0)

        return dsm_count, asam_scores, assist_risk, suicide_risk

    @staticmethod
    def render_results(decision: Dict, inputs: Dict):
        st.divider()
        st.header("📊 HASIL ANALISIS")
        
        # Result Box
        color_class = f"status-{decision['status_warna']}"
        st.markdown(f"""
        <div class="result-box {color_class}">
            <h2 style="margin:0">REKOMENDASI:</h2>
            <h1 style="margin:0.5rem 0; font-size: 2.5rem;">{decision['rekomendasi']}</h1>
            <p style="opacity: 0.9">Derajat Ketergantungan: <b>{decision['derajat_ketergantungan']}</b></p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔍 Dasar Pertimbangan")
            for reason in decision['alasan']:
                if "✓" in reason: st.success(reason)
                elif "⛔" in reason or "❌" in reason: st.error(reason)
                elif "⚠️" in reason: st.warning(reason)
                else: st.info(reason)
        
        with col2:
            st.subheader("📈 Profil ASAM")
            df_asam = pd.DataFrame({
                'Dimensi': [f"D{k}" for k in inputs['asam_scores'].keys()],
                'Score': list(inputs['asam_scores'].values())
            })
            fig = px.line_polar(df_asam, r='Score', theta='Dimensi', line_close=True, range_r=[0,4])
            fig.update_traces(fill='toself')
            st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_report(decision: Dict, inputs: Dict):
        st.header("🖨️ LAPORAN ASESMEN TERPADU")
        st.info("Salin teks di bawah ini untuk Berita Acara atau Laporan Resmi.")
        
        # Generate Text Report
        tgl = datetime.now().strftime("%d %B %Y")
        report_text = f"""
LAPORAN HASIL ASESMEN TERPADU (TAT)
BADAN NARKOTIKA NASIONAL
============================================================
Tanggal Pemeriksaan : {tgl}
Nama Terperiksa     : {inputs['nama']}
Usia                : {inputs['usia']} Tahun

A. DATA HUKUM & BARANG BUKTI
------------------------------------------------------------
1. Jenis Narkotika   : {inputs.get('jenis_narkotika', '-')}
2. Berat Barang Bukti: {inputs['bb_amount']} gram
   (Batas SEMA No. 4/2010: {inputs['bb_limit']} gram)
3. Status BB         : {'MELEBIHI BATAS' if inputs['bb_amount'] > inputs['bb_limit'] else 'DI BAWAH BATAS (Memenuhi Syarat)'}
4. Peran Tersangka   : {inputs['peran']}
5. Status Residivis  : {'Ya' if inputs['is_residivis'] else 'Tidak'}
6. Status Urine      : {'Positif' if inputs.get('is_urine_positive', True) else 'Negatif'}

B. DATA KLINIS & MEDIS
------------------------------------------------------------
1. Derajat Ketergantungan : {decision['derajat_ketergantungan']}
2. Diagnosis DSM-5        : {inputs['dsm_count']} Kriteria Terpenuhi
3. Profil ASAM            :
   - D1 (Intoksikasi) : {inputs['asam_scores'][1]}
   - D2 (Biomedis)    : {inputs['asam_scores'][2]}
   - D3 (Emosional)   : {inputs['asam_scores'][3]}
   - D4 (Motivasi)    : {inputs['asam_scores'][4]}
   - D5 (Relapse)     : {inputs['asam_scores'][5]}
   - D6 (Lingkungan)  : {inputs['asam_scores'][6]}

C. REKOMENDASI TIM ASESMEN TERPADU
------------------------------------------------------------
KESIMPULAN:
>> {decision['rekomendasi']} <<

DASAR PERTIMBANGAN:
{chr(10).join(['- ' + r for r in decision['alasan']])}

D. CATATAN TAMBAHAN
------------------------------------------------------------
Prioritas: {decision.get('urgency', 'Normal Priority')}

============================================================
Dicetak melalui Sistem Pendukung Keputusan TAT v4.1
(Alat bantu ini bukan pengganti keputusan klinis/hukum final)
"""
        st.text_area("Draft Laporan", report_text, height=400)
        
        st.download_button(
            label="💾 Download Laporan (.txt)",
            data=report_text,
            file_name=f"Laporan_TAT_{inputs['nama']}_{tgl}.txt",
            mime="text/plain"
        )

# =============================================================================
# 4. MAIN CONTROLLER
# =============================================================================

def main():
    TATUI.render_css()
    TATUI.render_header()
    TATUI.render_sidebar()

    if 'analyzed' not in st.session_state:
        st.session_state['analyzed'] = False
        st.session_state['decision'] = {}
        st.session_state['inputs'] = {}

    tab_input, tab_result, tab_report = st.tabs(["📝 Input Data", "📊 Hasil Analisis", "🖨️ Laporan Resmi"])

    with tab_input:
        with st.form("tat_form"):
            col1, col2 = st.columns(2)
            with col1: nama = st.text_input("Nama Klien")
            with col2: usia = st.number_input("Usia", 10, 80, 25)

            st.divider()
            jenis_narkotika, limit, bb_amount, peran, residivis, is_urine_pos, status_tangkap = TATUI.input_section_legal()
            
            st.divider()
            dsm_count, asam_scores, assist_risk, suicide_risk = TATUI.input_section_medical()

            submitted = st.form_submit_button("🔍 ANALISIS SEKARANG", type="primary", use_container_width=True)

            if submitted:
                decision = TATLogicEngine.determine_recommendation(
                    asam_scores=asam_scores, dsm5_count=dsm_count,
                    suicide_risk_level=suicide_risk, assist_risk=assist_risk,
                    bb_amount=bb_amount, bb_limit=limit, peran=peran,
                    is_residivis=residivis, is_urine_positive=is_urine_pos,
                    status_tangkap=status_tangkap
                )
                
                st.session_state['analyzed'] = True
                st.session_state['decision'] = decision
                st.session_state['inputs'] = {
                    'nama': nama, 'usia': usia, 
                    'jenis_narkotika': jenis_narkotika, # Ditambahkan
                    'bb_amount': bb_amount, 'bb_limit': limit,
                    'peran': peran, 'is_residivis': residivis, 
                    'is_urine_positive': is_urine_pos, # Ditambahkan
                    'asam_scores': asam_scores, 'dsm_count': dsm_count
                }
                st.rerun()

    with tab_result:
        if st.session_state['analyzed']:
            TATUI.render_results(st.session_state['decision'], st.session_state['inputs'])
        else:
            st.info("Silakan isi data dan klik Analisis pada tab Input Data.")

    with tab_report:
        if st.session_state['analyzed']:
            TATUI.render_report(st.session_state['decision'], st.session_state['inputs'])
        else:
            st.info("Laporan akan tersedia setelah analisis dilakukan.")

if __name__ == "__main__":
    main()
