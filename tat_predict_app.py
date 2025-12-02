"""
=================================================================================
SISTEM PENDUKUNG KEPUTUSAN TIM ASESMEN TERPADU (TAT) BNN
=================================================================================
Tools bantu untuk proses asesmen narkotika berdasarkan:
- UU No. 35 Tahun 2009 tentang Narkotika
- SEMA No. 4 Tahun 2010 tentang Penanganan Pecandu Narkotika
- Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014 tentang Tata Cara Penanganan Pecandu Narkotika
- Perka BNN No. 11 Tahun 2014 tentang Tata Cara Penanganan Tersangka dan/atau Terdakwa Pecandu Narkotika
- Instrumen Asesmen: ASAM (6 Dimensi), DSM-5, ASSIST, ICD-10, DAST-10
CATATAN HUKUM PENTING:
1. Sistem ini adalah ALAT BANTU untuk Tim Asesmen Terpadu (TAT) sesuai Pasal 8 ayat (2) Perka BNN No. 11 Tahun 2014. [[30]]
2. Tim Asesmen Terpadu terdiri dari Tim Dokter dan Tim Hukum yang ditetapkan oleh pimpinan. [[1]]
3. Keputusan final tetap ada di tangan Tim Asesmen Terpadu dan aparat penegak hukum yang berwenang.
4. Biaya Pelaksanaan asesmen yang dilakukan oleh Tim Asesmen Terpadu dibebankan pada anggaran Badan Narkotika Nasional. [[4]]
=================================================================================
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import numpy as np
from typing import Dict, List, Tuple, Optional

# =============================================================================
# KONFIGURASI HALAMAN
# =============================================================================
st.set_page_config(
    page_title="TAT Decision Support System - BNN",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS - Enhanced with BNN branding
# =============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        color: #1e3a8a;
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.2rem;
        border-radius: 1rem;
        border-left: 4px solid #1e3a8a;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .warning-box {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .info-box {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .success-box {
        background-color: #dcfce7;
        border-left: 4px solid #22c55e;
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .legal-box {
        background-color: #f3e8ff;
        border-left: 4px solid #8b5cf6;
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .asam-dimension {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 1rem;
        border-radius: 0.8rem;
        margin: 0.8rem 0;
        border-left: 3px solid #3b82f6;
    }
    .severity-low { background-color: #dcfce7; border-left: 3px solid #22c55e; }
    .severity-moderate { background-color: #fef3c7; border-left: 3px solid #f59e0b; }
    .severity-high { background-color: #fee2e2; border-left: 3px solid #ef4444; }
    .severity-severe { background-color: #fecaca; border-left: 3px solid #dc2626; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# KONSTANTA DAN KONFIGURASI SESUAI REGULASI
# =============================================================================

# Gramatur berdasarkan SEMA 4/2010 untuk rehabilitasi
GRAMATUR_LIMITS = {
    "Ganja/Cannabis": 5.0,
    "Metamfetamin/Sabu": 1.0,
    "Heroin": 1.8,
    "Kokain": 1.8,
    "Ekstasi/MDMA": 2.4,
    "Morfin": 1.8,
    "Kodein": 72.0,
    "Lainnya": 1.0
}

# Jenis-jenis narkotika untuk tes urine
JENIS_NARKOTIKA = [
    "Metamfetamin (MET/Sabu)",
    "Morfin (MOP/Heroin)", 
    "Kokain (COC)",
    "Amfetamin (AMP)",
    "Benzodiazepin (BZO)",
    "THC (Ganja)",
    "MDMA (Ekstasi)",
    "Lainnya"
]

# Kriteria DSM-5 (11 kriteria gangguan penggunaan zat)
DSM5_CRITERIA = [
    "Menggunakan dalam jumlah/waktu lebih lama dari yang direncanakan",
    "Keinginan kuat/gagal mengurangi penggunaan",
    "Banyak waktu untuk mendapatkan/menggunakan/pulih dari efek",
    "Craving (keinginan kuat menggunakan)",
    "Gagal memenuhi kewajiban (kerja/sekolah/rumah)",
    "Terus menggunakan meski ada masalah sosial/interpersonal",
    "Mengurangi/meninggalkan aktivitas penting karena penggunaan",
    "Menggunakan dalam situasi berbahaya",
    "Terus menggunakan meski tahu ada masalah fisik/psikologis",
    "Toleransi (butuh dosis lebih tinggi)",
    "Withdrawal/Sakau (gejala putus zat)"
]

# ASAM 6 Dimensions dengan severity levels
ASAM_DIMENSIONS = {
    1: {
        "name": "Intoksikasi Akut dan/atau Potensi Withdrawal",
        "description": "Gejala fisik penggunaan atau putus zat, risiko komplikasi medis akut",
        "severity_levels": {
            0: "Tidak ada gejala intoksikasi atau withdrawal",
            1: "Gejala ringan, stabil secara medis",
            2: "Gejala sedang, perlu monitoring",
            3: "Gejala berat, perlu intervensi medis",
            4: "Gejala severe, mengancam jiwa"
        }
    },
    2: {
        "name": "Kondisi Medis Biomedis",
        "description": "Penyakit fisik yang menyertai, kebutuhan perawatan medis",
        "severity_levels": {
            0: "Tidak ada kondisi medis signifikan",
            1: "Kondisi medis ringan, terkontrol",
            2: "Kondisi medis sedang, perlu monitoring",
            3: "Kondisi medis berat, mempengaruhi fungsi",
            4: "Kondisi medis severe, mengancam jiwa"
        }
    },
    3: {
        "name": "Kondisi Emosional/Behavioral/Kognitif",
        "description": "Gangguan mental komorbid, risiko bunuh diri/membahayakan",
        "severity_levels": {
            0: "Tidak ada gangguan psikiatrik",
            1: "Gangguan ringan, berfungsi baik",
            2: "Gangguan sedang, gangguan fungsi",
            3: "Gangguan berat, risiko sedang",
            4: "Gangguan severe, risiko tinggi bunuh diri/kekerasan"
        }
    },
    4: {
        "name": "Kesiapan untuk Berubah",
        "description": "Motivasi untuk pulih, resistensi terhadap perawatan",
        "severity_levels": {
            0: "Sangat termotivasi, komitmen tinggi",
            1: "Termotivasi, komitmen sedang",
            2: "Ambivalen, perlu motivasi",
            3: "Resistensi ringan-sedang",
            4: "Resistensi berat, menolak perawatan"
        }
    },
    5: {
        "name": "Potensi Relapse/Kontinuasi Penggunaan",
        "description": "Riwayat relapse, faktor risiko kambuh",
        "severity_levels": {
            0: "Tidak ada riwayat relapse, dukungan kuat",
            1: "Riwayat relapse ringan, faktor protektif",
            2: "Riwayat relapse sedang, faktor risiko moderat",
            3: "Riwayat relapse berat, faktor risiko tinggi",
            4: "Riwayat relapse kronis, faktor risiko severe"
        }
    },
    6: {
        "name": "Lingkungan Pemulihan/Hidup",
        "description": "Dukungan sosial, lingkungan kondusif untuk pemulihan",
        "severity_levels": {
            0: "Lingkungan sangat mendukung, bebas narkoba",
            1: "Lingkungan cukup mendukung, minim paparan",
            2: "Lingkungan netral, perlu dukungan tambahan",
            3: "Lingkungan kurang mendukung, paparan sedang",
            4: "Lingkungan tidak mendukung, paparan tinggi"
        }
    }
}

# Level Perawatan ASAM
ASAM_LEVELS = {
    "0.5": "Intervensi Awal",
    "1": "Rawat Jalan (Outpatient)",
    "2": "Intensive Outpatient/Partial Hospitalization",
    "3": "Residential/Inpatient",
    "4": "Medically-Managed Intensive Inpatient"
}

# ASSIST Scoring Categories
ASSIST_CATEGORIES = {
    "Tobacco": "Rokok",
    "Alcohol": "Alkohol", 
    "Cannabis": "Ganja",
    "Cocaine": "Kokain",
    "Amphetamines": "Sabu/Amfetamin",
    "Sedatives": "Obat Penenang",
    "Opioids": "Opioid/Heroin",
    "Hallucinogens": "Halusinogen"
}

# =============================================================================
# FUNGSI PERHITUNGAN SKOR SESUAI STANDAR
# =============================================================================

def calculate_asam_score(asam_scores: Dict[int, int]) -> Tuple[float, str, Dict]:
    """
    Menghitung skor ASAM berdasarkan 6 dimensi dengan severity rating 0-4
    Menggunakan metode risk rating matrix sesuai standar ASAM
    """
    total_score = sum(asam_scores.values())
    max_possible = 6 * 4  # 6 dimensions × max severity 4
    
    # Hitung rata-rata severity
    avg_severity = total_score / 6
    
    # Tentukan level perawatan berdasarkan dimensi tertinggi dan rata-rata
    max_severity = max(asam_scores.values())
    
    if max_severity == 0:
        level = "0.5"
        description = "Intervensi Awal - Edukasi dan monitoring"
    elif max_severity <= 1 and avg_severity <= 1:
        level = "1"
        description = "Rawat Jalan - 1-2 sesi/minggu"
    elif max_severity <= 2 and avg_severity <= 1.5:
        level = "2"
        description = "Intensive Outpatient - 3-5 sesi/minggu"
    elif max_severity <= 3:
        level = "3"
        description = "Residential/Inpatient - Perawatan 24 jam"
    else:
        level = "4"
        description = "Medically-Managed Intensive - ICU/Perawatan intensif"
    
    # Hitung persentase severity
    severity_percentage = (total_score / max_possible) * 100
    
    # Breakdown detail per dimensi
    breakdown = {}
    for dim, score in asam_scores.items():
        dimension_info = ASAM_DIMENSIONS[dim]
        breakdown[f"Dimensi {dim}"] = {
            'name': dimension_info['name'],
            'score': score,
            'max': 4,
            'severity': list(dimension_info['severity_levels'].values())[score],
            'description': dimension_info['description']
        }
    
    return severity_percentage, level, breakdown

def calculate_assist_score(assist_responses: Dict[str, int]) -> Tuple[int, str, Dict]:
    """
    Menghitung skor ASSIST (Alcohol, Smoking and Substance Involvement Screening Test)
    Skala: 0-39, dengan kategori:
    0-3: Low risk
    4-26: Moderate risk  
    27+: High risk
    """
    total_score = sum(assist_responses.values())
    
    if total_score <= 3:
        risk_level = "Low Risk"
        recommendation = "Minimal intervention, brief advice"
    elif total_score <= 26:
        risk_level = "Moderate Risk"
        recommendation = "Brief intervention, continued monitoring"
    else:
        risk_level = "High Risk"
        recommendation = "Intensive intervention, referral to specialist"
    
    breakdown = {}
    for substance, score in assist_responses.items():
        cat_name = ASSIST_CATEGORIES.get(substance, substance)
        breakdown[cat_name] = {
            'score': score,
            'max': 39,
            'risk_contribution': f"Kontribusi risiko untuk {cat_name.lower()}"
        }
    
    return total_score, risk_level, breakdown

def calculate_medical_composite(asam_pct: float, dsm5_count: int, 
                              assist_score: int, ada_komorbid: bool, 
                              komorbid_severity: str) -> Tuple[float, Dict]:
    """
    Menghitung skor komposit medis berdasarkan multiple instrumen
    Bobot:
    - ASAM: 50% (komprehensif)
    - DSM-5: 30% (diagnostik)
    - ASSIST: 15% (screening)
    - Komorbid: 5% (penyesuaian)
    """
    # Normalisasi skor ke skala 0-100
    asam_normalized = asam_pct  # Already 0-100
    
    # Normalisasi DSM-5 (0-11 kriteria)
    dsm5_normalized = (dsm5_count / 11) * 100
    
    # Normalisasi ASSIST (0-39)
    assist_normalized = min(assist_score / 39 * 100, 100)
    
    # Komorbid adjustment
    komorbid_adjustment = 0
    if ada_komorbid:
        if komorbid_severity == "Ringan":
            komorbid_adjustment = 3
        else:  # Berat
            komorbid_adjustment = 8
    
    # Hitung skor komposit
    composite_score = (
        asam_normalized * 0.5 +
        dsm5_normalized * 0.3 +
        assist_normalized * 0.15
    ) + komorbid_adjustment
    
    composite_score = min(composite_score, 100)  # Cap at 100
    
    breakdown = {
        'ASAM Assessment': {
            'score': asam_normalized,
            'weight': 0.5,
            'description': f"Assessment komprehensif 6 dimensi ASAM"
        },
        'DSM-5 Criteria': {
            'score': dsm5_normalized,
            'weight': 0.3,
            'description': f"{dsm5_count}/11 kriteria gangguan penggunaan zat"
        },
        'ASSIST Screening': {
            'score': assist_normalized,
            'weight': 0.15,
            'description': f"Skor screening keterlibatan zat"
        },
        'Komorbid Adjustment': {
            'score': komorbid_adjustment,
            'weight': 0.05,
            'description': f"Penyesuaian untuk kondisi komorbid {komorbid_severity}"
        }
    }
    
    return composite_score, breakdown

def calculate_legal_score(peran: str, barang_bukti: float, jenis_narkotika: str,
                         status_tangkap: str, riwayat_pidana: str, 
                         gramatur_limit: float) -> Tuple[float, Dict]:
    """
    Menghitung skor asesmen hukum berdasarkan Perka BNN No. 11 Tahun 2014
    dan SEMA No. 4 Tahun 2010
    """
    score = 0
    breakdown = {}
    
    # 1. Keterlibatan Jaringan Peredaran (0-40 poin)
    role_mapping = {
        "Pengguna murni (untuk diri sendiri)": 0,
        "Berbagi dengan teman (sharing)": 15,
        "Kurir/pengedar kecil": 25,
        "Pengedar besar/bandar": 40
    }
    network_score = role_mapping[peran]
    breakdown['Keterlibatan Jaringan'] = {
        'skor': network_score,
        'max': 40,
        'detail': peran,
        'legal_basis': "Pasal 103 UU 35/2009 - Hakim dapat memerintahkan rehabilitasi"
    }
    score += network_score
    
    # 2. Barang Bukti vs Gramatur SEMA (0-25 poin)
    if barang_bukti < gramatur_limit:
        evidence_score = 0
        evidence_label = f"Di bawah gramatur SEMA (< {gramatur_limit}g)"
        legal_implication = "Sesuai kriteria rehabilitasi SEMA 4/2010"
    elif barang_bukti <= gramatur_limit * 2:
        evidence_score = 8
        evidence_label = f"Mendekati gramatur SEMA ({gramatur_limit}-{gramatur_limit*2}g)"
        legal_implication = "Perlu pertimbangan tambahan"
    elif barang_bukti <= gramatur_limit * 5:
        evidence_score = 15
        evidence_label = f"Melebihi gramatur SEMA (2-5x)"
        legal_implication = "Indikasi kuat peredaran"
    elif barang_bukti <= gramatur_limit * 20:
        evidence_score = 20
        evidence_label = f"Jauh melebihi gramatur SEMA (5-20x)"
        legal_implication = "Kuat indikasi peredaran"
    else:
        evidence_score = 25
        evidence_label = f"Sangat jauh melebihi gramatur SEMA (>20x)"
        legal_implication = "Sangat kuat indikasi peredaran"
    
    breakdown['Barang Bukti'] = {
        'skor': evidence_score,
        'max': 25,
        'detail': f"{barang_bukti}g - {evidence_label}",
        'legal_basis': f"SEMA No. 4 Tahun 2010 - Gramatur maksimal rehabilitasi",
        'implication': legal_implication
    }
    score += evidence_score
    
    # 3. Status Penangkapan (0-15 poin)
    arrest_mapping = {
        "Sukarela datang untuk asesmen": 0,
        "Operasi targeted (penggerebekan terencana)": 8,
        "Tertangkap tangan saat transaksi": 15
    }
    arrest_score = arrest_mapping[status_tangkap]
    breakdown['Status Penangkapan'] = {
        'skor': arrest_score,
        'max': 15,
        'detail': status_tangkap,
        'legal_basis': "Perka BNN No. 11 Tahun 2014 - Prosedur asesmen"
    }
    score += arrest_score
    
    # 4. Riwayat Pidana (0-20 poin)
    history_mapping = {
        "First offender (pertama kali)": 0,
        "Pernah rehab sebelumnya (relapse)": 10,
        "Residivis kasus narkotika": 20
    }
    history_score = history_mapping[riwayat_pidana]
    breakdown['Riwayat Pidana'] = {
        'skor': history_score,
        'max': 20,
        'detail': riwayat_pidana,
        'legal_basis': "Pasal 54 UU 35/2009 - Kewajiban rehab untuk pecandu"
    }
    score += history_score
    
    return score, breakdown

def apply_tat_decision_rules(skor_medis: float, skor_hukum: float,
                           asam_level: str, dsm5_count: int,
                           barang_bukti: float, gramatur_limit: float,
                           peran: str, fungsi_sosial: str) -> Tuple[Dict, List, str]:
    """
    Menerapkan Decision Rules TAT sesuai Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014
    dan Perka BNN No. 11 Tahun 2014
    
    Kriteria utama:
    1. Apakah memenuhi kriteria pecandu (medis)?
    2. Apakah barang bukti sesuai gramatur SEMA?
    3. Apakah ada indikasi peredaran?
    4. Bagaimana tingkat ketergantungan?
    """
    probabilities = {
        "Rehabilitasi Rawat Jalan": 0,
        "Rehabilitasi Rawat Inap": 0, 
        "Proses Hukum": 0,
        "Proses Hukum + Rehabilitasi": 0
    }
    
    reasoning = []
    primary_recommendation = ""
    
    # Kriteria 1: Cek apakah barang bukti melebihi 20x gramatur SEMA
    if barang_bukti > gramatur_limit * 20:
        probabilities["Proses Hukum"] = 95
        primary_recommendation = "Proses Hukum"
        reasoning.append("✗ Barang bukti sangat jauh melebihi gramatur SEMA (>20x)")
        reasoning.append("✗ Indikasi sangat kuat keterlibatan peredaran")
        reasoning.append("✗ Tidak memenuhi kriteria rehabilitasi berdasarkan SEMA 4/2010")
        return probabilities, reasoning, primary_recommendation
    
    # Kriteria 2: Cek apakah pengedar besar/bandar
    if peran in ["Pengedar besar/bandar"]:
        probabilities["Proses Hukum"] = 90
        primary_recommendation = "Proses Hukum"
        reasoning.append("✗ Status sebagai pengedar besar/bandar")
        reasoning.append("✗ Fokus penegakan hukum untuk perlindungan masyarakat")
        reasoning.append("✗ Sesuai Pasal 111-114 UU 35/2009 tentang peredaran")
        return probabilities, reasoning, primary_recommendation
    
    # Kriteria 3: Cek kriteria rehabilitasi SEMA 4/2010
    if barang_bukti <= gramatur_limit:
        # Memenuhi gramatur SEMA
        if skor_medis <= 40:
            # Kecanduan ringan
            probabilities["Rehabilitasi Rawat Jalan"] = 85
            primary_recommendation = "Rehabilitasi Rawat Jalan"
            reasoning.append("✓ Memenuhi gramatur SEMA untuk rehabilitasi")
            reasoning.append("✓ Tingkat kecanduan ringan (skor medis ≤ 40)")
            reasoning.append("✓ Sesuai kriteria rehabilitasi rawat jalan")
        elif skor_medis <= 70:
            # Kecanduan sedang-berat
            probabilities["Rehabilitasi Rawat Inap"] = 80
            primary_recommendation = "Rehabilitasi Rawat Inap"
            reasoning.append("✓ Memenuhi gramatur SEMA untuk rehabilitasi")
            reasoning.append("✓ Tingkat kecanduan sedang-berat (skor medis 41-70)")
            reasoning.append("✓ Memerlukan pengawasan intensif")
        else:
            # Kecanduan very severe
            probabilities["Rehabilitasi Rawat Inap"] = 75
            probabilities["Proses Hukum + Rehabilitasi"] = 25
            primary_recommendation = "Rehabilitasi Rawat Inap"
            reasoning.append("✓ Memenuhi gramatur SEMA untuk rehabilitasi")
            reasoning.append("! Tingkat kecanduan sangat berat (skor medis > 70)")
            reasoning.append("! Perlu pertimbangan hukum tambahan")
        
        # Tambahkan reasoning berdasarkan fungsi sosial
        if fungsi_sosial == "Masih produktif (sekolah/kerja)":
            reasoning.append("✓ Masih berfungsi sosial dengan baik")
        elif fungsi_sosial == "Mulai terganggu":
            reasoning.append("! Fungsi sosial mulai terganggu")
        else:
            reasoning.append("✗ Fungsi sosial tidak berjalan")
        
        # Tambahkan kriteria DSM-5
        if dsm5_count >= 6:
            reasoning.append("! Memenuhi kriteria gangguan penggunaan zat berat (≥6 kriteria DSM-5)")
        elif dsm5_count >= 4:
            reasoning.append("! Memenuhi kriteria gangguan penggunaan zat sedang (4-5 kriteria DSM-5)")
        
        return probabilities, reasoning, primary_recommendation
    
    # Kriteria 4: Barang bukti di atas gramatur tapi di bawah 5x
    if barang_bukti <= gramatur_limit * 5:
        if skor_medis <= 30 and peran == "Pengguna murni (untuk diri sendiri)":
            probabilities["Rehabilitasi Rawat Jalan"] = 70
            probabilities["Proses Hukum + Rehabilitasi"] = 30
            primary_recommendation = "Rehabilitasi Rawat Jalan"
            reasoning.append("✓ Indikasi kuat sebagai pengguna murni")
            reasoning.append("✓ Tingkat kecanduan ringan")
            reasoning.append("! Barang bukti melebihi gramatur SEMA namun masih wajar untuk penggunaan pribadi")
        elif skor_medis <= 60:
            probabilities["Rehabilitasi Rawat Inap"] = 60
            probabilities["Proses Hukum + Rehabilitasi"] = 40
            primary_recommendation = "Rehabilitasi Rawat Inap"
            reasoning.append("! Barang bukti melebihi gramatur SEMA")
            reasoning.append("✓ Tingkat kecanduan sedang-berat")
            reasoning.append("! Perlu dual intervention - rehabilitasi dan pertimbangan hukum")
        else:
            probabilities["Proses Hukum + Rehabilitasi"] = 75
            probabilities["Proses Hukum"] = 25
            primary_recommendation = "Proses Hukum + Rehabilitasi"
            reasoning.append("! Barang bukti signifikan melebihi gramatur")
            reasoning.append("✓ Tingkat kecanduan berat")
            reasoning.append("! Kasus borderline - perlu evaluasi mendalam Tim TAT")
        return probabilities, reasoning, primary_recommendation
    
    # Kriteria 5: Barang bukti 5-20x gramatur (indikasi peredaran)
    probabilities["Proses Hukum + Rehabilitasi"] = 65
    probabilities["Proses Hukum"] = 35
    primary_recommendation = "Proses Hukum + Rehabilitasi"
    reasoning.append("! Barang bukti 5-20x gramatur SEMA - indikasi kuat peredaran")
    reasoning.append("! Namun masih terdapat aspek kecanduan yang perlu ditangani")
    reasoning.append("✗ Sesuai Pasal 103 UU 35/2009 - Hakim dapat memerintahkan rehabilitasi sambil menjalani pidana")
    reasoning.append("⚠ Kasus kompleks - WAJIB evaluasi mendalam oleh Tim Asesmen Terpadu")
    
    return probabilities, reasoning, primary_recommendation

# =============================================================================
# FUNGSI VISUALISASI ENHANCED
# =============================================================================

def create_asam_radar_chart(asam_scores: Dict[int, int]):
    """Membuat radar chart untuk visualisasi 6 dimensi ASAM"""
    categories = [f"Dimensi {i}: {ASAM_DIMENSIONS[i]['name']}" for i in range(1, 7)]
    values = [asam_scores[i] for i in range(1, 7)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # Close the polygon
        theta=categories + [categories[0]],
        fill='toself',
        name='Severity Score',
        line=dict(color='#1e3a8a'),
        marker=dict(size=8, color='#1e3a8a')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 4],
                tickvals=[0, 1, 2, 3, 4],
                ticktext=['0 (None)', '1 (Low)', '2 (Moderate)', '3 (High)', '4 (Severe)'],
                showline=True,
                showgrid=True
            )
        ),
        title="ASAM 6 Dimensions Assessment",
        height=500,
        showlegend=False
    )
    
    return fig

def create_gauge_chart(score: float, title: str, max_score: float = 100):
    """Membuat gauge chart untuk visualisasi skor"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 24, 'color': '#1e3a8a'}},
        delta={'reference': max_score/2, 'increasing': {'color': '#ef4444'}, 'decreasing': {'color': '#22c55e'}},
        gauge={
            'axis': {'range': [None, max_score], 'tickwidth': 1, 'tickcolor': '#64748b'},
            'bar': {'color': "#1e3a8a"},
            'steps': [
                {'range': [0, max_score/3], 'color': "#22c55e"},    # Low risk
                {'range': [max_score/3, 2*max_score/3], 'color': "#f59e0b"},  # Moderate risk
                {'range': [2*max_score/3, max_score], 'color': "#ef4444"}   # High risk
            ],
            'threshold': {
                'line': {'color': "#dc2626", 'width': 4},
                'thickness': 0.75,
                'value': max_score * 0.8
            }
        }
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_breakdown_chart(breakdown: Dict, title: str):
    """Membuat horizontal bar chart untuk breakdown skor"""
    categories = list(breakdown.keys())
    scores = []
    max_scores = []
    colors = []
    
    for cat in categories:
        scores.append(breakdown[cat]['skor'] if 'skor' in breakdown[cat] else breakdown[cat]['score'])
        max_scores.append(breakdown[cat]['max'] if 'max' in breakdown[cat] else 100)
        
        # Determine color based on severity
        score_val = scores[-1] / max_scores[-1]
        if score_val < 0.33:
            colors.append('#22c55e')  # Green
        elif score_val < 0.67:
            colors.append('#f59e0b')  # Yellow
        else:
            colors.append('#ef4444')  # Red
    
    fig = go.Figure()
    
    # Bar untuk skor aktual
    fig.add_trace(go.Bar(
        y=categories,
        x=scores,
        name='Skor Aktual',
        orientation='h',
        marker=dict(color=colors),
        text=[f"{s:.1f}" for s in scores],
        textposition='auto',
    ))
    
    # Bar untuk sisa dari max score
    fig.add_trace(go.Bar(
        y=categories,
        x=[max_scores[i] - scores[i] for i in range(len(scores))],
        name='Sisa Skor',
        orientation='h',
        marker=dict(color='#94a3b8'),
        showlegend=False
    ))
    
    fig.update_layout(
        title=title,
        barmode='stack',
        height=400 + (len(categories) * 20),
        xaxis_title="Poin",
        yaxis_title="Kategori",
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_probability_chart(probabilities: Dict):
    """Membuat bar chart untuk probabilitas rekomendasi"""
    categories = list(probabilities.keys())
    values = list(probabilities.values())
    
    # Determine colors based on recommendation type
    colors = []
    for cat in categories:
        if "Rawat Jalan" in cat:
            colors.append('#22c55e')  # Green for outpatient
        elif "Rawat Inap" in cat:
            colors.append('#3b82f6')  # Blue for inpatient  
        elif "Hukum + Rehabilitasi" in cat:
            colors.append('#8b5cf6')  # Purple for dual intervention
        else:
            colors.append('#ef4444')  # Red for legal process
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f"{v:.1f}%" for v in values],
            textposition='auto',
            hovertemplate="<b>%{x}</b><br>Probabilitas: %{y:.1f}%<extra></extra>",
        )
    ])
    
    fig.update_layout(
        title="Distribusi Probabilitas Rekomendasi TAT",
        xaxis_title="Jenis Rekomendasi",
        yaxis_title="Probabilitas (%)",
        yaxis=dict(range=[0, 100]),
        height=450,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# =============================================================================
# APLIKASI UTAMA - REVISED SESUAI REGULASI
# =============================================================================

def main():
    # Header dengan branding BNN
    st.markdown('<h1 class="main-header">⚖️ SISTEM PENDUKUNG KEPUTUSAN TIM ASESMEN TERPADU (TAT)</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #4b5563; font-size: 1.1rem; font-weight: 500;">Badan Narkotika Nasional Republik Indonesia</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #64748b;">Tools Bantu Tim Asesmen Terpadu - Penanganan Penyalahguna Narkotika Sesuai Peraturan Perundang-undangan</p>', unsafe_allow_html=True)
    
    # Warning Box - Legal Disclaimer
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ DISCLAIMER HUKUM PENTING:</strong><br>
        1. Sistem ini adalah <strong>ALAT BANTU</strong> untuk Tim Asesmen Terpadu (TAT) sesuai Pasal 8 ayat (2) Perka BNN No. 11 Tahun 2014.<br>
        2. Tim Asesmen Terpadu terdiri dari Tim Dokter dan Tim Hukum yang ditetapkan oleh pimpinan.<br>
        3. Keputusan final tetap berada di tangan <strong>Tim Asesmen Terpadu</strong> dan aparat penegak hukum yang berwenang.<br>
        4. Biaya Pelaksanaan asesmen yang dilakukan oleh Tim Asesmen Terpadu dibebankan pada anggaran Badan Narkotika Nasional.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Info Regulasi Lengkap
    with st.sidebar:
        st.header("📋 DASAR HUKUM LENGKAP")
        
        with st.expander("📖 Undang-Undang Dasar", expanded=True):
            st.markdown("""
            **Regulasi Utama:**
            - **UU No. 35 Tahun 2009** tentang Narkotika
              • Pasal 54: Kewajiban rehab untuk pecandu
              • Pasal 103: Hakim dapat menetapkan rehabilitasi
              • Pasal 127: Penyalahguna dapat direhabilitasi
            - **SEMA No. 4 Tahun 2010** tentang Penanganan Pecandu Narkotika
            """)
        
        with st.expander("🤝 Peraturan Bersama", expanded=True):
            st.markdown("""
            **Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014:**
            - Mahkamah Agung
            - Kejaksaan Agung  
            - Kepolisian RI
            - Kementerian Hukum dan HAM
            - Kementerian Kesehatan
            - Kementerian Sosial
            - Badan Narkotika Nasional
            
            Mengatur tata cara penanganan pecandu narkotika dan korban penyalahgunaan narkotika.
            """)
        
        with st.expander("⚙️ Peraturan BNN", expanded=True):
            st.markdown("""
            **Perka BNN No. 11 Tahun 2014:**
            - Tata Cara Penanganan Tersangka dan/atau Terdakwa Pecandu Narkotika
            - Pembentukan Tim Asesmen Terpadu (TAT)
            - Prosedur asesmen terpadu
            - Kriteria rekomendasi rehabilitasi
            """)
        
        st.markdown("---")
        
        with st.expander("🏥 Instrumen Asesmen Internasional", expanded=True):
            st.markdown("""
            **Standar Asesmen yang Diakui:**
            - **ASAM Criteria** (American Society of Addiction Medicine)
              • 6 Dimensi penilaian komprehensif
              • Level perawatan 0.5-4
            - **DSM-5** (Diagnostic and Statistical Manual of Mental Disorders)
              • 11 Kriteria Gangguan Penggunaan Zat
            - **ASSIST** (WHO Alcohol, Smoking and Substance Involvement Screening Test)
            - **ICD-10** (International Classification of Diseases)
            - **DAST-10** (Drug Abuse Screening Test)
            """)
        
        st.markdown("---")
        st.info("**Versi Sistem:** 2.0.0\n**Update:** Desember 2025\n**Sesuai Peraturan:** Perka BNN No. 11/2014")
        st.warning("🛠️ **Maintenance:** Sistem perlu update berkala sesuai perkembangan hukum dan medis")
    
    # Tab Layout - Enhanced
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Input Data Komprehensif", 
        "📊 Hasil Analisis TAT", 
        "📈 Visualisasi Detail",
        "📋 Laporan & Dokumentasi",
        "ℹ️ Panduan Lengkap"
    ])
    
    # ==========================================================================
    # TAB 1: INPUT DATA KOMPREHENSIF
    # ==========================================================================
    with tab1:
        st.header("📋 Input Data Asesmen Komprehensif TAT")
        
        # Section tabs for better organization
        medical_tab, legal_tab, asam_tab, assist_tab = st.tabs([
            "🏥 Asesmen Medis", 
            "⚖️ Asesmen Hukum", 
            "📐 ASAM 6 Dimensi", 
            "🧪 ASSIST Screening"
        ])
        
        with medical_tab:
            st.subheader("🏥 ASESMEN MEDIS KOMPREHENSIF")
            
            # Informasi Identitas (Opsional - untuk dokumentasi)
            with st.expander("👤 Informasi Identitas (Opsional)", expanded=False):
                col_id1, col_id2 = st.columns(2)
                with col_id1:
                    nama_inisial = st.text_input("Inisial Nama", placeholder="Contoh: AB", key="nama_inisial")
                    usia = st.number_input("Usia", min_value=0, max_value=100, value=25, key="usia")
                with col_id2:
                    jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"], key="jenis_kelamin")
                    pendidikan = st.selectbox("Tingkat Pendidikan", ["SD", "SMP", "SMA", "Diploma", "Sarjana", "Pascasarjana", "Lainnya"], key="pendidikan")
            
            st.markdown("---")
            
            # 1. Hasil Tes Urine/Laboratorium
            st.markdown("### **1️⃣ Hasil Tes Urine/Laboratorium**")
            col_urine1, col_urine2 = st.columns(2)
            
            with col_urine1:
                zat_positif = st.multiselect(
                    "Zat yang terdeteksi POSITIF:",
                    JENIS_NARKOTIKA,
                    default=[],
                    help="Pilih semua zat yang terdeteksi positif dalam tes urine/lab"
                )
                
                # Tampilkan hasil jika ada zat positif
                if zat_positif:
                    st.info(f"**Jumlah zat positif:** {len(zat_positif)}")
                    if len(zat_positif) >= 4:
                        st.warning("⚠️ Polisubstansi (≥4 zat) - indikasi kecanduan berat")
            
            with col_urine2:
                st.markdown("**Kuantifikasi Tes Urine:**")
                kuantifikasi = {}
                for zat in zat_positif:
                    nilai = st.slider(f"Kuantitas {zat.split('(')[0].strip()}", 0, 100, 50, 
                                    help="0=trace, 100=very high concentration", key=f"kuant_{zat}")
                    kuantifikasi[zat] = nilai
            
            st.markdown("---")
            
            # 2. Tingkat Kecanduan (DSM-5)
            st.markdown("### **2️⃣ Kriteria DSM-5 (Gangguan Penggunaan Zat)**")
            st.caption("Berikan tanda centang pada kriteria yang terpenuhi berdasarkan wawancara klinis:")
            
            dsm5_checked = []
            cols_dsm = st.columns(2)
            
            for i, criteria in enumerate(DSM5_CRITERIA, 1):
                col_idx = 0 if i <= 6 else 1
                with cols_dsm[col_idx]:
                    if st.checkbox(f"{i}. {criteria}", key=f"dsm5_{i}"):
                        dsm5_checked.append(criteria)
            
            dsm5_count = len(dsm5_checked)
            
            # Tampilkan interpretasi klinis
            st.markdown("---")
            st.markdown("**📊 Interpretasi DSM-5:**")
            
            if dsm5_count == 0:
                st.success("✅ Tidak ada kriteria terpenuhi - Tidak ada gangguan penggunaan zat")
            elif dsm5_count <= 1:
                st.info(f"ℹ️ **{dsm5_count}/11** - Belum memenuhi kriteria gangguan penggunaan zat")
            elif dsm5_count <= 3:
                st.warning(f"⚠️ **{dsm5_count}/11** - Gangguan Penggunaan **RINGAN** (Mild)")
            elif dsm5_count <= 5:
                st.warning(f"⚠️ **{dsm5_count}/11** - Gangguan Penggunaan **SEDANG** (Moderate)")
            else:
                st.error(f"🚨 **{dsm5_count}/11** - Gangguan Penggunaan **BERAT** (Severe)")
            
            st.markdown("""
            **Catatan Klinis:** 
            - 2-3 kriteria: Gangguan Ringan
            - 4-5 kriteria: Gangguan Sedang  
            - 6+ kriteria: Gangguan Berat
            - Sesuai DSM-5 untuk diagnosis klinis
            """)
            
            st.markdown("---")
            
            # 3. Durasi Penggunaan & Pola
            st.markdown("### **3️⃣ Durasi Penggunaan & Pola Konsumsi**")
            col_dur1, col_dur2 = st.columns(2)
            
            with col_dur1:
                durasi_bulan = st.number_input(
                    "Durasi penggunaan (dalam bulan)",
                    min_value=0,
                    max_value=480,  # 40 tahun
                    value=6,
                    help="Estimasi durasi penggunaan narkotika secara konsisten"
                )
                
                frekuensi = st.selectbox(
                    "Frekuensi penggunaan",
                    ["Jarang (1-3x/bulan)", "Kadang (1-3x/minggu)", "Sering (4-6x/minggu)", "Setiap hari", "Beberapa kali sehari"],
                    help="Frekuensi penggunaan dalam sebulan terakhir"
                )
            
            with col_dur2:
                usia_mulai = st.number_input(
                    "Usia mulai menggunakan",
                    min_value=8,
                    max_value=80,
                    value=18,
                    help="Usia saat pertama kali menggunakan narkotika"
                )
                
                pola_penggunaan = st.selectbox(
                    "Pola penggunaan",
                    ["Eksperimental", "Sosial/rekreasi", "Kebiasaan rutin", "Ketergantungan fisik/psikologis"],
                    help="Pola penggunaan yang dominan"
                )
            
            st.markdown("---")
            
            # 4. Fungsi Sosial/Okupasional
            st.markdown("### **4️⃣ Status Fungsi Sosial/Okupasional**")
            
            col_sos1, col_sos2 = st.columns(2)
            
            with col_sos1:
                fungsi_sosial = st.radio(
                    "Bagaimana fungsi sosial klien saat ini?",
                    [
                        "Masih produktif (sekolah/kerja)",
                        "Mulai terganggu",
                        "Tidak berfungsi sama sekali"
                    ],
                    help="Penilaian terhadap kemampuan menjalankan fungsi sehari-hari"
                )
                
                status_pekerjaan = st.selectbox(
                    "Status pekerjaan saat ini",
                    ["Bekerja tetap", "Bekerja tidak tetap", "Menganggur <6 bulan", "Menganggur >6 bulan", "Pelajar/mahasiswa", "Tidak bekerja"],
                    help="Status pekerjaan terkini"
                )
            
            with col_sos2:
                hubungan_keluarga = st.radio(
                    "Hubungan dengan keluarga",
                    ["Baik - dukungan penuh", "Cukup - dukungan terbatas", "Buruk - konflik tinggi", "Putus hubungan"],
                    help="Kualitas hubungan dengan keluarga"
                )
                
                riwayat_hukum_keluarga = st.checkbox(
                    "Ada riwayat penyalahgunaan narkotika/kriminal dalam keluarga?",
                    help="Riwayat gangguan perilaku dalam keluarga"
                )
            
            st.markdown("---")
            
            # 5. Kondisi Komorbid
            st.markdown("### **5️⃣ Kondisi Komorbid (Gangguan Penyerta)**")
            
            ada_komorbid = st.checkbox(
                "Ada gangguan psikiatrik/medis komorbid?",
                help="Gangguan kesehatan mental atau fisik yang menyertai"
            )
            
            komorbid_jenis = []
            komorbid_severity = "Ringan"
            
            if ada_komorbid:
                col_kom1, col_kom2 = st.columns(2)
                
                with col_kom1:
                    komorbid_jenis = st.multiselect(
                        "Jenis gangguan komorbid:",
                        ["Gangguan Depresi", "Gangguan Cemas", "Gangguan Psikotik", "Gangguan Bipolar", 
                         "Gangguan Kepribadian", "Gangguan Trauma (PTSD)", "Penyakit Jantung", 
                         "Penyakit Hati", "Penyakit Ginjal", "HIV/AIDS", "Diabetes", "Lainnya"],
                        help="Pilih semua gangguan yang relevan"
                    )
                
                with col_kom2:
                    komorbid_severity = st.radio(
                        "Tingkat keparahan komorbid:",
                        ["Ringan", "Sedang", "Berat"],
                        help="Ringan: terkontrol dengan pengobatan\nSedang: gangguan fungsi moderat\nBerat: mengancam jiwa/membutuhkan perawatan intensif"
                    )
                    
                    komorbid_terkontrol = st.checkbox(
                        "Kondisi komorbid terkontrol dengan pengobatan?",
                        help="Apakah gangguan komorbid terkontrol dengan baik?"
                    )
            st.markdown('<div class="legal-box">' + 
                        '<strong>🔍 Catatan Medis:</strong><br>' +
                        '• Asesmen komorbid harus dilakukan oleh dokter spesialis<br>' +
                        '• Dokumentasi medis lengkap diperlukan untuk rekomendasi<br>' +
                        '• Pertimbangkan interaksi obat dalam perencanaan rehabilitasi' +
                        '</div>', unsafe_allow_html=True)
        
        with legal_tab:
            st.subheader("⚖️ ASESMEN HUKUM SESUAI PERATURAN")
            
            # 1. Peran dalam Kasus
            st.markdown("### **1️⃣ Peran Tersangka/Terdakwa**")
            st.caption("Berdasarkan hasil investigasi, keterangan saksi, dan barang bukti")
            
            peran = st.selectbox(
                "Indikasi peran dalam kasus:",
                [
                    "Pengguna murni (untuk diri sendiri)",
                    "Berbagi dengan teman (sharing)",
                    "Kurir/pengedar kecil",
                    "Pengedar besar/bandar"
                ],
                help="Klasifikasi peran berdasarkan bukti dan keterangan"
            )
            
            # Tampilkan implikasi hukum
            if peran == "Pengguna murni (untuk diri sendiri)":
                st.success("✅ Memenuhi kriteria rehabilitasi berdasarkan Pasal 127 UU 35/2009")
            elif peran == "Berbagi dengan teman (sharing)":
                st.warning("⚠️ Perlu pertimbangan tambahan - borderline pengguna/peredar")
            elif peran == "Kurir/pengedar kecil":
                st.error("🚨 Indikasi peredaran - perlu kajian mendalam")
            else:
                st.error("🚨 Pengedar besar/bandar - fokus penegakan hukum")
            
            st.markdown("---")
            
            # 2. Barang Bukti
            st.markdown("### **2️⃣ Barang Bukti Narkotika**")
            st.caption("Sesuai SEMA No. 4 Tahun 2010 tentang Gramatur Maksimal Rehabilitasi")
            
            col_bb1, col_bb2 = st.columns(2)
            
            with col_bb1:
                jenis_narkotika = st.selectbox(
                    "Jenis narkotika yang disita:",
                    list(GRAMATUR_LIMITS.keys()),
                    help="Pilih jenis narkotika sesuai barang bukti"
                )
                gramatur_limit = GRAMATUR_LIMITS[jenis_narkotika]
                st.info(f"📊 **Gramatur SEMA 4/2010:** ≤ {gramatur_limit}g untuk rehabilitasi")
            
            with col_bb2:
                barang_bukti = st.number_input(
                    f"Jumlah barang bukti (gram):",
                    min_value=0.0,
                    max_value=10000.0,  # 10 kg max
                    value=0.5,
                    step=0.1,
                    help=f"Jumlah barang bukti fisik yang disita"
                )
                
                # Perhitungan gramatur ratio
                gramatur_ratio = barang_bukti / gramatur_limit if gramatur_limit > 0 else 0
                
                if barang_bukti < gramatur_limit:
                    st.success(f"✓ **Di bawah gramatur SEMA** ({barang_bukti:.2f}g < {gramatur_limit}g)")
                    st.caption("✅ Memenuhi syarat rehabilitasi berdasarkan SEMA")
                elif barang_bukti <= gramatur_limit * 2:
                    st.warning(f"⚠️ **Mendekati/Sedikit di atas gramatur** ({barang_bukti:.2f}g)")
                    st.caption("🔍 Perlu pertimbangan tambahan Tim TAT")
                elif barang_bukti <= gramatur_limit * 5:
                    st.error(f"🚨 **Di atas gramatur (2-5x)** ({barang_bukti:.2f}g)")
                    st.caption("❗ Indikasi kuat peredaran")
                elif barang_bukti <= gramatur_limit * 20:
                    st.error(f"🚨 **Jauh di atas gramatur (5-20x)** ({barang_bukti:.2f}g)")
                    st.caption("❌ Sangat kuat indikasi peredaran")
                else:
                    st.error(f"🔥 **Sangat jauh di atas gramatur (>20x)** ({barang_bukti:.2f}g)")
                    st.caption("❌ Tidak memenuhi kriteria rehabilitasi")
            
            st.markdown("---")
            
            # 3. Status Penangkapan
            st.markdown("### **3️⃣ Status Penangkapan**")
            st.caption("Modus penangkapan/kedatangan klien sesuai Perka BNN No. 11/2014")
            
            status_tangkap = st.selectbox(
                "Bagaimana klien ditangkap/datang?",
                [
                    "Sukarela datang untuk asesmen",
                    "Operasi targeted (penggerebekan terencana)",
                    "Tertangkap tangan saat transaksi"
                ],
                help="Status penangkapan mempengaruhi penilaian niat baik"
            )
            
            # Tampilkan implikasi
            if status_tangkap == "Sukarela datang untuk asesmen":
                st.success("✅ Niat baik tinggi - mendukung rehabilitasi")
            elif status_tangkap == "Operasi targeted (penggerebekan terencana)":
                st.warning("⚠️ Niat baik sedang - perlu evaluasi lebih lanjut")
            else:
                st.error("🚨 Tertangkap tangan - indikasi kuat peredaran")
            
            st.markdown("---")
            
            # 4. Riwayat Pidana
            st.markdown("### **4️⃣ Riwayat Pidana/Rehabilitasi**")
            st.caption("Riwayat keterlibatan kasus narkotika sebelumnya")
            
            riwayat_pidana = st.radio(
                "Status riwayat kasus sebelumnya:",
                [
                    "First offender (pertama kali)",
                    "Pernah rehab sebelumnya (relapse)",
                    "Residivis kasus narkotika"
                ],
                help="Riwayat sebelumnya mempengaruhi penilaian risiko"
            )
            
            if riwayat_pidana == "Pernah rehab sebelumnya (relapse)":
                st.warning("⚠️ Riwayat relapse - perlu program rehabilitasi lebih intensif")
            elif riwayat_pidana == "Residivis kasus narkotika":
                st.error("🚨 Residivis - prioritas penegakan hukum")
            
            st.markdown("---")
            
            # 5. Keterangan Tambahan Hukum
            st.markdown("### **5️⃣ Keterangan Tambahan**")
            
            col_ket1, col_ket2 = st.columns(2)
            
            with col_ket1:
                kooperatif = st.checkbox(
                    "Tersangka kooperatif dengan proses hukum",
                    help="Kooperatif dengan penyidik, jaksa, hakim"
                )
                
                pengakuan = st.radio(
                    "Status pengakuan:",
                    ["Mengakui semua", "Mengakui sebagian", "Menolak mengakui"],
                    help="Tingkat pengakuan terhadap perbuatan"
                )
            
            with col_ket2:
                saksi_meringankan = st.number_input(
                    "Jumlah saksi meringankan", 
                    min_value=0, max_value=10, value=0,
                    help="Saksi yang memberikan keterangan meringankan"
                )
                
                saksi_memberatkan = st.number_input(
                    "Jumlah saksi memberatkan", 
                    min_value=0, max_value=10, value=0,
                    help="Saksi yang memberikan keterangan memberatkan"
                )
            
            st.markdown('<div class="legal-box">' + 
                        '<strong>⚖️ Dasar Hukum:</strong><br>' +
                        '• Pasal 103 UU 35/2009: Hakim dapat memerintahkan rehabilitasi<br>' +
                        '• SEMA No. 4/2010: Kriteria gramatur rehabilitasi<br>' +
                        '• Perka BNN No. 11/2014: Prosedur asesmen terpadu' +
                        '</div>', unsafe_allow_html=True)
        
        with asam_tab:
            st.subheader("📐 ASAM 6 DIMENSI ASSESSMENT")
            st.caption("American Society of Addiction Medicine (ASAM) Criteria - Standar Internasional")
            st.markdown("""
            **Severity Rating Scale:**
            - **0 = None** - Tidak ada masalah
            - **1 = Mild** - Masalah ringan, terkontrol
            - **2 = Moderate** - Masalah sedang, perlu intervensi
            - **3 = High** - Masalah berat, perlu pengawasan
            - **4 = Severe** - Masalah severe, mengancam jiwa
            """)
            
            asam_scores = {}
            
            # Create sections for each dimension
            for dim_num in range(1, 7):
                dim_info = ASAM_DIMENSIONS[dim_num]
                
                st.markdown(f"### **.Dimension {dim_num}: {dim_info['name']}**")
                st.caption(f"*{dim_info['description']}*")
                
                col_asam1, col_asam2 = st.columns([3, 1])
                
                with col_asam1:
                    severity = st.radio(
                        f"Tingkat Severity Dimensi {dim_num}",
                        list(range(5)),  # 0-4
                        format_func=lambda x: f"{x} - {dim_info['severity_levels'][x]}",
                        horizontal=True,
                        key=f"asam_dim{dim_num}"
                    )
                    
                    # Display clinical notes based on severity
                    if severity >= 3:
                        st.error(f"⚠️ **Severity {severity} (High/Severe)** - Memerlukan intervensi segera")
                    elif severity == 2:
                        st.warning(f"⚠️ **Severity {severity} (Moderate)** - Perlu monitoring intensif")
                    else:
                        st.success(f"✅ **Severity {severity} (None/Low)** - Stabil")
                
                with col_asam2:
                    # Visual indicator
                    if severity == 0:
                        st.markdown('<div class="severity-low" style="padding: 10px; text-align: center;"><strong>STABIL</strong></div>', unsafe_allow_html=True)
                    elif severity == 1:
                        st.markdown('<div class="severity-low" style="padding: 10px; text-align: center;"><strong>LOW</strong></div>', unsafe_allow_html=True)
                    elif severity == 2:
                        st.markdown('<div class="severity-moderate" style="padding: 10px; text-align: center;"><strong>MODERATE</strong></div>', unsafe_allow_html=True)
                    elif severity == 3:
                        st.markdown('<div class="severity-high" style="padding: 10px; text-align: center;"><strong>HIGH</strong></div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="severity-severe" style="padding: 10px; text-align: center;"><strong>SEVERE</strong></div>', unsafe_allow_html=True)
                
                asam_scores[dim_num] = severity
                st.markdown("---")
            
            # Display ASAM summary
            st.markdown("### **📊 Ringkasan ASAM Assessment**")
            avg_severity = sum(asam_scores.values()) / 6
            max_severity = max(asam_scores.values())
            
            st.info(f"""
            **Severity Rata-rata:** {avg_severity:.1f}/4.0
            **Severity Tertinggi:** {max_severity}/4.0 (Dimensi {list(asam_scores.keys())[list(asam_scores.values()).index(max_severity)]})
            **Total Score:** {sum(asam_scores.values())}/24
            """)
            
            # Suggested level of care
            if max_severity == 0:
                st.success("✅ **Level 0.5 - Intervensi Awal**")
            elif max_severity <= 1 and avg_severity <= 1:
                st.success("✅ **Level 1 - Rawat Jalan**")
            elif max_severity <= 2 and avg_severity <= 1.5:
                st.warning("⚠️ **Level 2 - Intensive Outpatient**")
            elif max_severity <= 3:
                st.error("🚨 **Level 3 - Rawat Inap**")
            else:
                st.error("🔥 **Level 4 - Perawatan Intensif**")
            
            st.markdown('<div class="info-box">' + 
                        '<strong>🏥 Catatan Klinis:</strong><br>' +
                        '• ASAM Criteria adalah standar emas untuk penentuan level perawatan<br>' +
                        '• Severity rating harus berdasarkan bukti klinis dan observasi<br>' +
                        '• Perlu direview oleh dokter spesialis untuk keputusan akhir' +
                        '</div>', unsafe_allow_html=True)
        
        with assist_tab:
            st.subheader("🧪 ASSIST SCREENING (WHO)")
            st.caption("Alcohol, Smoking and Substance Involvement Screening Test")
            st.markdown("""
            **Petunjuk Pengisian:**
            Untuk setiap zat, nilai keterlibatan dalam 3 bulan terakhir:
            - **0 = Tidak pernah** menggunakan
            - **1 = Jarang** menggunakan (kurang dari bulanan)
            - **2 = Kadang** menggunakan (bulanan)
            - **3 = Sering** menggunakan (mingguan)
            - **4 = Sangat sering** menggunakan (harian/hamper setiap hari)
            """)
            
            assist_responses = {}
            
            cols_assist = st.columns(2)
            
            for i, (substance, display_name) in enumerate(ASSIST_CATEGORIES.items()):
                col_idx = 0 if i < 4 else 1
                with cols_assist[col_idx]:
                    score = st.radio(
                        f"**{display_name}**",
                        [0, 1, 2, 3, 4],
                        format_func=lambda x: ["0 (Tidak pernah)", "1 (Jarang)", "2 (Kadang)", "3 (Sering)", "4 (Sangat sering)"][x],
                        horizontal=True,
                        key=f"assist_{substance}"
                    )
                    assist_responses[substance] = score
            
            # Calculate ASSIST score
            total_assist = sum(assist_responses.values())
            
            st.markdown("---")
            st.markdown("### **📊 Hasil ASSIST Screening**")
            
            col_assist1, col_assist2 = st.columns(2)
            
            with col_assist1:
                st.metric("Total Skor ASSIST", total_assist, delta=None)
                
                if total_assist <= 3:
                    st.success("✅ **Low Risk** - Minimal intervention")
                elif total_assist <= 26:
                    st.warning("⚠️ **Moderate Risk** - Brief intervention needed")
                else:
                    st.error("🚨 **High Risk** - Intensive intervention required")
            
            with col_assist2:
                # Display risk per substance
                st.markdown("**Risk per Substance:**")
                for substance, score in assist_responses.items():
                    if score >= 3:
                        st.error(f"🚨 {ASSIST_CATEGORIES[substance]}: {score}/4 (High Risk)")
                    elif score >= 2:
                        st.warning(f"⚠️ {ASSIST_CATEGORIES[substance]}: {score}/4 (Moderate Risk)")
                    elif score >= 1:
                        st.info(f"ℹ️ {ASSIST_CATEGORIES[substance]}: {score}/4 (Low Risk)")
                    else:
                        st.success(f"✅ {ASSIST_CATEGORIES[substance]}: {score}/4 (No Risk)")
            
            st.markdown('<div class="info-box">' + 
                        '<strong>🔬 Catatan Screening:</strong><br>' +
                        '• ASSIST adalah instrumen screening validasi internasional dari WHO<br>' +
                        '• Digunakan untuk identifikasi awal tingkat keterlibatan zat<br>' +
                        '• Hasil screening perlu dikonfirmasi dengan asesmen klinis lengkap' +
                        '</div>', unsafe_allow_html=True)
        
        # Tombol Analisis - Enhanced
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        
        with col_btn2:
            analyze_button = st.button(
                "🔍 ANALISIS KOMPREHENSIF TAT",
                use_container_width=True,
                type="primary",
                help="Klik untuk melakukan analisis berdasarkan semua data yang diinput"
            )
            
            if analyze_button:
                if not zat_positif:
                    st.warning("⚠️ Peringatan: Tidak ada zat yang terdeteksi positif. Pastikan hasil tes urine sudah diisi dengan benar.")
                if dsm5_count < 2 and skor_medis_rencana < 30:
                    st.info("ℹ️ Catatan: Skor kecanduan rendah. Pertimbangkan apakah benar-benar memerlukan rehabilitasi intensif.")
    
    # ==========================================================================
    # TAB 2: HASIL ANALISIS TAT
    # ==========================================================================
    with tab2:
        if 'analyze_button' in locals() and analyze_button:
            with st.spinner('🔄 Melakukan analisis komprehensif...'):
                try:
                    # Hitung skor ASAM
                    asam_pct, asam_level, asam_breakdown = calculate_asam_score(asam_scores)
                    
                    # Hitung skor ASSIST
                    assist_total, assist_risk, assist_breakdown = calculate_assist_score(assist_responses)
                    
                    # Hitung skor medis komposit
                    skor_medis, medis_breakdown = calculate_medical_composite(
                        asam_pct, dsm5_count, assist_total, ada_komorbid, komorbid_severity
                    )
                    
                    # Hitung skor hukum
                    skor_hukum, hukum_breakdown = calculate_legal_score(
                        peran, barang_bukti, jenis_narkotika,
                        status_tangkap, riwayat_pidana, gramatur_limit
                    )
                    
                    # Terapkan decision rules TAT
                    probabilities, reasoning, primary_rec = apply_tat_decision_rules(
                        skor_medis, skor_hukum, asam_level, dsm5_count,
                        barang_bukti, gramatur_limit, peran, fungsi_sosial
                    )
                    
                    # Simpan ke session state
                    st.session_state['tat_results'] = {
                        'skor_medis': skor_medis,
                        'skor_hukum': skor_hukum,
                        'asam_pct': asam_pct,
                        'asam_level': asam_level,
                        'asam_breakdown': asam_breakdown,
                        'assist_total': assist_total,
                        'assist_risk': assist_risk,
                        'medis_breakdown': medis_breakdown,
                        'hukum_breakdown': hukum_breakdown,
                        'probabilities': probabilities,
                        'reasoning': reasoning,
                        'primary_rec': primary_rec,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'input_data': {
                            'zat_positif': zat_positif,
                            'dsm5_count': dsm5_count,
                            'durasi_bulan': durasi_bulan,
                            'fungsi_sosial': fungsi_sosial,
                            'ada_komorbid': ada_komorbid,
                            'komorbid_severity': komorbid_severity,
                            'peran': peran,
                            'barang_bukti': barang_bukti,
                            'jenis_narkotika': jenis_narkotika,
                            'status_tangkap': status_tangkap,
                            'riwayat_pidana': riwayat_pidana,
                            'asam_scores': asam_scores,
                            'assist_responses': assist_responses,
                            'nama_inisial': nama_inisial,
                            'usia': usia,
                            'jenis_kelamin': jenis_kelamin
                        }
                    }
                    
                    st.success("✅ Analisis TAT komprehensif selesai!")
                    
                except Exception as e:
                    st.error(f"❌ Error dalam analisis: {str(e)}")
                    st.error("Silakan periksa kembali input data Anda")
        
        # Tampilkan hasil jika sudah ada
        if 'tat_results' in st.session_state:
            results = st.session_state['tat_results']
            
            st.header("📊 HASIL ANALISIS TIM ASESMEN TERPADU (TAT)")
            st.caption(f"**Waktu Analisis:** {results['timestamp']}")
            st.caption(f"**Inisial Klien:** {results['input_data']['nama_inisial'] or 'Tidak disebutkan'}")
            
            # Executive Summary
            st.markdown("### 📋 **RINGKASAN EKSEKUTIF**")
            col_sum1, col_sum2, col_sum3 = st.columns(3)
            
            with col_sum1:
                st.markdown(f"""
                **🏥 Asesmen Medis**  
                Skor: **{results['skor_medis']:.1f}/100**  
                Kategori: **{'BERAT' if results['skor_medis'] > 70 else 'SEDANG' if results['skor_medis'] > 40 else 'RINGAN'}**  
                ASAM Level: **{results['asam_level']}** ({ASAM_LEVELS[results['asam_level']]})
                """)
            
            with col_sum2:
                st.markdown(f"""
                **⚖️ Asesmen Hukum**  
                Skor: **{results['skor_hukum']:.1f}/100**  
                Kategori: **{'TINGGI' if results['skor_hukum'] > 70 else 'SEDANG' if results['skor_hukum'] > 40 else 'RENDAH'}**  
                Gramatur Ratio: **{results['input_data']['barang_bukti'] / GRAMATUR_LIMITS[results['input_data']['jenis_narkotika']]:.1f}x**
                """)
            
            with col_sum3:
                st.markdown(f"""
                **🎯 Rekomendasi Utama**  
                **{results['primary_rec']}**  
                Keyakinan: **{results['probabilities'][results['primary_rec']]:.1f}%**  
                Urgensi: **{'TINGGI' if results['skor_medis'] > 60 or results['skor_hukum'] > 60 else 'SEDANG' if results['skor_medis'] > 40 or results['skor_hukum'] > 40 else 'RENDAH'}**
                """)
            
            st.markdown("---")
            
            # Rekomendasi Utama dengan Visual Enhancement
            st.markdown("### 🎯 **REKOMENDASI UTAMA TIM TAT**")
            primary_prob = results['probabilities'][results['primary_rec']]
            
            if "Rawat Jalan" in results['primary_rec']:
                box_class = "success-box"
                icon = "✅"
                color = "#22c55e"
            elif "Rawat Inap" in results['primary_rec']:
                box_class = "info-box"
                icon = "🏥"
                color = "#3b82f6"
            elif "Hukum + Rehabilitasi" in results['primary_rec']:
                box_class = "legal-box"
                icon = "⚖️"
                color = "#8b5cf6"
            else:
                box_class = "warning-box"
                icon = "⚠️"
                color = "#ef4444"
            
            st.markdown(f"""
            <div class="{box_class}">
                <h2 style="margin: 0; color: {color};">{icon} {results['primary_rec']}</h2>
                <p style="font-size: 1.3rem; margin: 0.5rem 0; font-weight: bold;">
                    <strong>Tingkat Keyakinan: {primary_prob:.1f}%</strong>
                </p>
                <p style="margin: 0.5rem 0; color: #4b5563;">
                    Rekomendasi ini berdasarkan analisis komprehensif 6 dimensi ASAM, kriteria DSM-5, 
                    dan pertimbangan hukum sesuai Peraturan Perundang-undangan.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Detailed Reasoning with Legal Basis
            st.markdown("### 📝 **ALASAN & PERTIMBANGAN HUKUM-MEDIS**")
            
            for reason in results['reasoning']:
                if reason.startswith("✓"):
                    st.success(reason)
                elif reason.startswith("✗"):
                    st.error(reason)
                elif reason.startswith("!"):
                    st.warning(reason)
                elif reason.startswith("•") or reason.startswith("⚠"):
                    st.info(reason)
                else:
                    st.write(reason)
            
            # Add legal basis section
            st.markdown("### ⚖️ **DASAR HUKUM REKOMENDASI**")
            
            legal_basis = {
                "Rehabilitasi Rawat Jalan": [
                    "Pasal 54 UU No. 35 Tahun 2009 - Kewajiban rehab untuk pecandu",
                    "SEMA No. 4 Tahun 2010 - Kriteria gramatur rehabilitasi",
                    "Perka BNN No. 11 Tahun 2014 - Tata cara penanganan tersangka pecandu"
                ],
                "Rehabilitasi Rawat Inap": [
                    "Pasal 103 UU No. 35 Tahun 2009 - Hakim dapat memerintahkan rehabilitasi",
                    "SEMA No. 4 Tahun 2010 - Rehabilitasi untuk pecandu berat",
                    "Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014 - Asesmen terpadu"
                ],
                "Proses Hukum": [
                    "Pasal 111-114 UU No. 35 Tahun 2009 - Ketentuan pidana peredaran",
                    "SEMA No. 4 Tahun 2010 - Batasan gramatur untuk rehabilitasi",
                    "Perka BNN No. 11 Tahun 2014 - Kriteria penolakan rehabilitasi"
                ],
                "Proses Hukum + Rehabilitasi": [
                    "Pasal 103 ayat (2) UU No. 35 Tahun 2009 - Rehabilitasi sambil menjalani pidana",
                    "Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014 - Dual track approach",
                    "SEMA No. 4 Tahun 2010 - Pengecualian untuk kasus borderline"
                ]
            }
            
            current_basis = legal_basis.get(results['primary_rec'], [])
            for item in current_basis:
                st.markdown(f"- **{item}**")
            
            st.markdown("---")
            
            # Probabilities Distribution
            st.markdown("### 📊 **DISTRIBUSI PROBABILITAS REKOMENDASI**")
            
            prob_df = pd.DataFrame({
                'Rekomendasi': list(results['probabilities'].keys()),
                'Probabilitas (%)': [f"{v:.1f}%" for v in results['probabilities'].values()],
                'Status': ['✅ PRIMARY' if k == results['primary_rec'] else '◻️ Alternative' 
                          for k in results['probabilities'].keys()]
            })
            
            st.dataframe(prob_df, use_container_width=True, hide_index=True)
            
            # Visual Chart
            fig_prob = create_probability_chart(results['probabilities'])
            st.plotly_chart(fig_prob, use_container_width=True)
            
            st.markdown("---")
            
            # Clinical Summary
            st.markdown("### 🏥 **RINGKASAN KLINIS**")
            
            col_clin1, col_clin2 = st.columns(2)
            
            with col_clin1:
                st.markdown("**ASAM Assessment:**")
                for dim, data in results['asam_breakdown'].items():
                    severity_level = int(data['score'] / 4 * 100)  # Convert to percentage
                    severity_text = "Severe" if severity_level > 75 else "High" if severity_level > 50 else "Moderate" if severity_level > 25 else "Low"
                    st.markdown(f"- **{data['name']}**: {data['score']}/4 - {severity_text}")
                    st.caption(f"  *{data['severity']}*")
            
            with col_clin2:
                st.markdown("**DSM-5 Assessment:**")
                st.markdown(f"- **Jumlah Kriteria Terpenuhi**: {results['input_data']['dsm5_count']}/11")
                st.markdown(f"- **Tingkat Gangguan**: {'Berat (≥6)' if results['input_data']['dsm5_count'] >= 6 else 'Sedang (4-5)' if results['input_data']['dsm5_count'] >= 4 else 'Ringan (2-3)' if results['input_data']['dsm5_count'] >= 2 else 'Tidak ada gangguan'}")
                
                if results['input_data']['ada_komorbid']:
                    st.markdown(f"**Komorbid**: {results['input_data']['komorbid_severity']} ({', '.join(results['input_data']['komorbid_jenis'] if 'komorbid_jenis' in results['input_data'] else [])})")
            
            st.markdown("---")
            
            # Legal Summary
            st.markdown("### ⚖️ **RINGKASAN HUKUM**")
            
            st.markdown(f"""
            **Peran Tersangka**: {results['input_data']['peran']}  
            **Barang Bukti**: {results['input_data']['barang_bukti']}g {results['input_data']['jenis_narkotika']}  
            **Status Penangkapan**: {results['input_data']['status_tangkap']}  
            **Riwayat**: {results['input_data']['riwayat_pidana']}
            """)
            
            st.markdown("**Pertimbangan Hukum:**")
            for cat, data in results['hukum_breakdown'].items():
                st.markdown(f"- **{cat}**: {data['skor']}/{data['max']} - {data['detail']}")
                if 'implication' in data:
                    st.caption(f"  *{data['implication']}*")
            
            st.markdown("---")
            
            # Final Notes & Legal Disclaimer
            st.markdown("""
            <div class="warning-box">
                <strong>📌 CATATAN PENTING TIM TAT:</strong><br>
                • Rekomendasi ini bersifat <strong>teknis dan informatif</strong> sebagai bahan pertimbangan<br>
                • Keputusan final <strong>WAJIB</strong> melalui <strong>Case Conference Tim Asesmen Terpadu</strong> yang terdiri dari dokter, psikolog, penyidik, jaksa, dan hakim<br>
                • Pertimbangkan faktor kontekstual lain: dukungan keluarga, lingkungan, riwayat trauma, dll<br>
                • Sesuai Pasal 8 Perka BNN No. 11 Tahun 2014, biaya asesmen dibebankan pada anggaran BNN<br>
                • Dokumentasi lengkap asesmen harus disimpan sesuai SOP BNN
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-box">
                <strong>💡 REKOMENDASI TINDAK LANJUT:</strong><br>
                • Lakukan <strong>wawancara mendalam</strong> untuk konfirmasi hasil asesmen<br>
                • Jadwalkan <strong>case conference</strong> dengan seluruh anggota Tim TAT<br>
                • Siapkan <strong>dokumentasi lengkap</strong> untuk proses hukum/rehabilitasi<br>
                • Koordinasi dengan <strong>IPWL/Lembaga Rehabilitasi</strong> terkait ketersediaan tempat<br>
                • Lakukan <strong>monitoring dan evaluasi</strong> pasca keputusan
            </div>
            """, unsafe_allow_html=True)
            
            # Export Data
            st.markdown("---")
            st.markdown("### 💾 **EKSPOR & DOKUMENTASI**")
            
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            
            with col_exp1:
                if st.button("📥 Download Laporan Lengkap (JSON)", use_container_width=True):
                    export_data = {
                        "laporan_tat": {
                            "metadata": {
                                "timestamp": results['timestamp'],
                                "versi_sistem": "2.0.0",
                                "dasar_hukum": [
                                    "UU No. 35 Tahun 2009",
                                    "SEMA No. 4 Tahun 2010", 
                                    "Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014",
                                    "Perka BNN No. 11 Tahun 2014"
                                ]
                            },
                            "hasil_analisis": results
                        }
                    }
                    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="💾 Simpan JSON",
                        data=json_str,
                        file_name=f"TAT_Report_{results['timestamp'].replace(':', '-')}.json",
                        mime="application/json"
                    )
            
            with col_exp2:
                if st.button("📋 Buat Ringkasan PDF", use_container_width=True, disabled=True):
                    st.info("Fitur PDF akan tersedia di versi berikutnya")
            
            with col_exp3:
                if st.button("📤 Kirim ke Sistem BNN", use_container_width=True, disabled=True):
                    st.info("Integrasi dengan sistem BNN akan dikembangkan sesuai SOP")
            
            st.markdown("""
            <div class="legal-box">
                <p style="margin: 0; font-size: 0.9rem; color: #4b5563;">
                    <strong>Catatan Keamanan Data:</strong><br>
                    • Data asesmen bersifat rahasia dan hanya untuk keperluan TAT<br>
                    • Penyimpanan data harus sesuai Peraturan Perlindungan Data Pribadi<br>
                    • Akses data terbatas untuk anggota Tim TAT yang berwenang<br>
                    • Data tidak boleh digunakan untuk keperluan di luar asesmen rehabilitasi
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        else:
            st.info("👈 Silakan isi data komprehensif di tab **Input Data** dan klik tombol **Analisis Komprehensif TAT**")
    
    # ==========================================================================
    # TAB 3: VISUALISASI DETAIL
    # ==========================================================================
    with tab3:
        if 'tat_results' in st.session_state:
            results = st.session_state['tat_results']
            
            st.header("📈 VISUALISASI DETAIL ANALISIS TAT")
            
            # ASAM Radar Chart
            st.markdown("### 📊 **ASAM 6 DIMENSIONS RADAR CHART**")
            asam_scores = {int(k.split()[1]): v['score'] for k, v in results['asam_breakdown'].items()}
            fig_asam = create_asam_radar_chart(asam_scores)
            st.plotly_chart(fig_asam, use_container_width=True)
            
            # Detailed Score Charts
            col_viz1, col_viz2 = st.columns(2)
            
            with col_viz1:
                st.markdown("### **🏥 Skor Asesmen Medis**")
                fig_medis = create_gauge_chart(
                    results['skor_medis'],
                    "Skor Asesmen Medis (0-100)"
                )
                st.plotly_chart(fig_medis, use_container_width=True)
                
                fig_breakdown_medis = create_breakdown_chart(
                    results['medis_breakdown'],
                    "Breakdown Skor Asesmen Medis"
                )
                st.plotly_chart(fig_breakdown_medis, use_container_width=True)
            
            with col_viz2:
                st.markdown("### **⚖️ Skor Asesmen Hukum**")
                fig_hukum = create_gauge_chart(
                    results['skor_hukum'],
                    "Skor Asesmen Hukum (0-100)"
                )
                st.plotly_chart(fig_hukum, use_container_width=True)
                
                fig_breakdown_hukum = create_breakdown_chart(
                    results['hukum_breakdown'],
                    "Breakdown Skor Asesmen Hukum"
                )
                st.plotly_chart(fig_breakdown_hukum, use_container_width=True)
            
            # Additional Visualizations
            st.markdown("### 📈 **ANALISIS KOMPLEMENTER**")
            
            col_add1, col_add2 = st.columns(2)
            
            with col_add1:
                st.markdown("#### **DSM-5 Criteria Fulfillment**")
                dsm5_data = {
                    'Status': ['Terpenuhi', 'Tidak Terpenuhi'],
                    'Jumlah': [results['input_data']['dsm5_count'], 11 - results['input_data']['dsm5_count']]
                }
                fig_dsm5 = px.pie(
                    dsm5_data, 
                    values='Jumlah', 
                    names='Status',
                    title=f"Kriteria DSM-5: {results['input_data']['dsm5_count']}/11 Terpenuhi",
                    color_discrete_sequence=['#ef4444', '#94a3b8']
                )
                st.plotly_chart(fig_dsm5, use_container_width=True)
            
            with col_add2:
                st.markdown("#### **Severity Distribution**")
                severity_data = {
                    'Dimensi': [f"Dim {i}" for i in range(1, 7)],
                    'Severity': [asam_scores[i] for i in range(1, 7)],
                    'Max': [4] * 6
                }
                fig_severity = px.bar(
                    severity_data,
                    x='Dimensi',
                    y='Severity',
                    title="Distribusi Severity ASAM",
                    color='Severity',
                    color_continuous_scale=['#22c55e', '#f59e0b', '#ef4444', '#dc2626'],
                    range_color=[0, 4]
                )
                st.plotly_chart(fig_severity, use_container_width=True)
            
            st.markdown("---")
            
            # Raw Data Tables
            st.markdown("### 📋 **DATA LENGKAP ANALISIS**")
            
            col_table1, col_table2 = st.columns(2)
            
            with col_table1:
                st.markdown("**Detail Asesmen Medis:**")
                medis_detail = []
                for kategori, data in results['medis_breakdown'].items():
                    medis_detail.append({
                        'Parameter': kategori,
                        'Skor': f"{data['score']:.1f}",
                        'Bobot': f"{data['weight']*100:.0f}%",
                        'Detail': data['description']
                    })
                st.dataframe(pd.DataFrame(medis_detail), use_container_width=True, hide_index=True)
            
            with col_table2:
                st.markdown("**Detail Asesmen Hukum:**")
                hukum_detail = []
                for kategori, data in results['hukum_breakdown'].items():
                    hukum_detail.append({
                        'Parameter': kategori,
                        'Skor': f"{data['skor']}/{data['max']}",
                        'Detail': data['detail'],
                        'Dasar Hukum': data.get('legal_basis', 'Tidak disebutkan')
                    })
                st.dataframe(pd.DataFrame(hukum_detail), use_container_width=True, hide_index=True)
            
            # Risk Assessment Matrix
            st.markdown("### 🎯 **MATRIKS PENILAIAN RISIKO**")
            
            risk_matrix = {
                'Kategori': ['Kecanduan', 'Peredaran', 'Relapse', 'Komitmen Rehab'],
                'Level': [
                    'Berat' if results['skor_medis'] > 70 else 'Sedang' if results['skor_medis'] > 40 else 'Ringan',
                    'Tinggi' if results['skor_hukum'] > 70 else 'Sedang' if results['skor_hukum'] > 40 else 'Rendah',
                    'Tinggi' if results['input_data']['dsm5_count'] >= 6 or (results['input_data']['ada_komorbid'] and results['input_data']['komorbid_severity'] == 'Berat') else 'Sedang' if results['input_data']['dsm5_count'] >= 4 else 'Rendah',
                    'Tinggi' if results['input_data']['status_tangkap'] == 'Sukarela datang untuk asesmen' and results['input_data']['fungsi_sosial'] == 'Masih produktif (sekolah/kerja)' else 'Sedang' if results['input_data']['status_tangkap'] == 'Sukarela datang untuk asesmen' else 'Rendah'
                ],
                'Rekomendasi': [
                    'Rawat Inap' if results['skor_medis'] > 60 else 'Rawat Jalan',
                    'Proses Hukum' if results['skor_hukum'] > 60 else 'Rehabilitasi',
                    'Program Intensif + Monitoring' if results['input_data']['dsm5_count'] >= 5 else 'Program Standar',
                    'Rehabilitasi' if results['input_data']['status_tangkap'] == 'Sukarela datang untuk asesmen' else 'Evaluasi Lanjutan'
                ]
            }
            
            st.dataframe(pd.DataFrame(risk_matrix), use_container_width=True, hide_index=True)
        
        else:
            st.info("👈 Silakan lakukan analisis terlebih dahulu di tab **Input Data**")
    
    # ==========================================================================
    # TAB 4: LAPORAN & DOKUMENTASI
    # ==========================================================================
    with tab4:
        st.header("📋 LAPORAN & DOKUMENTASI TAT")
        
        if 'tat_results' in st.session_state:
            results = st.session_state['tat_results']
            
            # Template Laporan Resmi
            st.markdown("### 📄 **TEMPLATE LAPORAN RESMI TAT**")
            
            with st.expander("📋 Template Laporan Lengkap", expanded=True):
                st.markdown(f"""
                **BADAN NARKOTIKA NASIONAL REPUBLIK INDONESIA**  
                **TIM ASESMEN TERPADU (TAT)**  
                **LAPORAN HASIL ASESMEN**
                
                **Tanggal Asesmen:** {results['timestamp']}  
                **Inisial Klien:** {results['input_data']['nama_inisial'] or '[Nama Dirahasiakan]'}  
                **Usia:** {results['input_data']['usia']} tahun  
                **Jenis Kelamin:** {results['input_data']['jenis_kelamin']}
                
                **I. HASIL ASESMEN MEDIS**  
                1. **Tes Urine:** {'Positif ' + ', '.join(results['input_data']['zat_positif']) if results['input_data']['zat_positif'] else 'Negatif'}  
                2. **Kriteria DSM-5:** {results['input_data']['dsm5_count']}/11 kriteria terpenuhi  
                   - Tingkat Gangguan: {'Berat' if results['input_data']['dsm5_count'] >= 6 else 'Sedang' if results['input_data']['dsm5_count'] >= 4 else 'Ringan' if results['input_data']['dsm5_count'] >= 2 else 'Tidak Ada Gangguan'}  
                3. **ASAM Assessment:**  
                   - Level Perawatan: {results['asam_level']} ({ASAM_LEVELS[results['asam_level']]})  
                   - Severity Rata-rata: {results['asam_pct']:.1f}%  
                4. **ASSIST Screening:** Skor {results['assist_total']} - {results['assist_risk']}  
                5. **Komorbid:** {'Ada (' + results['input_data']['komorbid_severity'] + ')' if results['input_data']['ada_komorbid'] else 'Tidak Ada'}
                
                **II. HASIL ASESMEN HUKUM**  
                1. **Peran Tersangka:** {results['input_data']['peran']}  
                2. **Barang Bukti:** {results['input_data']['barang_bukti']}g {results['input_data']['jenis_narkotika']}  
                   - Gramatur SEMA: {GRAMATUR_LIMITS[results['input_data']['jenis_narkotika']]}g  
                   - Rasio: {results['input_data']['barang_bukti'] / GRAMATUR_LIMITS[results['input_data']['jenis_narkotika']]:.1f}x  
                3. **Status Penangkapan:** {results['input_data']['status_tangkap']}  
                4. **Riwayat Pidana:** {results['input_data']['riwayat_pidana']}
                
                **III. REKOMENDASI TAT**  
                **Rekomendasi Utama:** {results['primary_rec']}  
                **Tingkat Keyakinan:** {results['probabilities'][results['primary_rec']]:.1f}%  
                
                **Pertimbangan Utama:**  
                {'\n'.join(['- ' + r for r in results['reasoning']])}
                
                **Dasar Hukum:**  
                - UU No. 35 Tahun 2009 tentang Narkotika  
                - SEMA No. 4 Tahun 2010  
                - Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014  
                - Perka BNN No. 11 Tahun 2014
                
                **IV. CATATAN TIM**  
                1. Rekomendasi ini bersifat teknis dan informatif  
                2. Keputusan final melalui Case Conference TAT  
                3. Diperlukan evaluasi lanjutan sesuai prosedur  
                
                **V. TIM ASESMEN**  
                - Dokter: _________________________  
                - Psikolog: _________________________  
                - Penyidik: _________________________  
                - Jaksa: _________________________  
                - Hakim: _________________________  
                
                **Tarakan, {datetime.now().strftime('%d %B %Y')}**  
                **TIM ASESMEN TERPADU (TAT) BNN**
                """)
            
            # Checklist Dokumentasi
            st.markdown("### ✅ **CHECKLIST DOKUMENTASI WAJIB**")
            
            checklist_items = [
                "Formulir Asesmen Medis lengkap",
                "Hasil Tes Urine/Laboratorium asli",
                "Wawancara Klinis terdokumentasi",
                "Formulir Asesmen Hukum lengkap",
                "Berita Acara Pemeriksaan (BAP)",
                "Fotokopi Barang Bukti",
                "Riwayat Kesehatan lengkap",
                "Surat Pernyataan Kesediaan Rehabilitasi",
                "Dokumen Pendukung (KTP, KK, dll)",
                "Rekaman Wawancara (jika ada)"
            ]
            
            checklist_status = []
            for item in checklist_items:
                status = st.checkbox(item, key=f"check_{item}")
                checklist_status.append((item, status))
            
            completed = sum(1 for _, status in checklist_status if status)
            total = len(checklist_items)
            
            st.progress(completed/total, text=f"Dokumentasi Lengkap: {completed}/{total}")
            
            if completed == total:
                st.success("✅ **Dokumentasi Lengkap** - Siap untuk Case Conference TAT")
            elif completed >= total * 0.8:
                st.warning("⚠️ **Dokumentasi Hampir Lengkap** - Perlu melengkapi beberapa dokumen")
            else:
                st.error("❌ **Dokumentasi Belum Lengkap** - Perlu melengkapi dokumen sebelum Case Conference")
            
            # SOP Case Conference
            st.markdown("### 🤝 **SOP CASE CONFERENCE TAT**")
            
            st.markdown("""
            **Tahapan Case Conference:**
            1. **Persiapan Dokumen** (1-3 hari)
               - Kumpulkan semua dokumentasi wajib
               - Siapkan ringkasan eksekutif
               - Jadwalkan pertemuan dengan seluruh anggota TAT
            
            2. **Pembahasan Awal** (30 menit)
               - Presentasi hasil asesmen medis oleh dokter
               - Presentasi hasil asesmen hukum oleh penyidik/jaksa
               - Diskusi awal temuan kunci
            
            3. **Diskusi Mendalam** (60 menit)
               - Analisis temuan kontroversial
               - Pertimbangan faktor sosial-ekonomi
               - Evaluasi risiko dan manfaat setiap opsi
            
            4. **Pengambilan Keputusan** (30 menit)
               - Voting jika diperlukan
               - Dokumentasi alasan keputusan
               - Penentuan timeline tindak lanjut
            
            5. **Dokumentasi Akhir** (15 menit)
               - Penandatanganan berita acara
               - Penyusunan rekomendasi resmi
               - Distribusi dokumen ke pihak terkait
            
            **Komposisi Tim TAT Minimal:**
            - 1 Dokter Spesialis Jiwa/Adiksi
            - 1 Psikolog Klinis
            - 1 Perwakilan Penyidik (Polri/BNN)
            - 1 Perwakilan Kejaksaan
            - 1 Perwakilan Pengadilan
            - 1 Perwakilan BNN (Koordinator)
            """)
            
            # Timeline & Follow-up
            st.markdown("### ⏰ **TIMELINE & TINDAK LANJUT**")
            
            timeline = {
                'Tahap': ['Asesmen Awal', 'Case Conference', 'Keputusan', 'Eksekusi', 'Monitoring'],
                'Timeline': ['Hari 1', 'Hari 2-3', 'Hari 4', 'Hari 5-7', 'Bulanan'],
                'Penanggung Jawab': ['Tim Asesmen', 'Koordinator TAT', 'Ketua TAT', 'Instansi Terkait', 'Petugas Rehab/Kejaksaan']
            }
            
            st.dataframe(pd.DataFrame(timeline), use_container_width=True, hide_index=True)
            
            st.markdown("""
            **Catatan Penting Timeline:**
            - Sesuai Perka BNN No. 11 Tahun 2014, asesmen harus selesai maksimal 3 hari kerja
            - Case Conference harus dilakukan sebelum sidang pertama
            - Keputusan TAT mengikat secara administratif
            - Monitoring evaluasi minimal 6 bulan pasca rehabilitasi
            """)
        
        else:
            st.info("👈 Silakan lakukan analisis terlebih dahulu untuk melihat template laporan dan dokumentasi")
    
    # ==========================================================================
    # TAB 5: PANDUAN LENGKAP
    # ==========================================================================
    with tab5:
        st.header("ℹ️ PANDUAN LENGKAP SISTEM TAT")
        
        # Tentang Sistem
        st.markdown("""
        ### 📖 **TENTANG SISTEM INI**
        
        Sistem ini merupakan **alat bantu pendukung keputusan** bagi Tim Asesmen Terpadu (TAT) dalam melakukan asesmen terhadap tersangka/terdakwa penyalahguna narkotika. Sistem dirancang sesuai dengan:
        
        - **UU No. 35 Tahun 2009** tentang Narkotika
        - **SEMA No. 4 Tahun 2010** tentang Penanganan Pecandu Narkotika
        - **Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014** tentang Tata Cara Penanganan Pecandu Narkotika
        - **Perka BNN No. 11 Tahun 2014** tentang Tata Cara Penanganan Tersangka dan/atau Terdakwa Pecandu Narkotika
        
        **Bukan pengganti keputusan profesional** - sistem hanya memberikan rekomendasi teknis berdasarkan data yang diinput.
        """)
        
        # Dasar Hukum Lengkap
        with st.expander("⚖️ **DASAR HUKUM LENGKAP**", expanded=True):
            st.markdown("""
            #### **1. UU No. 35 Tahun 2009 tentang Narkotika**
            
            **Pasal 54:**  
            "Pecandu Narkotika dan korban penyalahgunaan narkotika wajib menjalani rehabilitasi medis dan rehabilitasi sosial."
            
            **Pasal 103 ayat (2):**  
            "Hakim dapat memutuskan untuk menempatkan Pecandu Narkotika dan korban penyalahgunaan narkotika ke dalam lembaga rehabilitasi medis dan rehabilitasi sosial."
            
            **Pasal 127 ayat (1):**  
            "Pengguna narkotika yang tidak memenuhi syarat sebagai pecandu sebagaimana dimaksud dalam Pasal 1 angka 19 dapat direhabilitasi."
            
            ---
            
            #### **2. SEMA No. 4 Tahun 2010**
            
            **Poin 3:**  
            "Hakim dapat memerintahkan terdakwa untuk menjalani rehabilitasi apabila memenuhi kriteria:
            a. Terdakwa adalah pecandu narkotika;
            b. Jumlah barang bukti tidak melebihi ketentuan gramatur:
               - Ganja: 5 gram
               - Sabu: 1 gram
               - Heroin: 1,8 gram
               - Kokain: 1,8 gram
               - Ekstasi: 2,4 gram (8 butir @ 0,3 gram)"
            
            ---
            
            #### **3. Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014**
            
            **Pasal 5 ayat (1):**  
            "Penanganan terhadap Pecandu Narkotika dan Korban Penyalahgunaan Narkotika dilakukan melalui mekanisme asesmen terpadu oleh Tim Asesmen Terpadu."
            
            **Pasal 8 ayat (2):**  
            "Tim Asesmen Terpadu sebagaimana dimaksud pada ayat (1) terdiri dari Tim Dokter dan Tim Hukum yang ditetapkan oleh pimpinan masing-masing instansi."
            
            ---
            
            #### **4. Perka BNN No. 11 Tahun 2014**
            
            **Pasal 7:**  
            "Asesmen terpadu dilaksanakan oleh Tim Asesmen Terpadu yang dibentuk oleh Kepala BNN."
            
            **Pasal 8 ayat (2):**  
            "Biaya Pelaksanaan asesmen yang dilakukan oleh Tim Asesmen Terpadu dibebankan pada anggaran Badan Narkotika Nasional."
            """)
        
        # Instrumen Asesmen
        with st.expander("🏥 **INSTRUMEN ASESMEN STANDAR**", expanded=False):
            st.markdown("""
            #### **1. ASAM Criteria (6 Dimensi)**
            
            **Dimensi 1: Intoksikasi Akut dan/atau Potensi Withdrawal**  
            - Gejala fisik penggunaan atau putus zat
            - Risiko komplikasi medis akut
            - Skor 0-4 (None-Severe)
            
            **Dimensi 2: Kondisi dan Komplikasi Biomedis**  
            - Penyakit fisik yang menyertai
            - Kebutuhan perawatan medis
            - Skor 0-4
            
            **Dimensi 3: Kondisi Emosional, Behavioral, Kognitif**  
            - Gangguan mental komorbid
            - Risiko bunuh diri atau membahayakan orang lain
            - Skor 0-4
            
            **Dimensi 4: Kesiapan untuk Berubah**  
            - Motivasi untuk pulih
            - Resistensi terhadap perawatan
            - Skor 0-4
            
            **Dimensi 5: Potensi Relapse, Continued Use, atau Continued Problem**  
            - Riwayat relapse sebelumnya
            - Faktor risiko kambuh
            - Skor 0-4
            
            **Dimensi 6: Lingkungan Pemulihan/Hidup**  
            - Dukungan sosial dan keluarga
            - Lingkungan yang kondusif untuk pemulihan
            - Skor 0-4
            
            **Level Perawatan ASAM:**
            - **Level 0.5**: Intervensi awal
            - **Level 1**: Rawat jalan (outpatient)
            - **Level 2**: Intensive outpatient / Partial hospitalization
            - **Level 3**: Residential / Inpatient
            - **Level 4**: Medically-managed intensive inpatient
            
            ---
            
            #### **2. DSM-5 (11 Kriteria Gangguan Penggunaan Zat)**
            
            **Kriteria Diagnostik:**
            1. Menggunakan dalam jumlah/waktu lebih lama dari yang direncanakan
            2. Keinginan kuat/gagal mengurangi penggunaan
            3. Banyak waktu untuk mendapatkan/menggunakan/pulih dari efek
            4. Craving (keinginan kuat menggunakan)
            5. Gagal memenuhi kewajiban (kerja/sekolah/rumah)
            6. Terus menggunakan meski ada masalah sosial/interpersonal
            7. Mengurangi/meninggalkan aktivitas penting karena penggunaan
            8. Menggunakan dalam situasi berbahaya
            9. Terus menggunakan meski tahu ada masalah fisik/psikologis
            10. Toleransi (butuh dosis lebih tinggi)
            11. Withdrawal/Sakau (gejala putus zat)
            
            **Interpretasi Tingkat Keparahan:**
            - **0-1 kriteria**: Tidak ada gangguan
            - **2-3 kriteria**: Gangguan Penggunaan **RINGAN** (Mild)
            - **4-5 kriteria**: Gangguan Penggunaan **SEDANG** (Moderate)
            - **6+ kriteria**: Gangguan Penggunaan **BERAT** (Severe)
            
            ---
            
            #### **3. ASSIST (WHO)**
            
            **Alcohol, Smoking and Substance Involvement Screening Test**  
            - Skor 0-39
            - **0-3**: Low risk - Minimal intervention
            - **4-26**: Moderate risk - Brief intervention
            - **27+**: High risk - Intensive intervention
            
            ---
            
            #### **4. ICD-10 & DAST-10**
            
            **ICD-10 (International Classification of Diseases):**  
            - F10-F19: Mental and behavioural disorders due to substance use
            
            **DAST-10 (Drug Abuse Screening Test):**  
            - 10 item screening untuk gangguan penggunaan zat
            - Skor 0-10, cut-off ≥3 untuk gangguan sedang-berat
            """)
        
        # SOP Penggunaan Sistem
        with st.expander("📝 **SOP PENGGUNAAN SISTEM**", expanded=True):
            st.markdown("""
            ### **LANGKAH-LANGKAH PENGGUNAAN SISTEM:**
            
            #### **Fase Persiapan (Sebelum Input Data)**
            1. **Kumpulkan Dokumen Wajib:**
               - Hasil tes urine/laboratorium asli
               - Berita Acara Pemeriksaan (BAP)
               - Riwayat kesehatan lengkap
               - Identitas tersangka
               - Barang bukti fisik
            
            2. **Bentuk Tim Asesmen Minimal:**
               - 1 dokter spesialis jiwa/adiksi
               - 1 psikolog klinis
               - 1 perwakilan penegak hukum
               - 1 koordinator dari BNN
            
            3. **Lakukan Wawancara Klinis:**
               - Wawancara tersangka minimal 60 menit
               - Wawancara keluarga jika memungkinkan
               - Observasi perilaku langsung
               - Lakukan tes psikologis dasar
            
            #### **Fase Input Data (Tab 1)**
            1. **Isi Data Identitas (Opsional)**
               - Inisial nama, usia, jenis kelamin
               - Untuk dokumentasi internal
            
            2. **Asesmen Medis (Wajib)**
               - Hasil tes urine: pilih semua zat positif
               - DSM-5: centang kriteria yang terpenuhi berdasarkan wawancara
               - Durasi penggunaan: estimasi dalam bulan
               - Fungsi sosial: pilih status terkini
               - Komorbid: tandai jika ada gangguan penyerta
            
            3. **Asesmen Hukum (Wajib)**
               - Peran tersangka: pilih berdasarkan bukti
               - Barang bukti: input jenis dan jumlah dalam gram
               - Status penangkapan: pilih sesuai fakta
               - Riwayat pidana: pilih status riwayat
            
            4. **ASAM Assessment (Komprehensif)**
               - Isi severity 0-4 untuk setiap dimensi
               - Berikan justifikasi klinis untuk skor tinggi
               - Lakukan cross-check antar dimensi
            
            5. **ASSIST Screening (Pendukung)**
               - Isi frekuensi penggunaan tiap zat
               - Gunakan sebagai validasi tambahan
            
            #### **Fase Analisis (Tab 2)**
            1. **Klik Tombol Analisis**
               - Sistem akan memproses semua data
               - Tunggu hingga muncul hasil komprehensif
            
            2. **Review Hasil Utama**
               - Periksa rekomendasi utama
               - Analisis tingkat keyakinan
               - Review alasan dan pertimbangan
            
            3. **Validasi dengan Profesional**
               - Diskusikan hasil dengan tim dokter
               - Konfirmasi dengan tim hukum
               - Bandingkan dengan pengalaman klinis
            
            #### **Fase Dokumentasi (Tab 4)**
            1. **Lengkapi Checklist Dokumentasi**
               - Pastikan semua dokumen wajib tersedia
               - Verifikasi kelengkapan isian
            
            2. **Siapkan Case Conference**
               - Jadwalkan pertemuan tim TAT
               - Siapkan presentasi hasil analisis
               - Undang semua anggota tim TAT
            
            3. **Ekspor Data**
               - Download laporan dalam format JSON
               - Simpan untuk arsip dan audit
               - Gunakan sebagai bahan presentasi
            
            #### **Fase Keputusan Akhir**
            1. **Lakukan Case Conference**
               - Presentasikan hasil sistem dan justifikasi manual
               - Lakukan diskusi mendalam
               - Ambil keputusan kolektif
            
            2. **Dokumentasikan Keputusan**
               - Buat berita acara hasil TAT
               - Tanda tangani oleh semua anggota
               - Distribusikan ke pihak terkait
            
            3. **Tindak Lanjut**
               - Koordinasi dengan lembaga rehabilitasi
               - Laporkan ke pengadilan/hakim
               - Jadwalkan monitoring evaluasi
            """)
        
        # Keterbatasan & Disclaimer
        with st.expander("⚠️ **KETERBATASAN & DISCLAIMER**", expanded=False):
            st.markdown("""
            ### **KETERBATASAN SISTEM:**
            
            #### **Sistem INI TIDAK DAPAT:**
            ❌ **Menggantikan penilaian klinis profesional**  
            - Dokter, psikolog, dan penegak hukum tetap yang menentukan  
            - Sistem hanya alat bantu analisis data
            
            ❌ **Menangkap nuansa kasus individual**  
            - Setiap kasus memiliki konteks unik  
            - Faktor budaya, keluarga, trauma tidak tercakup penuh
            
            ❌ **Memprediksi hasil rehabilitasi dengan pasti**  
            - Keberhasilan tergantung motivasi individu  
            - Dukungan sosial sangat menentukan
            
            ❌ **Menggantikan keputusan hakim**  
            - Hakim memiliki kewenangan penuh sesuai UU 35/2009  
            - Sistem hanya memberikan rekomendasi teknis
            
            #### **Sistem INI HANYA:**
            ✅ **Alat bantu** untuk strukturisasi data  
            ✅ **Referensi** untuk diskusi tim  
            ✅ **Dokumentasi** sistematis asesmen  
            ✅ **Basis** untuk case conference  
            
            ### **DISCLAIMER HUKUM:**
            
            1. **Tidak Mengikat Secara Hukum**  
               - Output sistem bersifat rekomendatif  
               - Keputusan final ada pada otoritas berwenang
            
            2. **Perlu Validasi Profesional**  
               - Setiap kasus harus direview oleh tim TAT  
               - Pertimbangkan faktor lain yang tidak tercakup
            
            3. **Update Berkala Diperlukan**  
               - Regulasi bisa berubah  
               - Sistem perlu disesuaikan dengan perkembangan hukum
            
            4. **Akurasi Tergantung Input**  
               - "Garbage in, garbage out"  
               - Pastikan data yang diinput akurat dan lengkap
            
            5. **Tidak untuk Screening Massal**  
               - Sistem dirancang untuk asesmen individual mendalam  
               - Bukan untuk screening cepat dalam jumlah besar
            
            6. **Kerahasiaan Data**  
               - Data asesmen bersifat rahasia medis dan hukum  
               - Akses terbatas untuk anggota Tim TAT yang berwenang  
               - Sesuai peraturan perlindungan data pribadi
            """)
        
        # FAQ
        with st.expander("❓ **FREQUENTLY ASKED QUESTIONS (FAQ)**", expanded=False):
            st.markdown("""
            ### **Pertanyaan yang Sering Diajukan:**
            
            **Q1: Apakah sistem ini menggantikan peran Tim TAT?**  
            **A:** **TIDAK**. Sistem ini hanya alat bantu. Keputusan final tetap ada pada Tim Asesmen Terpadu yang terdiri dari profesional kesehatan dan penegak hukum sesuai Pasal 8 Perka BNN No. 11 Tahun 2014.
            
            ---
            
            **Q2: Bagaimana jika hasil sistem berbeda dengan penilaian tim?**  
            **A:** Penilaian tim TAT **SELALU lebih prioritas**. Sistem mungkin tidak menangkap faktor-faktor kontekstual yang penting. Gunakan hasil sistem sebagai salah satu pertimbangan, bukan kebenaran mutlak.
            
            ---
            
            **Q3: Apakah gramatur SEMA 4/2010 masih berlaku?**  
            **A:** Ya, SEMA 4/2010 masih menjadi pedoman utama, namun hakim memiliki kewenangan untuk mempertimbangkan faktor lain sesuai Pasal 103 UU 35/2009. Sistem ini menggunakan gramatur tersebut sebagai referensi awal.
            
            ---
            
            **Q4: Bagaimana jika tersangka positif multiple substances?**  
            **A:** Pilih semua zat yang terdeteksi positif. Sistem akan memberikan skor lebih tinggi untuk polisubstansi (≥4 zat) karena menunjukkan tingkat keparahan yang lebih tinggi dan kompleksitas penanganan.
            
            ---
            
            **Q5: Apa bedanya rawat jalan vs rawat inap?**  
            **A:**  
            - **Rawat Jalan**: Datang ke fasilitas rehab 2-3x/minggu, bisa sambil bekerja/sekolah. Cocok untuk kecanduan ringan-sedang dengan dukungan keluarga kuat. Level ASAM 1.  
            - **Rawat Inap**: Tinggal di fasilitas rehab 24/7. Untuk kecanduan berat, komorbid serius, atau lingkungan rumah tidak mendukung. Level ASAM 3-4.
            
            ---
            
            **Q6: Bagaimana dengan kasus first offender tapi barang bukti besar?**  
            **A:** Sistem akan memberikan skor hukum tinggi karena barang bukti. Meskipun first offender, jika barang bukti jauh melebihi gramatur SEMA (>5x), indikasi peredaran lebih kuat. Tim TAT perlu evaluasi mendalam untuk kasus seperti ini dengan mempertimbangkan motif dan pola penggunaan.
            
            ---
            
            **Q7: Apakah sistem ini bisa digunakan untuk asesmen mandiri?**  
            **A:** Sistem dirancang untuk **profesional** (dokter, psikolog, penyidik, jaksa). Tidak disarankan untuk asesmen mandiri karena perlu keahlian untuk interpretasi hasil dan pengambilan keputusan yang bertanggung jawab.
            
            ---
            
            **Q8: Bagaimana cara update kriteria jika ada perubahan regulasi?**  
            **A:** Sistem rule-based ini mudah diupdate. Cukup modifikasi parameter scoring dan decision rules di kode. Tidak perlu retraining seperti sistem AI/ML. Koordinator BNN provinsi dapat mengkoordinasikan update dengan tim IT pusat.
            
            ---
            
            **Q9: Apakah data yang diinput disimpan?**  
            **A:** Sistem ini **TIDAK menyimpan** data secara otomatis ke server. Data hanya ada di session browser. Anda bisa export hasil analisis dalam format JSON untuk dokumentasi internal sesuai SOP BNN tentang perlindungan data pribadi.
            
            ---
            
            **Q10: Sistem ini bisa digunakan untuk kasus anak/remaja?**  
            **A:** Kriteria umum bisa digunakan, tapi untuk anak/remaja perlu pertimbangan khusus sesuai UU Perlindungan Anak dan sistem peradilan anak. Konsultasikan dengan ahli hukum anak dan psikolog anak. Skor severity mungkin perlu penyesuaian karena perkembangan otak remaja masih berlangsung.
            """)
        
        # Referensi & Kontak
        st.markdown("---")
        st.markdown("""
        ### 📚 **REFERENSI & SUMBER:**
        1. UU No. 35 Tahun 2009 tentang Narkotika
        2. SEMA No. 4 Tahun 2010 tentang Penanganan Pecandu Narkotika
        3. Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014
        4. Perka BNN No. 11 Tahun 2014 tentang Tata Cara Penanganan Tersangka Pecandu
        5. DSM-5 (Diagnostic and Statistical Manual of Mental Disorders, 5th Edition)
        6. ASAM Criteria (American Society of Addiction Medicine, 4th Edition)
        7. WHO ASSIST (Alcohol, Smoking and Substance Involvement Screening Test)
        8. ICD-10 Classification of Mental and Behavioural Disorders
        
        ### 📞 **INFORMASI KONTAK BNN:**
        - **Hotline BNN**: 184 (24 jam)
        - **Website BNN**: https://bnn.go.id
        - **IPWL BNN**: https://ipwl.bnn.go.id (Informasi Pusat Layanan)
        - **Email**: info@bnn.go.id
        - **Media Sosial**: @infobnn (Instagram, Twitter, Facebook)
        
        ---
        
        <div class="info-box">
        <strong>💡 TIPS PENGGUNAAN:</strong><br>
        • Gunakan sistem ini sebagai <strong>bagian dari proses asesmen komprehensif</strong><br>
        • Kombinasikan dengan <strong>wawancara mendalam</strong> dan <strong>observasi klinis</strong><br>
        • Lakukan <strong>cross-check</strong> antara hasil sistem dan penilaian profesional<br>
        • Dokumentasikan semua <strong>justifikasi manual</strong> untuk keputusan akhir<br>
        • Selalu prioritaskan <strong>keselamatan klien</strong> dan <strong>keadilan hukum</strong>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# JALANKAN APLIKASI
# =============================================================================
if __name__ == "__main__":
    main()
