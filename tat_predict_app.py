"""
=================================================================================
SISTEM PENDUKUNG KEPUTUSAN TIM ASESMEN TERPADU (TAT) BNN - VERSI LENGKAP
=================================================================================
VERSI: 3.0.0 - COMPREHENSIVE ASSESSMENT EDITION

Tools bantu untuk proses asesmen narkotika berdasarkan:
- UU No. 35 Tahun 2009 tentang Narkotika
- SEMA No. 4 Tahun 2010 tentang Penanganan Pecandu Narkotika
- Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014
- Perka BNN No. 11 Tahun 2014

Instrumen Asesmen Lengkap:
✓ ASAM 6 Dimensi (American Society of Addiction Medicine)
✓ DSM-5 (11 Kriteria Gangguan Penggunaan Zat)
✓ ASSIST (WHO - Per Substance Scoring)
✓ DAST-10 (Drug Abuse Screening Test)
✓ ICD-10 (International Classification of Diseases)
✓ C-SSRS (Columbia Suicide Severity Rating Scale - Simplified)
✓ ACEs (Adverse Childhood Experiences)
✓ Stages of Change (Motivational Readiness)
✓ GAF (Global Assessment of Functioning)
✓ Lab Test Quantitative Analysis

CATATAN HUKUM PENTING:
1. Sistem ini adalah ALAT BANTU untuk Tim Asesmen Terpadu (TAT)
2. Tim TAT terdiri dari Tim Dokter dan Tim Hukum yang ditetapkan oleh pimpinan
3. Keputusan final tetap ada di tangan Tim Asesmen Terpadu dan aparat penegak hukum
4. Biaya asesmen dibebankan pada anggaran Badan Narkotika Nasional
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
import math

# =============================================================================
# KONFIGURASI HALAMAN
# =============================================================================
st.set_page_config(
    page_title="TAT DSS v3.0 - BNN Comprehensive",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS - Enhanced
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
    .danger-box {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
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
    .instrument-box {
        background-color: #f0fdf4;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0.8rem;
        margin: 0.5rem 0;
    }
    .severity-low { background-color: #dcfce7; border-left: 3px solid #22c55e; padding: 0.5rem; margin: 0.3rem 0; }
    .severity-moderate { background-color: #fef3c7; border-left: 3px solid #f59e0b; padding: 0.5rem; margin: 0.3rem 0; }
    .severity-high { background-color: #fee2e2; border-left: 3px solid #ef4444; padding: 0.5rem; margin: 0.3rem 0; }
    .severity-severe { background-color: #fecaca; border-left: 3px solid #dc2626; padding: 0.5rem; margin: 0.3rem 0; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# KONSTANTA - EXPANDED
# =============================================================================

# Gramatur SEMA 4/2010
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

# Jenis narkotika untuk tes urine dengan cut-off values (ng/mL)
JENIS_NARKOTIKA_CUTOFF = {
    "Metamfetamin (MET/Sabu)": {"cutoff": 1000, "unit": "ng/mL"},
    "Morfin (MOP/Heroin)": {"cutoff": 300, "unit": "ng/mL"},
    "Kokain (COC)": {"cutoff": 300, "unit": "ng/mL"},
    "Amfetamin (AMP)": {"cutoff": 1000, "unit": "ng/mL"},
    "Benzodiazepin (BZO)": {"cutoff": 300, "unit": "ng/mL"},
    "THC (Ganja)": {"cutoff": 50, "unit": "ng/mL"},
    "MDMA (Ekstasi)": {"cutoff": 500, "unit": "ng/mL"},
    "Lainnya": {"cutoff": 0, "unit": "ng/mL"}
}

JENIS_NARKOTIKA = list(JENIS_NARKOTIKA_CUTOFF.keys())

# DSM-5 Criteria (11 kriteria)
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

# ICD-10 Criteria (6 kriteria, butuh 3+ untuk diagnosis dependence)
ICD10_CRITERIA = [
    "Keinginan kuat atau kompulsif untuk menggunakan zat",
    "Kesulitan mengontrol onset, terminasi, atau jumlah penggunaan",
    "Sindrom withdrawal fisiologis saat berhenti/mengurangi",
    "Toleransi (butuh dosis lebih tinggi untuk efek yang sama)",
    "Progresif mengabaikan minat/kesenangan lain karena penggunaan zat",
    "Terus menggunakan meski ada bukti jelas konsekuensi berbahaya"
]

# DAST-10 Questions
DAST10_QUESTIONS = [
    "Apakah Anda menggunakan obat/narkotika selain untuk alasan medis?",
    "Apakah Anda menyalahgunakan lebih dari satu jenis obat/narkotika pada satu waktu?",
    "Apakah Anda DAPAT berhenti menggunakan obat/narkotika kapan saja Anda mau?",  # REVERSE
    "Pernahkah Anda mengalami blackout atau flashback akibat penggunaan obat?",
    "Apakah Anda merasa buruk atau bersalah tentang penggunaan obat Anda?",
    "Apakah pasangan (atau orang tua) Anda mengeluh tentang keterlibatan Anda dengan obat?",
    "Apakah Anda mengabaikan keluarga Anda karena penggunaan obat?",
    "Apakah Anda terlibat dalam aktivitas ilegal untuk mendapatkan obat?",
    "Pernahkah Anda mengalami gejala putus zat (withdrawal) saat berhenti?",
    "Apakah Anda mengalami masalah medis/kesehatan akibat penggunaan obat?"
]

# ASAM 6 Dimensions
ASAM_DIMENSIONS = {
    1: {
        "name": "Intoksikasi Akut dan/atau Potensi Withdrawal",
        "description": "Gejala fisik penggunaan atau putus zat, risiko komplikasi medis akut",
        "severity_levels": {
            0: "Tidak ada gejala intoksikasi atau withdrawal",
            1: "Gejala ringan, stabil secara medis, tidak butuh detox",
            2: "Gejala sedang, perlu monitoring, mungkin perlu medikasi",
            3: "Gejala berat, perlu intervensi medis aktif, risiko komplikasi",
            4: "Gejala severe mengancam jiwa, perlu ICU/emergency care"
        }
    },
    2: {
        "name": "Kondisi Medis Biomedis",
        "description": "Penyakit fisik yang menyertai, kebutuhan perawatan medis",
        "severity_levels": {
            0: "Tidak ada kondisi medis signifikan",
            1: "Kondisi medis ringan, terkontrol dengan pengobatan",
            2: "Kondisi medis sedang, perlu monitoring rutin",
            3: "Kondisi medis berat, mempengaruhi fungsi harian",
            4: "Kondisi medis severe mengancam jiwa, perlu perawatan intensif"
        }
    },
    3: {
        "name": "Kondisi Emosional/Behavioral/Kognitif",
        "description": "Gangguan mental komorbid, risiko bunuh diri/membahayakan orang lain",
        "severity_levels": {
            0: "Tidak ada gangguan psikiatrik, kondisi mental stabil",
            1: "Gangguan ringan, berfungsi baik dengan minimal support",
            2: "Gangguan sedang, gangguan fungsi, perlu terapi",
            3: "Gangguan berat, risiko sedang harm to self/others",
            4: "Gangguan severe, risiko tinggi bunuh diri/kekerasan, perlu pengawasan ketat"
        }
    },
    4: {
        "name": "Kesiapan untuk Berubah",
        "description": "Motivasi untuk pulih, resistensi terhadap perawatan",
        "severity_levels": {
            0: "Sangat termotivasi, komitmen tinggi, action stage",
            1: "Termotivasi, komitmen sedang, preparation stage",
            2: "Ambivalen, perlu motivational enhancement, contemplation stage",
            3: "Resistensi ringan-sedang, precontemplation stage",
            4: "Resistensi berat, menolak perawatan, denial kuat"
        }
    },
    5: {
        "name": "Potensi Relapse/Kontinuasi Penggunaan",
        "description": "Riwayat relapse, faktor risiko kambuh, coping skills",
        "severity_levels": {
            0: "Tidak ada riwayat relapse, dukungan kuat, coping skills bagus",
            1: "Riwayat relapse ringan, faktor protektif cukup",
            2: "Riwayat relapse sedang, faktor risiko moderat",
            3: "Riwayat relapse berat, faktor risiko tinggi, poor coping",
            4: "Riwayat relapse kronis, faktor risiko severe, no coping skills"
        }
    },
    6: {
        "name": "Lingkungan Pemulihan/Hidup",
        "description": "Dukungan sosial, lingkungan kondusif untuk pemulihan",
        "severity_levels": {
            0: "Lingkungan sangat mendukung, bebas narkoba, support system kuat",
            1: "Lingkungan cukup mendukung, minim paparan, ada support",
            2: "Lingkungan netral, perlu dukungan tambahan, paparan sedang",
            3: "Lingkungan kurang mendukung, paparan tinggi, support lemah",
            4: "Lingkungan destruktif, paparan terus-menerus, tidak ada support"
        }
    }
}

# ASAM Level of Care
ASAM_LEVELS = {
    "0.5": "Intervensi Awal (Early Intervention)",
    "1": "Rawat Jalan (Outpatient - 1-2x/minggu)",
    "2": "Intensive Outpatient/Partial Hospitalization (3-5x/minggu)",
    "3": "Residential/Inpatient (Perawatan 24 jam)",
    "4": "Medically-Managed Intensive Inpatient (ICU/Emergency)"
}

# ASSIST Categories
ASSIST_CATEGORIES = {
    "Tobacco": "Rokok/Tembakau",
    "Alcohol": "Alkohol", 
    "Cannabis": "Ganja/Marijuana",
    "Cocaine": "Kokain",
    "Amphetamines": "Sabu/Amfetamin/Stimulan",
    "Sedatives": "Obat Penenang/Benzodiazepin",
    "Opioids": "Opioid/Heroin/Morfin",
    "Hallucinogens": "Halusinogen/LSD/Jamur"
}

# ASSIST Full Questions (8 questions per substance - simplified for system)
ASSIST_QUESTIONS = {
    "Q1": "Seberapa sering menggunakan dalam 3 bulan terakhir?",
    "Q2": "Seberapa kuat keinginan/dorongan untuk menggunakan?",
    "Q3": "Seberapa sering penggunaan menyebabkan masalah (kesehatan/sosial/legal/finansial)?",
    "Q4": "Seberapa sering gagal melakukan yang seharusnya dilakukan karena penggunaan?",
    "Q5": "Apakah teman/keluarga/orang lain mengkhawatirkan penggunaan Anda?",
    "Q6": "Seberapa sering mencoba mengurangi/berhenti tapi gagal?",
    "Q7": "Pernah menggunakan dengan cara injeksi/suntik?"
}

# ACEs (Adverse Childhood Experiences) - 10 categories
ACES_CATEGORIES = [
    "Kekerasan fisik dari orang tua/pengasuh",
    "Kekerasan emosional/verbal dari orang tua/pengasuh",
    "Kekerasan seksual",
    "Penelantaran fisik (tidak tercukupi kebutuhan dasar)",
    "Penelantaran emosional (tidak ada dukungan/kasih sayang)",
    "Perceraian/perpisahan orang tua",
    "Kekerasan domestik terhadap ibu",
    "Penyalahgunaan alkohol/narkotika oleh anggota keluarga",
    "Gangguan mental/bunuh diri dalam keluarga",
    "Anggota keluarga dipenjara"
]

# Stages of Change (Prochaska & DiClemente)
STAGES_OF_CHANGE = {
    "Precontemplation": {
        "description": "Tidak ada niat untuk berubah dalam 6 bulan ke depan",
        "characteristics": "Denial, tidak sadar ada masalah, resistensi",
        "score": 1
    },
    "Contemplation": {
        "description": "Berniat berubah dalam 6 bulan, tapi belum siap sekarang",
        "characteristics": "Ambivalen, sadar ada masalah tapi belum berkomitmen",
        "score": 2
    },
    "Preparation": {
        "description": "Berniat berubah dalam 30 hari, mulai membuat rencana",
        "characteristics": "Mulai berkomitmen, mencari informasi, membuat rencana kecil",
        "score": 3
    },
    "Action": {
        "description": "Sudah melakukan perubahan perilaku nyata < 6 bulan",
        "characteristics": "Aktif mengubah perilaku, butuh dukungan intensif",
        "score": 4
    },
    "Maintenance": {
        "description": "Mempertahankan perubahan > 6 bulan",
        "characteristics": "Fokus mencegah relapse, coping skills kuat",
        "score": 5
    },
    "Relapse": {
        "description": "Kembali ke perilaku lama",
        "characteristics": "Perlu restart dari contemplation/preparation",
        "score": 0
    }
}

# C-SSRS Simplified (Columbia Suicide Severity Rating Scale)
CSSRS_QUESTIONS = {
    "Q1": "Apakah Anda berharap sudah mati atau ingin tidur dan tidak bangun lagi?",
    "Q2": "Apakah Anda memiliki pikiran untuk bunuh diri?",
    "Q3": "Apakah Anda memikirkan bagaimana cara bunuh diri?",
    "Q4": "Apakah Anda berniat untuk melakukan bunuh diri?",
    "Q5": "Apakah Anda sudah mulai membuat rencana atau mempersiapkan cara bunuh diri?"
}

CSSRS_RISK_LEVELS = {
    0: "No Risk - Tidak ada ideasi bunuh diri",
    1: "Low Risk - Wish to be dead, tapi tidak ada pikiran aktif",
    2: "Low-Moderate Risk - Pikiran bunuh diri tanpa metode spesifik",
    3: "Moderate Risk - Pikiran bunuh diri dengan metode, tapi tanpa intent/plan",
    4: "Moderate-High Risk - Intent tanpa plan spesifik",
    5: "High Risk - Intent dengan plan spesifik",
    6: "Imminent Risk - Behavior/preparation untuk bunuh diri"
}

# GAF Score (Global Assessment of Functioning) - ranges
GAF_RANGES = {
    "91-100": "Fungsi superior di semua area kehidupan",
    "81-90": "Gejala minimal, fungsi baik di semua area",
    "71-80": "Gejala sementara dan dapat diatasi, fungsi baik",
    "61-70": "Gejala ringan, beberapa kesulitan tapi masih berfungsi cukup baik",
    "51-60": "Gejala sedang, kesulitan moderat dalam fungsi sosial/okupasional",
    "41-50": "Gejala serius, gangguan berat dalam fungsi sosial/okupasional",
    "31-40": "Gangguan dalam reality testing/komunikasi, atau gangguan mayor dalam fungsi",
    "21-30": "Perilaku sangat dipengaruhi delusi/halusinasi, atau gangguan serius",
    "11-20": "Bahaya menyakiti diri/orang lain, atau gagal menjaga kebersihan minimal",
    "1-10": "Bahaya terus-menerus menyakiti diri/orang lain, atau ketidakmampuan total"
}

# =============================================================================
# FUNGSI PERHITUNGAN SKOR - COMPREHENSIVE & CORRECTED
# =============================================================================

def calculate_asam_score(asam_scores: Dict[int, int]) -> Tuple[float, str, Dict]:
    """
    Menghitung skor ASAM berdasarkan 6 dimensi dengan severity rating 0-4
    Return: (percentage, level_of_care, detailed_breakdown)
    """
    total_score = sum(asam_scores.values())
    max_possible = 6 * 4
    
    avg_severity = total_score / 6
    max_severity = max(asam_scores.values())
    
    # Determine level of care based on ASAM guidelines
    if max_severity == 0 and avg_severity == 0:
        level = "0.5"
    elif max_severity <= 1 and avg_severity <= 1:
        level = "1"
    elif max_severity <= 2 and avg_severity <= 1.5:
        level = "2"
    elif max_severity <= 3 or avg_severity <= 2.5:
        level = "3"
    else:
        level = "4"
    
    severity_percentage = (total_score / max_possible) * 100
    
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

def calculate_dsm5_score(criteria_met: List[bool]) -> Tuple[int, str, str]:
    """
    Calculate DSM-5 severity
    Return: (count, severity_level, diagnosis)
    """
    count = sum(criteria_met)
    
    if count == 0:
        severity = "No Disorder"
        diagnosis = "Tidak memenuhi kriteria gangguan penggunaan zat"
    elif count == 1:
        severity = "Subthreshold"
        diagnosis = "Di bawah ambang batas diagnosis (hanya 1 kriteria)"
    elif count <= 3:
        severity = "Mild"
        diagnosis = "Gangguan Penggunaan Zat RINGAN (Mild Substance Use Disorder)"
    elif count <= 5:
        severity = "Moderate"
        diagnosis = "Gangguan Penggunaan Zat SEDANG (Moderate Substance Use Disorder)"
    else:
        severity = "Severe"
        diagnosis = "Gangguan Penggunaan Zat BERAT (Severe Substance Use Disorder)"
    
    return count, severity, diagnosis

def calculate_icd10_score(criteria_met: List[bool]) -> Tuple[int, bool, str]:
    """
    ICD-10 requires 3+ criteria for dependence syndrome diagnosis
    Return: (count, is_dependent, severity)
    """
    count = sum(criteria_met)
    is_dependent = count >= 3
    
    if not is_dependent:
        if count >= 1:
            severity = "Harmful Use (F1x.1) - belum dependence"
        else:
            severity = "No Diagnosis atau Acute Intoxication only"
    else:
        if count >= 5:
            severity = "Severe Dependence Syndrome (F1x.2)"
        elif count >= 4:
            severity = "Moderate Dependence Syndrome (F1x.2)"
        else:
            severity = "Mild Dependence Syndrome (F1x.2)"
    
    return count, is_dependent, severity

def calculate_dast10_score(responses: List[bool]) -> Tuple[int, str, str]:
    """
    Calculate DAST-10 score
    responses: List of 10 boolean (True = Yes for Q1,2,4-10; False = Yes for Q3 reverse)
    Return: (score, risk_level, recommendation)
    """
    score = 0
    
    # Questions 1, 2, 4-10 are direct scored
    for i in [0, 1, 3, 4, 5, 6, 7, 8, 9]:
        if responses[i]:
            score += 1
    
    # Question 3 is reverse scored ("Can you stop anytime?" - No = problem)
    if not responses[2]:
        score += 1
    
    if score == 0:
        risk_level = "No Problem"
        recommendation = "Tidak ada indikasi masalah penggunaan narkotika"
    elif score <= 2:
        risk_level = "Low Level"
        recommendation = "Level rendah - monitor dan brief intervention"
    elif score <= 5:
        risk_level = "Moderate Level"
        recommendation = "Level sedang - butuh further assessment dan intervention"
    elif score <= 8:
        risk_level = "Substantial Level"
        recommendation = "Level substansial - butuh intensive treatment"
    else:
        risk_level = "Severe Level"
        recommendation = "Level severe - butuh immediate intensive treatment"
    
    return score, risk_level, recommendation

def calculate_assist_score_corrected(assist_responses: Dict[str, Dict[str, int]]) -> Tuple[Dict, str, int]:
    """
    ASSIST scoring yang benar - PER SUBSTANCE
    assist_responses: {substance: {Q1: score, Q2: score, ...}}
    
    Scoring per question:
    Q1 (frequency): Never=0, Once/twice=2, Monthly=3, Weekly=4, Daily=6
    Q2-Q6 (problems): Never=0, <3mo=4, 3mo=5, Monthly=6, Weekly=7, Daily=8
    Q7 (injection): No=0, Yes in past 3mo=2, Yes but not in past 3mo=1
    
    Risk levels PER SUBSTANCE:
    - Low: 0-10
    - Moderate: 11-26
    - High: 27+
    
    Return: (detailed_results_per_substance, highest_risk_overall, highest_score)
    """
    results = {}
    highest_risk = "Low Risk"
    highest_score = 0
    
    for substance, scores in assist_responses.items():
        # Calculate total score for this substance
        total = sum(scores.values())
        
        if total <= 10:
            risk_level = "Low Risk"
            intervention = "No intervention needed - brief advice only"
        elif total <= 26:
            risk_level = "Moderate Risk"
            intervention = "Brief intervention - motivational interviewing, follow-up"
        else:
            risk_level = "High Risk"
            intervention = "Intensive intervention - referral to specialist treatment"
        
        cat_name = ASSIST_CATEGORIES.get(substance, substance)
        results[cat_name] = {
            'score': total,
            'max': 39,
            'risk_level': risk_level,
            'intervention': intervention,
            'detail_scores': scores
        }
        
        # Track highest risk
        if total > highest_score:
            highest_score = total
            highest_risk = risk_level
    
    return results, highest_risk, highest_score

def calculate_aces_score(aces_responses: List[bool]) -> Tuple[int, str, str]:
    """
    Calculate ACEs score (0-10)
    Higher score = more childhood trauma = higher risk
    
    Return: (score, risk_level, interpretation)
    """
    score = sum(aces_responses)
    
    if score == 0:
        risk_level = "No Adverse Experiences"
        interpretation = "Tidak ada riwayat trauma masa kecil yang teridentifikasi"
    elif score <= 3:
        risk_level = "Low-Moderate Risk"
        interpretation = "Beberapa pengalaman traumatis - perlu eksplorasi dampaknya"
    elif score <= 5:
        risk_level = "High Risk"
        interpretation = "Riwayat trauma signifikan - likely mempengaruhi addiction dan mental health"
    else:
        risk_level = "Very High Risk"
        interpretation = "Riwayat trauma berat - sangat likely komorbid PTSD/kompleks trauma"
    
    return score, risk_level, interpretation

def calculate_cssrs_risk(responses: List[bool]) -> Tuple[int, str, str]:
    """
    C-SSRS Simplified Risk Assessment
    Return: (highest_level, risk_category, action_needed)
    """
    highest_level = 0
    for i, response in enumerate(responses):
        if response:
            highest_level = i + 1
    
    if highest_level == 0:
        risk_category = "No Risk"
        action_needed = "Tidak ada ideasi bunuh diri - monitor rutin"
    elif highest_level == 1:
        risk_category = "Low Risk"
        action_needed = "Wish to be dead - increase monitoring, supportive counseling"
    elif highest_level == 2:
        risk_category = "Low-Moderate Risk"
        action_needed = "Suicidal ideation - mental health referral, safety planning"
    elif highest_level == 3:
        risk_category = "Moderate Risk"
        action_needed = "Ideation with method - urgent psychiatric evaluation, safety plan"
    elif highest_level == 4:
        risk_category = "Moderate-High Risk"
        action_needed = "Intent without plan - immediate psychiatric consult, consider hospitalization"
    else:  # 5
        risk_category = "High Risk"
        action_needed = "Intent with plan - IMMEDIATE psychiatric hospitalization, remove means"
    
    return highest_level, risk_category, action_needed

def calculate_gaf_score(selected_range: str) -> Tuple[int, str]:
    """
    GAF Score - clinician rates functioning
    Return: (midpoint_score, interpretation)
    """
    range_map = {
        "91-100": (95, "Superior functioning"),
        "81-90": (85, "Good functioning, minimal symptoms"),
        "71-80": (75, "Transient symptoms, generally good"),
        "61-70": (65, "Mild symptoms, some difficulty"),
        "51-60": (55, "Moderate symptoms, moderate difficulty"),
        "41-50": (45, "Serious symptoms, serious impairment"),
        "31-40": (35, "Major impairment in multiple areas"),
        "21-30": (25, "Behavior considerably influenced by delusions/hallucinations"),
        "11-20": (15, "Some danger of hurting self/others"),
        "1-10": (5, "Persistent danger or persistent inability")
    }
    
    score, interpretation = range_map.get(selected_range, (50, "Moderate"))
    return score, interpretation

def analyze_lab_results(lab_values: Dict[str, float]) -> Dict[str, Dict]:
    """
    Analyze quantitative lab results against cut-off values
    Return: detailed analysis per substance
    """
    results = {}
    
    for substance, value in lab_values.items():
        if substance in JENIS_NARKOTIKA_CUTOFF:
            cutoff_info = JENIS_NARKOTIKA_CUTOFF[substance]
            cutoff = cutoff_info['cutoff']
            unit = cutoff_info['unit']
            
            if cutoff == 0:  # Unknown cutoff
                interpretation = "Cut-off tidak tersedia - konfirmasi dengan lab"
                severity = "Unknown"
            elif value < cutoff * 0.5:
                interpretation = f"Trace/Negatif (< {cutoff*0.5:.0f} {unit})"
                severity = "Trace"
            elif value < cutoff:
                interpretation = f"Di bawah cut-off positif (< {cutoff} {unit})"
                severity = "Below Cutoff"
            elif value < cutoff * 3:
                interpretation = f"Positif (> {cutoff} {unit})"
                severity = "Positive"
            elif value < cutoff * 10:
                interpretation = f"Positif Kuat ({cutoff*3}-{cutoff*10} {unit})"
                severity = "Strong Positive"
            else:
                interpretation = f"Positif Sangat Tinggi (> {cutoff*10} {unit})"
                severity = "Very High"
            
            results[substance] = {
                'value': value,
                'unit': unit,
                'cutoff': cutoff,
                'interpretation': interpretation,
                'severity': severity,
                'ratio': value / cutoff if cutoff > 0 else 0
            }
    
    return results

def calculate_medical_composite_v3(
    asam_pct: float,
    dsm5_count: int,
    icd10_count: int,
    dast10_score: int,
    assist_highest_score: int,
    aces_score: int,
    gaf_score: int,
    cssrs_level: int,
    ada_komorbid: bool,
    komorbid_severity: str
) -> Tuple[float, Dict]:
    """
    Comprehensive medical composite score v3.0
    
    Bobot (Total = 95% + 5% komorbid):
    - ASAM: 35% (gold standard multidimensional)
    - DSM-5: 20% (diagnostic criteria)
    - ICD-10: 15% (international diagnostic)
    - DAST-10: 10% (screening tool)
    - ASSIST: 8% (WHO screening)
    - ACEs: 5% (trauma history)
    - GAF: 4% (functioning)
    - C-SSRS: 3% (suicide risk)
    - Komorbid: +5% adjustment
    """
    # Normalize all scores to 0-100
    asam_normalized = asam_pct  # Already 0-100
    dsm5_normalized = (dsm5_count / 11) * 100
    icd10_normalized = (icd10_count / 6) * 100
    dast10_normalized = (dast10_score / 10) * 100
    assist_normalized = min((assist_highest_score / 39) * 100, 100)
    aces_normalized = (aces_score / 10) * 100
    gaf_normalized = 100 - gaf_score  # Invert GAF (lower GAF = worse = higher score)
    cssrs_normalized = (cssrs_level / 5) * 100
    
    # Komorbid adjustment
    komorbid_adjustment = 0
    if ada_komorbid:
        komorbid_map = {
            "Ringan": 3,
            "Sedang": 5,
            "Berat": 8
        }
        komorbid_adjustment = komorbid_map.get(komorbid_severity, 5)
    
    # Calculate weighted composite
    composite_score = (
        asam_normalized * 0.35 +
        dsm5_normalized * 0.20 +
        icd10_normalized * 0.15 +
        dast10_normalized * 0.10 +
        assist_normalized * 0.08 +
        aces_normalized * 0.05 +
        gaf_normalized * 0.04 +
        cssrs_normalized * 0.03
    ) + komorbid_adjustment
    
    composite_score = min(composite_score, 100)
    
    # Detailed breakdown
    breakdown = {
        'ASAM 6 Dimensi (35%)': {
            'score': asam_normalized * 0.35,
            'weight': 0.35,
            'raw': asam_normalized,
            'description': 'Comprehensive multidimensional assessment'
        },
        'DSM-5 Criteria (20%)': {
            'score': dsm5_normalized * 0.20,
            'weight': 0.20,
            'raw': dsm5_normalized,
            'description': f'{dsm5_count}/11 kriteria terpenuhi'
        },
        'ICD-10 Dependence (15%)': {
            'score': icd10_normalized * 0.15,
            'weight': 0.15,
            'raw': icd10_normalized,
            'description': f'{icd10_count}/6 kriteria terpenuhi'
        },
        'DAST-10 Screening (10%)': {
            'score': dast10_normalized * 0.10,
            'weight': 0.10,
            'raw': dast10_normalized,
            'description': f'Skor {dast10_score}/10'
        },
        'ASSIST Screening (8%)': {
            'score': assist_normalized * 0.08,
            'weight': 0.08,
            'raw': assist_normalized,
            'description': f'Highest score {assist_highest_score}/39'
        },
        'ACEs Trauma (5%)': {
            'score': aces_normalized * 0.05,
            'weight': 0.05,
            'raw': aces_normalized,
            'description': f'{aces_score}/10 adverse experiences'
        },
        'GAF Functioning (4%)': {
            'score': gaf_normalized * 0.04,
            'weight': 0.04,
            'raw': gaf_normalized,
            'description': f'GAF Score {gaf_score}/100 (inverted)'
        },
        'C-SSRS Suicide Risk (3%)': {
            'score': cssrs_normalized * 0.03,
            'weight': 0.03,
            'raw': cssrs_normalized,
            'description': f'Level {cssrs_level}/5 suicide risk'
        },
        'Komorbid Adjustment': {
            'score': komorbid_adjustment,
            'weight': 0.05,
            'raw': komorbid_adjustment,
            'description': f'{komorbid_severity if ada_komorbid else "Tidak ada"}'
        }
    }
    
    return composite_score, breakdown

def calculate_legal_score(
    peran: str, 
    barang_bukti: float, 
    jenis_narkotika: str,
    status_tangkap: str, 
    riwayat_pidana: str, 
    gramatur_limit: float,
    kooperatif: bool,
    pengakuan: str,
    ada_korban: bool
) -> Tuple[float, Dict]:
    """
    Legal assessment score - enhanced v3.0
    
    Komponen:
    - Keterlibatan jaringan: 0-35 poin
    - Barang bukti: 0-25 poin
    - Status penangkapan: 0-15 poin
    - Riwayat pidana: 0-15 poin
    - Kooperatif/pengakuan: 0-7 poin
    - Ada korban: 0-3 poin
    """
    score = 0
    breakdown = {}
    
    # 1. Keterlibatan Jaringan (0-35)
    role_mapping = {
        "Pengguna murni (untuk diri sendiri)": 0,
        "Berbagi dengan teman (sharing)": 12,
        "Kurir/pengedar kecil": 23,
        "Pengedar besar/bandar": 35
    }
    network_score = role_mapping.get(peran, 0)
    breakdown['Keterlibatan Jaringan'] = {
        'skor': network_score,
        'max': 35,
        'detail': peran,
        'legal_basis': "Pasal 111-114 UU 35/2009"
    }
    score += network_score
    
    # 2. Barang Bukti vs Gramatur (0-25)
    if barang_bukti < gramatur_limit:
        evidence_score = 0
        evidence_label = f"Di bawah gramatur SEMA (< {gramatur_limit}g)"
        implication = "Memenuhi syarat rehabilitasi"
    elif barang_bukti <= gramatur_limit * 2:
        evidence_score = 6
        evidence_label = f"Sedikit di atas gramatur (1-2x)"
        implication = "Borderline - perlu pertimbangan"
    elif barang_bukti <= gramatur_limit * 5:
        evidence_score = 12
        evidence_label = f"Melebihi gramatur (2-5x)"
        implication = "Indikasi peredaran"
    elif barang_bukti <= gramatur_limit * 20:
        evidence_score = 20
        evidence_label = f"Jauh melebihi gramatur (5-20x)"
        implication = "Kuat indikasi peredaran"
    else:
        evidence_score = 25
        evidence_label = f"Sangat jauh melebihi (>20x)"
        implication = "Tidak memenuhi syarat rehabilitasi"
    
    breakdown['Barang Bukti'] = {
        'skor': evidence_score,
        'max': 25,
        'detail': f"{barang_bukti}g - {evidence_label}",
        'legal_basis': "SEMA No. 4 Tahun 2010",
        'implication': implication
    }
    score += evidence_score
    
    # 3. Status Penangkapan (0-15)
    arrest_mapping = {
        "Sukarela datang untuk asesmen": 0,
        "Operasi targeted (penggerebekan terencana)": 7,
        "Tertangkap tangan saat transaksi": 15
    }
    arrest_score = arrest_mapping.get(status_tangkap, 7)
    breakdown['Status Penangkapan'] = {
        'skor': arrest_score,
        'max': 15,
        'detail': status_tangkap,
        'legal_basis': "Perka BNN No. 11 Tahun 2014"
    }
    score += arrest_score
    
    # 4. Riwayat Pidana (0-15)
    history_mapping = {
        "First offender (pertama kali)": 0,
        "Pernah rehab sebelumnya (relapse)": 8,
        "Residivis kasus narkotika": 15
    }
    history_score = history_mapping.get(riwayat_pidana, 0)
    breakdown['Riwayat Pidana'] = {
        'skor': history_score,
        'max': 15,
        'detail': riwayat_pidana,
        'legal_basis': "Pasal 127 ayat (2) UU 35/2009"
    }
    score += history_score
    
    # 5. Kooperatif & Pengakuan (0-7)
    coop_score = 0
    if not kooperatif:
        coop_score += 3
    
    pengakuan_map = {
        "Mengakui semua": 0,
        "Mengakui sebagian": 2,
        "Menolak mengakui": 4
    }
    coop_score += pengakuan_map.get(pengakuan, 2)
    
    breakdown['Sikap Kooperatif'] = {
        'skor': coop_score,
        'max': 7,
        'detail': f"{'Tidak kooperatif' if not kooperatif else 'Kooperatif'}, {pengakuan}",
        'legal_basis': "Faktor yang meringankan/memberatkan"
    }
    score += coop_score
    
    # 6. Ada Korban (0-3)
    korban_score = 3 if ada_korban else 0
    breakdown['Dampak Korban'] = {
        'skor': korban_score,
        'max': 3,
        'detail': "Ada korban" if ada_korban else "Tidak ada korban",
        'legal_basis': "Aspek pemberatan pidana"
    }
    score += korban_score
    
    return score, breakdown

def apply_tat_decision_rules_v3(
    skor_medis: float,
    skor_hukum: float,
    asam_level: str,
    dsm5_count: int,
    icd10_dependent: bool,
    dast10_level: str,
    cssrs_level: int,
    barang_bukti: float,
    gramatur_limit: float,
    peran: str,
    fungsi_sosial: str,
    gaf_score: int,
    stage_of_change: str
) -> Tuple[Dict, List, str, Dict]:
    """
    Enhanced TAT Decision Rules v3.0
    Mengintegrasikan semua instrumen asesmen
    
    Return: (probabilities, reasoning, primary_recommendation, clinical_notes)
    """
    probabilities = {
        "Rehabilitasi Rawat Jalan": 0,
        "Rehabilitasi Rawat Inap": 0,
        "Proses Hukum": 0,
        "Proses Hukum + Rehabilitasi": 0
    }
    
    reasoning = []
    primary_recommendation = ""
    clinical_notes = {}
    
    # RED FLAGS - Immediate disqualification from rehabilitation
    red_flags = []
    
    # 1. Barang bukti >20x gramatur
    if barang_bukti > gramatur_limit * 20:
        red_flags.append("Barang bukti >20x gramatur SEMA")
        probabilities["Proses Hukum"] = 95
        probabilities["Proses Hukum + Rehabilitasi"] = 5
        primary_recommendation = "Proses Hukum"
        reasoning.append("✗ Barang bukti sangat jauh melebihi gramatur SEMA (>20x)")
        reasoning.append("✗ Indikasi sangat kuat keterlibatan peredaran sistemik")
        reasoning.append("✗ Tidak memenuhi kriteria rehabilitasi SEMA 4/2010")
        clinical_notes['urgency'] = 'high'
        clinical_notes['law_enforcement_priority'] = True
        return probabilities, reasoning, primary_recommendation, clinical_notes
    
    # 2. Pengedar besar/bandar
    if peran == "Pengedar besar/bandar":
        red_flags.append("Status pengedar besar/bandar")
        probabilities["Proses Hukum"] = 90
        probabilities["Proses Hukum + Rehabilitasi"] = 10
        primary_recommendation = "Proses Hukum"
        reasoning.append("✗ Status sebagai pengedar besar/bandar")
        reasoning.append("✗ Prioritas penegakan hukum untuk perlindungan masyarakat")
        reasoning.append("✗ Pasal 111-114 UU 35/2009 tentang peredaran")
        clinical_notes['urgency'] = 'high'
        clinical_notes['law_enforcement_priority'] = True
        return probabilities, reasoning, primary_recommendation, clinical_notes
    
    # 3. High suicide risk - Medical emergency
    if cssrs_level >= 4:
        red_flags.append("High suicide risk (C-SSRS level 4-5)")
        probabilities["Rehabilitasi Rawat Inap"] = 95
        probabilities["Proses Hukum + Rehabilitasi"] = 5
        primary_recommendation = "Rehabilitasi Rawat Inap"
        reasoning.append("🚨 MEDICAL EMERGENCY - High suicide risk detected")
        reasoning.append("! Immediate psychiatric hospitalization required")
        reasoning.append("! C-SSRS Level {}: {}".format(cssrs_level, "Intent with plan" if cssrs_level == 5 else "Intent without plan"))
        clinical_notes['urgency'] = 'immediate'
        clinical_notes['medical_emergency'] = True
        clinical_notes['suicide_protocol'] = True
        return probabilities, reasoning, primary_recommendation, clinical_notes
    
    # MAIN DECISION TREE - Rehabilitasi criteria met
    if barang_bukti <= gramatur_limit:
        # Gramatur SEMA met
        
        # Consider medical severity
        if skor_medis <= 30:
            # Mild addiction
            if stage_of_change in ["Precontemplation", "Relapse"]:
                probabilities["Rehabilitasi Rawat Jalan"] = 65
                probabilities["Rehabilitasi Rawat Inap"] = 30
                probabilities["Proses Hukum + Rehabilitasi"] = 5
                primary_recommendation = "Rehabilitasi Rawat Jalan"
                reasoning.append("✓ Memenuhi gramatur SEMA")
                reasoning.append("✓ Kecanduan ringan (skor medis ≤30)")
                reasoning.append("! Low motivation - perlu intensive motivational enhancement")
            else:
                probabilities["Rehabilitasi Rawat Jalan"] = 85
                probabilities["Rehabilitasi Rawat Inap"] = 10
                probabilities["Proses Hukum + Rehabilitasi"] = 5
                primary_recommendation = "Rehabilitasi Rawat Jalan"
                reasoning.append("✓ Memenuhi gramatur SEMA")
                reasoning.append("✓ Kecanduan ringan (skor medis ≤30)")
                reasoning.append("✓ Sesuai kriteria rawat jalan")
        
        elif skor_medis <= 60:
            # Moderate addiction
            if gaf_score < 50 or cssrs_level >= 2:
                probabilities["Rehabilitasi Rawat Inap"] = 80
                probabilities["Rehabilitasi Rawat Jalan"] = 15
                probabilities["Proses Hukum + Rehabilitasi"] = 5
                primary_recommendation = "Rehabilitasi Rawat Inap"
                reasoning.append("✓ Memenuhi gramatur SEMA")
                reasoning.append("! Kecanduan sedang (skor medis 31-60)")
                reasoning.append("! GAF < 50 atau suicide risk - butuh intensive care")
            else:
                probabilities["Rehabilitasi Rawat Inap"] = 60
                probabilities["Rehabilitasi Rawat Jalan"] = 35
                probabilities["Proses Hukum + Rehabilitasi"] = 5
                primary_recommendation = "Rehabilitasi Rawat Inap"
                reasoning.append("✓ Memenuhi gramatur SEMA")
                reasoning.append("! Kecanduan sedang (skor medis 31-60)")
                reasoning.append("✓ Perlu pengawasan struktured")
        
        else:
            # Severe addiction (>60)
            if asam_level == "4" or cssrs_level >= 3:
                probabilities["Rehabilitasi Rawat Inap"] = 95
                probabilities["Proses Hukum + Rehabilitasi"] = 5
                primary_recommendation = "Rehabilitasi Rawat Inap"
                reasoning.append("✓ Memenuhi gramatur SEMA")
                reasoning.append("🚨 Kecanduan BERAT (skor medis >60)")
                reasoning.append("! ASAM Level 4 atau moderate suicide risk")
                reasoning.append("! Perlu medically-managed intensive inpatient")
                clinical_notes['urgency'] = 'high'
                clinical_notes['medical_monitoring'] = 'intensive'
            else:
                probabilities["Rehabilitasi Rawat Inap"] = 75
                probabilities["Proses Hukum + Rehabilitasi"] = 20
                probabilities["Rehabilitasi Rawat Jalan"] = 5
                primary_recommendation = "Rehabilitasi Rawat Inap"
                reasoning.append("✓ Memenuhi gramatur SEMA")
                reasoning.append("! Kecanduan berat (skor medis >60)")
                reasoning.append("! Perlu evaluasi komprehensif")
        
        # Add functional assessment
        if fungsi_sosial == "Masih produktif (sekolah/kerja)":
            reasoning.append("✓ Masih berfungsi sosial dengan baik")
        elif fungsi_sosial == "Mulai terganggu":
            reasoning.append("! Fungsi sosial mulai terganggu")
        else:
            reasoning.append("✗ Fungsi sosial tidak berjalan")
        
        # Add diagnostic confirmation
        if dsm5_count >= 6 or icd10_dependent:
            reasoning.append("! Memenuhi kriteria dependence (DSM-5 ≥6 atau ICD-10 ≥3)")
        
        clinical_notes['rehabilitation_eligible'] = True
        clinical_notes['sema_compliant'] = True
        return probabilities, reasoning, primary_recommendation, clinical_notes
    
    # Barang bukti > gramatur tapi ≤5x
    elif barang_bukti <= gramatur_limit * 5:
        if skor_medis <= 30 and peran == "Pengguna murni (untuk diri sendiri)":
            probabilities["Rehabilitasi Rawat Jalan"] = 60
            probabilities["Proses Hukum + Rehabilitasi"] = 35
            probabilities["Rehabilitasi Rawat Inap"] = 5
            primary_recommendation = "Rehabilitasi Rawat Jalan"
            reasoning.append("✓ Indikasi kuat pengguna murni")
            reasoning.append("✓ Kecanduan ringan")
            reasoning.append("! Barang bukti 1-5x gramatur - borderline case")
            reasoning.append("! Perlu justifikasi kuat untuk rehabilitasi")
        elif skor_medis <= 60:
            probabilities["Rehabilitasi Rawat Inap"] = 50
            probabilities["Proses Hukum + Rehabilitasi"] = 45
            probabilities["Rehabilitasi Rawat Jalan"] = 5
            primary_recommendation = "Rehabilitasi Rawat Inap"
            reasoning.append("! Barang bukti melebihi gramatur SEMA")
            reasoning.append("! Kecanduan sedang-berat")
            reasoning.append("! Dual approach - rehabilitasi prioritas tapi pertimbangan hukum")
        else:
            probabilities["Proses Hukum + Rehabilitasi"] = 70
            probabilities["Rehabilitasi Rawat Inap"] = 20
            probabilities["Proses Hukum"] = 10
            primary_recommendation = "Proses Hukum + Rehabilitasi"
            reasoning.append("! Barang bukti signifikan melebihi gramatur")
            reasoning.append("! Kecanduan berat")
            reasoning.append("! Complex case - perlu case conference mendalam")
        
        clinical_notes['borderline_case'] = True
        clinical_notes['tat_review_required'] = True
        return probabilities, reasoning, primary_recommendation, clinical_notes
    
    # Barang bukti 5-20x gramatur
    else:  # 5x < BB ≤ 20x
        if skor_medis > 70 and (dsm5_count >= 6 or icd10_dependent):
            probabilities["Proses Hukum + Rehabilitasi"] = 75
            probabilities["Proses Hukum"] = 20
            probabilities["Rehabilitasi Rawat Inap"] = 5
            primary_recommendation = "Proses Hukum + Rehabilitasi"
            reasoning.append("! Barang bukti 5-20x gramatur - indikasi kuat peredaran")
            reasoning.append("✓ Namun dependence syndrome terkonfirmasi")
            reasoning.append("! Pasal 103 UU 35/2009 - rehabilitasi sambil menjalani pidana")
            reasoning.append("⚠ WAJIB case conference Tim TAT untuk keputusan final")
        else:
            probabilities["Proses Hukum"] = 70
            probabilities["Proses Hukum + Rehabilitasi"] = 25
            probabilities["Rehabilitasi Rawat Inap"] = 5
            primary_recommendation = "Proses Hukum"
            reasoning.append("! Barang bukti 5-20x gramatur SEMA")
            reasoning.append("✗ Indikasi kuat peredaran")
            reasoning.append("! Evidence outweighs rehabilitation consideration")
        
        clinical_notes['complex_case'] = True
        clinical_notes['high_legal_concern'] = True
        clinical_notes['tat_review_required'] = True
        return probabilities, reasoning, primary_recommendation, clinical_notes

# =============================================================================
# FUNGSI VISUALISASI - ENHANCED
# =============================================================================

def create_asam_radar_chart(asam_scores: Dict[int, int]):
    """Radar chart untuk ASAM 6 dimensi"""
    try:
        categories = []
        values = []
        
        for i in range(1, 7):
            dim_name = ASAM_DIMENSIONS[i]['name']
            # Truncate long names
            if len(dim_name) > 40:
                dim_name = dim_name[:37] + "..."
            categories.append(f"D{i}: {dim_name}")
            values.append(asam_scores[i])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name='Severity Score',
            line=dict(color='#1e3a8a', width=2),
            marker=dict(size=8, color='#1e3a8a')
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 4],
                    tickvals=[0, 1, 2, 3, 4],
                    ticktext=['0', '1', '2', '3', '4'],
                    showline=True,
                    showgrid=True,
                    gridcolor='#cbd5e1'
                ),
                angularaxis=dict(
                    gridcolor='#cbd5e1'
                )
            ),
            title={
                'text': "ASAM 6 Dimensions Assessment",
                'x': 0.5,
                'xanchor': 'center'
            },
            height=550,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating ASAM radar chart: {str(e)}")
        return go.Figure()

def create_gauge_chart(score: float, title: str, max_score: float = 100):
    """Gauge chart untuk skor"""
    try:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 20, 'color': '#1e3a8a'}},
            delta={'reference': max_score/2, 'increasing': {'color': '#ef4444'}, 'decreasing': {'color': '#22c55e'}},
            gauge={
                'axis': {'range': [None, max_score], 'tickwidth': 1, 'tickcolor': '#64748b'},
                'bar': {'color': "#1e3a8a", 'thickness': 0.75},
                'steps': [
                    {'range': [0, max_score/3], 'color': "#dcfce7"},
                    {'range': [max_score/3, 2*max_score/3], 'color': "#fef3c7"},
                    {'range': [2*max_score/3, max_score], 'color': "#fee2e2"}
                ],'threshold': {
                    'line': {'color': "#dc2626", 'width': 4},
                    'thickness': 0.75,
                    'value': max_score * 0.75
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
    except Exception as e:
        st.error(f"Error creating gauge chart: {str(e)}")
        return go.Figure()

def create_breakdown_chart(breakdown: Dict, title: str):
    """Horizontal bar chart untuk breakdown skor"""
    try:
        categories = list(breakdown.keys())
        scores = []
        max_scores = []
        colors = []
        
        for cat in categories:
            score_val = breakdown[cat].get('skor') or breakdown[cat].get('score', 0)
            max_val = breakdown[cat].get('max', 100)
            
            scores.append(score_val)
            max_scores.append(max_val)
            
            # Determine color based on severity
            ratio = score_val / max_val if max_val > 0 else 0
            if ratio < 0.33:
                colors.append('#22c55e')  # Green
            elif ratio < 0.67:
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
            name='Sisa',
            orientation='h',
            marker=dict(color='#e2e8f0'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.update_layout(
            title=title,
            barmode='stack',
            height=max(400, len(categories) * 50),
            xaxis_title="Poin",
            yaxis_title="",
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(autorange="reversed")
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating breakdown chart: {str(e)}")
        return go.Figure()

def create_probability_chart(probabilities: Dict):
    """Bar chart untuk probabilitas rekomendasi"""
    try:
        categories = list(probabilities.keys())
        values = list(probabilities.values())
        
        colors = []
        for cat in categories:
            if "Rawat Jalan" in cat:
                colors.append('#22c55e')
            elif "Rawat Inap" in cat:
                colors.append('#3b82f6')
            elif "Hukum + Rehabilitasi" in cat:
                colors.append('#8b5cf6')
            else:
                colors.append('#ef4444')
        
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
    except Exception as e:
        st.error(f"Error creating probability chart: {str(e)}")
        return go.Figure()

def create_comprehensive_dashboard(results: Dict):
    """Create comprehensive visualization dashboard"""
    try:
        # Create subplots
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Medical Score', 'Legal Score', 'Risk Factors', 'Functioning'),
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
                   [{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        # Medical gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=results['skor_medis'],
            title={'text': "Medical"},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#1e3a8a"},
                   'steps': [
                       {'range': [0, 33], 'color': "#dcfce7"},
                       {'range': [33, 67], 'color': "#fef3c7"},
                       {'range': [67, 100], 'color': "#fee2e2"}]},
            domain={'x': [0, 1], 'y': [0, 1]}
        ), row=1, col=1)
        
        # Legal gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=results['skor_hukum'],
            title={'text': "Legal"},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#dc2626"},
                   'steps': [
                       {'range': [0, 33], 'color': "#dcfce7"},
                       {'range': [33, 67], 'color': "#fef3c7"},
                       {'range': [67, 100], 'color': "#fee2e2"}]},
            domain={'x': [0, 1], 'y': [0, 1]}
        ), row=1, col=2)
        
        fig.update_layout(height=700)
        
        return fig
    except Exception as e:
        st.error(f"Error creating dashboard: {str(e)}")
        return go.Figure()

# =============================================================================
# APLIKASI UTAMA - COMPREHENSIVE VERSION
# =============================================================================

def main():
    # Header
    st.markdown('<h1 class="main-header">⚖️ SISTEM PENDUKUNG KEPUTUSAN TAT v3.0 - COMPREHENSIVE</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #4b5563; font-size: 1.1rem; font-weight: 500;">Badan Narkotika Nasional Republik Indonesia</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #64748b;">Asesmen Komprehensif dengan 10+ Instrumen Standar Internasional</p>', unsafe_allow_html=True)
    
    # Legal Disclaimer
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ DISCLAIMER HUKUM PENTING:</strong><br>
        1. Sistem ini adalah <strong>ALAT BANTU</strong> untuk Tim Asesmen Terpadu (TAT)<br>
        2. Keputusan final berada di tangan <strong>Tim TAT dan Aparat Penegak Hukum</strong><br>
        3. Biaya asesmen dibebankan pada anggaran BNN (Perka BNN No. 11/2014)
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 INSTRUMEN ASESMEN v3.0")
        
        st.markdown("""
        <div class="instrument-box">
        <strong>✅ Instrumen Lengkap:</strong><br>
        • ASAM 6 Dimensi<br>
        • DSM-5 (11 Kriteria)<br>
        • ICD-10 Dependence<br>
        • DAST-10<br>
        • ASSIST (WHO)<br>
        • ACEs (Trauma)<br>
        • C-SSRS (Suicide Risk)<br>
        • GAF (Functioning)<br>
        • Stages of Change<br>
        • Lab Quantitative
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📖 Dasar Hukum", expanded=False):
            st.markdown("""
            - UU No. 35 Tahun 2009
            - SEMA No. 4 Tahun 2010
            - Peraturan Bersama 7 Instansi
            - Perka BNN No. 11 Tahun 2014
            """)
        
        st.markdown("---")
        st.info("**Versi:** 3.0.0 COMPREHENSIVE\n**Update:** Desember 2025")
    
    # Main Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Input Data",
        "📊 Hasil Analisis",
        "📈 Visualisasi",
        "📋 Laporan",
        "🔬 Lab Results",
        "ℹ️ Panduan"
    ])
    
    # ==========================================================================
    # TAB 1: INPUT DATA KOMPREHENSIF
    # ==========================================================================
    with tab1:
        st.header("📋 INPUT DATA ASESMEN KOMPREHENSIF")
        
        # Create sub-tabs for better organization
        input_tabs = st.tabs([
            "👤 Identitas",
            "🏥 Medical (1/3)",
            "🏥 Medical (2/3)",
            "🏥 Medical (3/3)",
            "⚖️ Legal",
            "🧪 Lab Tests"
        ])
        
        # ==================== SUB-TAB: IDENTITAS ====================
        with input_tabs[0]:
            st.subheader("👤 INFORMASI IDENTITAS")
            
            col_id1, col_id2, col_id3 = st.columns(3)
            
            with col_id1:
                nama_inisial = st.text_input("Inisial Nama", placeholder="Contoh: AB", key="nama_inisial")
                usia = st.number_input("Usia", min_value=12, max_value=100, value=25, key="usia")
                jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"], key="jenis_kelamin")
            
            with col_id2:
                pendidikan = st.selectbox("Pendidikan Terakhir", 
                    ["SD", "SMP", "SMA", "Diploma", "Sarjana", "Pascasarjana", "Lainnya"], 
                    key="pendidikan")
                status_pernikahan = st.selectbox("Status Pernikahan",
                    ["Belum menikah", "Menikah", "Cerai", "Janda/Duda"],
                    key="status_nikah")
                jumlah_tanggungan = st.number_input("Jumlah Tanggungan", min_value=0, max_value=20, value=0)
            
            with col_id3:
                pekerjaan = st.selectbox("Pekerjaan",
                    ["Pelajar/Mahasiswa", "Pegawai Swasta", "PNS/TNI/Polri", "Wiraswasta", 
                     "Buruh", "Tidak Bekerja", "Lainnya"],
                    key="pekerjaan")
                penghasilan = st.selectbox("Penghasilan per Bulan",
                    ["< Rp 1 juta", "Rp 1-3 juta", "Rp 3-5 juta", "Rp 5-10 juta", "> Rp 10 juta", "Tidak ada"],
                    key="penghasilan")
                alamat_kota = st.text_input("Kota/Kabupaten", placeholder="Contoh: Jakarta")
        
        # ==================== SUB-TAB: MEDICAL 1 - BASIC & DSM-5 & ICD-10 ====================
        with input_tabs[1]:
            st.subheader("🏥 ASESMEN MEDIS (1/3): BASIC & DIAGNOSTIC CRITERIA")
            
            # Basic Medical Info
            st.markdown("### **1️⃣ Informasi Medis Dasar**")
            col_med1, col_med2 = st.columns(2)
            
            with col_med1:
                durasi_bulan = st.number_input("Durasi penggunaan (bulan)", 
                    min_value=0, max_value=600, value=12,
                    help="Berapa lama menggunakan narkotika")
                
                usia_mulai = st.number_input("Usia pertama kali menggunakan",
                    min_value=8, max_value=80, value=18)
                
                frekuensi = st.selectbox("Frekuensi penggunaan",
                    ["Jarang (1-3x/bulan)", "Kadang (1-3x/minggu)", 
                     "Sering (4-6x/minggu)", "Setiap hari", "Beberapa kali sehari"])
            
            with col_med2:
                pola_penggunaan = st.selectbox("Pola penggunaan",
                    ["Eksperimental", "Sosial/rekreasi", "Kebiasaan rutin", 
                     "Ketergantungan fisik/psikologis"])
                
                rute_penggunaan = st.multiselect("Cara penggunaan",
                    ["Oral (diminum)", "Dihirup (snorting)", "Dihisap (smoking)", 
                     "Injeksi/suntik", "Lainnya"],
                    default=["Dihisap (smoking)"])
                
                zat_utama = st.selectbox("Zat utama yang digunakan",
                    ["Ganja", "Sabu/Metamfetamin", "Heroin/Opioid", "Kokain", 
                     "Ekstasi/MDMA", "Benzodiazepin", "Alkohol", "Polisubstansi"])
            
            st.markdown("---")
            
            # DSM-5 Criteria
            st.markdown("### **2️⃣ DSM-5: 11 Kriteria Gangguan Penggunaan Zat**")
            st.caption("Centang kriteria yang terpenuhi dalam 12 bulan terakhir:")
            
            dsm5_responses = []
            cols_dsm = st.columns(2)
            
            for i, criteria in enumerate(DSM5_CRITERIA, 1):
                col_idx = 0 if i <= 6 else 1
                with cols_dsm[col_idx]:
                    checked = st.checkbox(f"{i}. {criteria}", key=f"dsm5_{i}")
                    dsm5_responses.append(checked)
            
            dsm5_count, dsm5_severity, dsm5_diagnosis = calculate_dsm5_score(dsm5_responses)
            
            st.markdown("---")
            st.markdown("**📊 Hasil DSM-5:**")
            
            if dsm5_count == 0:
                st.success(f"✅ {dsm5_diagnosis}")
            elif dsm5_count <= 1:
                st.info(f"ℹ️ {dsm5_count}/11 kriteria - {dsm5_diagnosis}")
            elif dsm5_severity == "Mild":
                st.warning(f"⚠️ {dsm5_count}/11 kriteria - {dsm5_diagnosis}")
            elif dsm5_severity == "Moderate":
                st.warning(f"⚠️ {dsm5_count}/11 kriteria - {dsm5_diagnosis}")
            else:
                st.error(f"🚨 {dsm5_count}/11 kriteria - {dsm5_diagnosis}")
            
            st.markdown("---")
            
            # ICD-10 Criteria
            st.markdown("### **3️⃣ ICD-10: Dependence Syndrome (F1x.2)**")
            st.caption("Centang kriteria yang terpenuhi dalam 12 bulan terakhir (butuh ≥3 untuk diagnosis dependence):")
            
            icd10_responses = []
            for i, criteria in enumerate(ICD10_CRITERIA, 1):
                checked = st.checkbox(f"{i}. {criteria}", key=f"icd10_{i}")
                icd10_responses.append(checked)
            
            icd10_count, icd10_dependent, icd10_severity = calculate_icd10_score(icd10_responses)
            
            st.markdown("---")
            st.markdown("**📊 Hasil ICD-10:**")
            
            if icd10_dependent:
                st.error(f"🚨 {icd10_count}/6 kriteria - **{icd10_severity}**")
                st.caption("✓ Memenuhi kriteria Dependence Syndrome")
            else:
                if icd10_count >= 1:
                    st.warning(f"⚠️ {icd10_count}/6 kriteria - {icd10_severity}")
                else:
                    st.success(f"✅ {icd10_count}/6 kriteria - {icd10_severity}")
        
        # ==================== SUB-TAB: MEDICAL 2 - DAST-10 & ASSIST ====================
        with input_tabs[2]:
            st.subheader("🏥 ASESMEN MEDIS (2/3): SCREENING TOOLS")
            
            # DAST-10
            st.markdown("### **4️⃣ DAST-10: Drug Abuse Screening Test**")
            st.caption("Jawab YA/TIDAK untuk 10 pertanyaan berikut:")
            
            dast10_responses = []
            for i, question in enumerate(DAST10_QUESTIONS, 1):
                reverse_note = " **(REVERSE SCORED)**" if i == 3 else ""
                response = st.radio(
                    f"**{i}.** {question}{reverse_note}",
                    ["TIDAK", "YA"],
                    horizontal=True,
                    key=f"dast10_{i}"
                )
                dast10_responses.append(response == "YA")
            
            dast10_score, dast10_level, dast10_rec = calculate_dast10_score(dast10_responses)
            
            st.markdown("---")
            st.markdown("**📊 Hasil DAST-10:**")
            
            col_dast1, col_dast2 = st.columns(2)
            with col_dast1:
                st.metric("Skor DAST-10", f"{dast10_score}/10")
            with col_dast2:
                if dast10_score == 0:
                    st.success(f"✅ {dast10_level}")
                elif dast10_score <= 2:
                    st.info(f"ℹ️ {dast10_level}")
                elif dast10_score <= 5:
                    st.warning(f"⚠️ {dast10_level}")
                else:
                    st.error(f"🚨 {dast10_level}")
            
            st.caption(f"**Rekomendasi:** {dast10_rec}")
            
            st.markdown("---")
            
            # ASSIST Simplified
            st.markdown("### **5️⃣ ASSIST: WHO Screening (Simplified)**")
            st.caption("Untuk setiap zat, nilai keterlibatan dalam 3 bulan terakhir:")
            st.caption("Dalam implementasi lengkap, ASSIST memiliki 7-8 pertanyaan per zat. Ini versi simplified.")
            
            assist_responses = {}
            
            for substance, display_name in ASSIST_CATEGORIES.items():
                st.markdown(f"**{display_name}:**")
                
                col_a1, col_a2, col_a3 = st.columns(3)
                
                with col_a1:
                    q1 = st.radio(
                        "Q1: Frekuensi 3 bulan terakhir",
                        [0, 2, 3, 4, 6],
                        format_func=lambda x: {0:"Never", 2:"Once/Twice", 3:"Monthly", 4:"Weekly", 6:"Daily"}[x],
                        horizontal=False,
                        key=f"assist_{substance}_q1"
                    )
                
                with col_a2:
                    q2 = st.radio(
                        "Q2: Keinginan/dorongan kuat",
                        [0, 3, 4, 5, 6],
                        format_func=lambda x: {0:"Never", 3:"Rarely", 4:"Sometimes", 5:"Often", 6:"Always"}[x],
                        horizontal=False,
                        key=f"assist_{substance}_q2"
                    )
                
                with col_a3:
                    q3 = st.radio(
                        "Q3: Menyebabkan masalah",
                        [0, 4, 5, 6, 7],
                        format_func=lambda x: {0:"Never", 4:"Rarely", 5:"Sometimes", 6:"Often", 7:"Always"}[x],
                        horizontal=False,
                        key=f"assist_{substance}_q3"
                    )
                
                # Simplified: hanya 3 pertanyaan, dalam full version ada 7-8
                assist_responses[substance] = {
                    'Q1': q1,
                    'Q2': q2,
                    'Q3': q3
                }
                
                st.markdown("---")
            
            # Calculate ASSIST
            assist_results, assist_highest_risk, assist_highest_score = calculate_assist_score_corrected(assist_responses)
            
            st.markdown("**📊 Hasil ASSIST per Zat:**")
            for substance, result in assist_results.items():
                risk_level = result['risk_level']
                score = result['score']
                
                if risk_level == "Low Risk":
                    st.success(f"✅ {substance}: {score}/39 - {risk_level}")
                elif risk_level == "Moderate Risk":
                    st.warning(f"⚠️ {substance}: {score}/39 - {risk_level}")
                else:
                    st.error(f"🚨 {substance}: {score}/39 - {risk_level}")
            
            st.info(f"**Overall Highest Risk:** {assist_highest_risk} (Skor tertinggi: {assist_highest_score}/39)")
        
        # ==================== SUB-TAB: MEDICAL 3 - ASAM, ACEs, C-SSRS, GAF ====================
        with input_tabs[3]:
            st.subheader("🏥 ASESMEN MEDIS (3/3): ASAM, TRAUMA, SUICIDE RISK, FUNCTIONING")
            
            # ASAM 6 Dimensions
            st.markdown("### **6️⃣ ASAM 6 DIMENSI ASSESSMENT**")
            st.caption("American Society of Addiction Medicine Criteria - Severity 0-4")
            
            asam_scores = {}
            
            for dim_num in range(1, 7):
                dim_info = ASAM_DIMENSIONS[dim_num]
                
                with st.expander(f"📐 Dimensi {dim_num}: {dim_info['name']}", expanded=False):
                    st.caption(f"*{dim_info['description']}*")
                    
                    severity = st.radio(
                        f"Tingkat Severity",
                        list(range(5)),
                        format_func=lambda x: f"{x} - {dim_info['severity_levels'][x]}",
                        key=f"asam_dim{dim_num}"
                    )
                    
                    asam_scores[dim_num] = severity
                    
                    if severity >= 3:
                        st.error(f"⚠️ Severity {severity} - Perlu intervensi intensif")
                    elif severity == 2:
                        st.warning(f"⚠️ Severity {severity} - Perlu monitoring")
                    else:
                        st.success(f"✅ Severity {severity} - Stabil/Ringan")
            
            # Calculate ASAM
            asam_pct, asam_level, asam_breakdown = calculate_asam_score(asam_scores)
            
            st.markdown("**📊 Ringkasan ASAM:**")
            col_asam1, col_asam2, col_asam3 = st.columns(3)
            
            with col_asam1:
                st.metric("Severity Average", f"{asam_pct:.1f}%")
            with col_asam2:
                st.metric("Level of Care", asam_level)
            with col_asam3:
                st.info(ASAM_LEVELS[asam_level])
            
            st.markdown("---")
            
            # ACEs
            st.markdown("### **7️⃣ ACEs: Adverse Childhood Experiences**")
            st.caption("Riwayat trauma masa kecil (≤18 tahun). Centang yang dialami:")
            
            aces_responses = []
            cols_aces = st.columns(2)
            
            for i, experience in enumerate(ACES_CATEGORIES):
                col_idx = 0 if i < 5 else 1
                with cols_aces[col_idx]:
                    checked = st.checkbox(f"{i+1}. {experience}", key=f"aces_{i+1}")
                    aces_responses.append(checked)
            
            aces_score, aces_risk, aces_interp = calculate_aces_score(aces_responses)
            
            st.markdown("**📊 Hasil ACEs:**")
            if aces_score == 0:
                st.success(f"✅ ACEs Score: {aces_score}/10 - {aces_risk}")
            elif aces_score <= 3:
                st.info(f"ℹ️ ACEs Score: {aces_score}/10 - {aces_risk}")
            elif aces_score <= 5:
                st.warning(f"⚠️ ACEs Score: {aces_score}/10 - {aces_risk}")
            else:
                st.error(f"🚨 ACEs Score: {aces_score}/10 - {aces_risk}")
            
            st.caption(aces_interp)
            
            st.markdown("---")
            
            # C-SSRS Simplified
            st.markdown("### **8️⃣ C-SSRS: Columbia Suicide Severity Rating Scale (Simplified)**")
            st.caption("⚠️ PENTING: Skrining risiko bunuh diri")
            
            cssrs_responses = []
            for i, (qkey, question) in enumerate(CSSRS_QUESTIONS.items(), 1):
                response = st.radio(
                    f"**{i}.** {question}",
                    ["TIDAK", "YA"],
                    horizontal=True,
                    key=f"cssrs_{i}"
                )
                cssrs_responses.append(response == "YA")
            
            cssrs_level, cssrs_risk, cssrs_action = calculate_cssrs_risk(cssrs_responses)
            
            st.markdown("**📊 Hasil C-SSRS:**")
            
            if cssrs_level == 0:
                st.success(f"✅ No Suicide Risk")
            elif cssrs_level <= 2:
                st.warning(f"⚠️ Level {cssrs_level} - {cssrs_risk}")
            elif cssrs_level <= 4:
                st.error(f"🚨 Level {cssrs_level} - {cssrs_risk}")
            else:
                st.markdown(f"""
                <div class="danger-box">
                    <strong>🚨🚨🚨 CRITICAL - Level {cssrs_level} - {cssrs_risk}</strong><br>
                    <strong>ACTION REQUIRED:</strong> {cssrs_action}
                </div>
                """, unsafe_allow_html=True)
            
            st.caption(f"**Tindakan:** {cssrs_action}")
            
            st.markdown("---")
            
            # GAF Score
            st.markdown("### **9️⃣ GAF: Global Assessment of Functioning**")
            st.caption("Penilaian klinis terhadap fungsi keseluruhan (skor 1-100)")
            
            gaf_range = st.select_slider(
                "Pilih range GAF yang sesuai:",
                options=list(GAF_RANGES.keys()),
                value="61-70",
                format_func=lambda x: f"{x}: {GAF_RANGES[x]}",
                key="gaf_range"
            )
            
            gaf_score, gaf_interp = calculate_gaf_score(gaf_range)
            
            st.markdown("**📊 Hasil GAF:**")
            col_gaf1, col_gaf2 = st.columns(2)
            
            with col_gaf1:
                st.metric("GAF Score", gaf_score)
            with col_gaf2:
                if gaf_score >= 71:
                    st.success(f"✅ {gaf_interp}")
                elif gaf_score >= 51:
                    st.info(f"ℹ️ {gaf_interp}")
                elif gaf_score >= 31:
                    st.warning(f"⚠️ {gaf_interp}")
                else:
                    st.error(f"🚨 {gaf_interp}")
            
            st.markdown("---")
            
            # Stages of Change
            st.markdown("### **🔟 STAGES OF CHANGE: Motivational Readiness**")
            st.caption("Prochaska & DiClemente - Tahap kesiapan untuk berubah")
            
            stage_of_change = st.radio(
                "Pilih tahap yang paling sesuai dengan kondisi klien saat ini:",
                list(STAGES_OF_CHANGE.keys()),
                format_func=lambda x: f"**{x}**: {STAGES_OF_CHANGE[x]['description']}",
                key="stage_change"
            )
            
            st.markdown(f"""
            **Karakteristik:** {STAGES_OF_CHANGE[stage_of_change]['characteristics']}
            """)
            
            if stage_of_change in ["Precontemplation", "Relapse"]:
                st.error("⚠️ Low motivation - perlu intensive motivational enhancement")
            elif stage_of_change == "Contemplation":
                st.warning("⚠️ Ambivalen - perlu motivational interviewing")
            elif stage_of_change == "Preparation":
                st.info("ℹ️ Ready for change - support action planning")
            else:
                st.success(f"✅ Active change - maintain support")
            
            st.markdown("---")
            
            # Fungsi Sosial & Komorbid
            st.markdown("### **1️⃣1️⃣ FUNGSI SOSIAL & KOMORBID**")
            
            col_func1, col_func2 = st.columns(2)
            
            with col_func1:
                fungsi_sosial = st.radio(
                    "**Fungsi Sosial:**",
                    [
                        "Masih produktif (sekolah/kerja)",
                        "Mulai terganggu",
                        "Tidak berfungsi sama sekali"
                    ]
                )
                
                hubungan_keluarga = st.radio(
                    "**Hubungan Keluarga:**",
                    ["Baik - dukungan penuh", "Cukup - dukungan terbatas", 
                     "Buruk - konflik tinggi", "Putus hubungan"]
                )
            
            with col_func2:
                ada_komorbid = st.checkbox("Ada gangguan komorbid (psikiatrik/medis)?")
                
                if ada_komorbid:
                    komorbid_jenis = st.multiselect(
                        "Jenis komorbid:",
                        ["Gangguan Depresi", "Gangguan Cemas", "Gangguan Psikotik", 
                         "Gangguan Bipolar", "Gangguan Kepribadian", "PTSD", 
                         "Penyakit Jantung", "Penyakit Hati", "HIV/AIDS", 
                         "Hepatitis", "Diabetes", "Lainnya"]
                    )
                    
                    komorbid_severity = st.radio(
                        "Tingkat keparahan:",
                        ["Ringan", "Sedang", "Berat"]
                    )
                else:
                    komorbid_jenis = []
                    komorbid_severity = "Ringan"
        
        # ==================== SUB-TAB: LEGAL ====================
        with input_tabs[4]:
            st.subheader("⚖️ ASESMEN HUKUM")
            
            st.markdown("### **1️⃣ Peran & Keterlibatan**")
            col_leg1, col_leg2 = st.columns(2)
            
            with col_leg1:
                peran = st.selectbox(
                    "Peran tersangka dalam kasus:",
                    [
                        "Pengguna murni (untuk diri sendiri)",
                        "Berbagi dengan teman (sharing)",
                        "Kurir/pengedar kecil",
                        "Pengedar besar/bandar"
                    ]
                )
                
                if peran == "Pengguna murni (untuk diri sendiri)":
                    st.success("✅ Memenuhi kriteria rehabilitasi (Pasal 127 UU 35/2009)")
                elif peran == "Berbagi dengan teman (sharing)":
                    st.warning("⚠️ Borderline - perlu pertimbangan")
                else:
                    st.error("🚨 Indikasi peredaran")
            
            with col_leg2:
                ada_jaringan = st.checkbox("Bagian dari jaringan peredaran?")
                
                if ada_jaringan:
                    posisi_jaringan = st.radio(
                        "Posisi dalam jaringan:",
                        ["Kurir/runner", "Pengedar tingkat bawah", 
                         "Pengedar tingkat menengah", "Bandar/supplier"]
                    )
                else:
                    posisi_jaringan = "Tidak ada"
            
            st.markdown("---")
            
            # Barang Bukti
            st.markdown("### **2️⃣ Barang Bukti**")
            
            col_bb1, col_bb2 = st.columns(2)
            
            with col_bb1:
                jenis_narkotika = st.selectbox(
                    "Jenis narkotika yang disita:",
                    list(GRAMATUR_LIMITS.keys())
                )
                gramatur_limit = GRAMATUR_LIMITS[jenis_narkotika]
                
                st.info(f"📊 **Gramatur SEMA 4/2010:** ≤ {gramatur_limit}g untuk rehabilitasi")
            
            with col_bb2:
                barang_bukti = st.number_input(
                    "Jumlah barang bukti (gram):",
                    min_value=0.0,
                    max_value=10000.0,
                    value=0.5,
                    step=0.1
                )
                
                if gramatur_limit > 0:
                    ratio = barang_bukti / gramatur_limit
                    
                    if barang_bukti < gramatur_limit:
                        st.success(f"✅ Di bawah gramatur ({ratio:.1f}x)")
                    elif barang_bukti <= gramatur_limit * 2:
                        st.warning(f"⚠️ Sedikit di atas ({ratio:.1f}x)")
                    elif barang_bukti <= gramatur_limit * 5:
                        st.error(f"🚨 Melebihi gramatur ({ratio:.1f}x)")
                    elif barang_bukti <= gramatur_limit * 20:
                        st.error(f"🚨 Jauh melebihi ({ratio:.1f}x)")
                    else:
                        st.error(f"🔥 Sangat jauh melebihi ({ratio:.1f}x)")
            
            st.markdown("---")
            
            # Status & Riwayat
            st.markdown("### **3️⃣ Status Penangkapan & Riwayat**")
            
            col_stat1, col_stat2 = st.columns(2)
            
            with col_stat1:
                status_tangkap = st.selectbox(
                    "Status penangkapan:",
                    [
                        "Sukarela datang untuk asesmen",
                        "Operasi targeted (penggerebekan terencana)",
                        "Tertangkap tangan saat transaksi"
                    ]
                )
                
                riwayat_pidana = st.radio(
                    "Riwayat pidana:",
                    [
                        "First offender (pertama kali)",
                        "Pernah rehab sebelumnya (relapse)",
                        "Residivis kasus narkotika"
                    ]
                )
            
            with col_stat2:
                kooperatif = st.checkbox("Tersangka kooperatif?", value=True)
                
                pengakuan = st.radio(
                    "Status pengakuan:",
                    ["Mengakui semua", "Mengakui sebagian", "Menolak mengakui"]
                )
                
                ada_korban = st.checkbox("Ada korban dalam kasus ini?")
            
            st.markdown("---")
            
            # Saksi & Bukti Lain
            st.markdown("### **4️⃣ Saksi & Bukti Pendukung**")
            
            col_sak1, col_sak2 = st.columns(2)
            
            with col_sak1:
                saksi_meringankan = st.number_input("Jumlah saksi meringankan", 
                    min_value=0, max_value=20, value=0)
                bukti_transaksi = st.checkbox("Ada bukti transaksi (transfer/chat)?")
            
            with col_sak2:
                saksi_memberatkan = st.number_input("Jumlah saksi memberatkan", 
                    min_value=0, max_value=20, value=0)
                aset_mencurigakan = st.checkbox("Ada aset tidak wajar?")
        
        # ==================== SUB-TAB: LAB TESTS ====================
        with input_tabs[5]:
            st.subheader("🧪 HASIL TES LABORATORIUM KUANTITATIF")
            
            st.markdown("""
            <div class="info-box">
            <strong>ℹ️ Petunjuk Pengisian:</strong><br>
            Masukkan nilai konsentrasi zat dalam ng/mL (nanogram per mililiter).<br>
            Sistem akan membandingkan dengan cut-off values standar.
            </div>
            """, unsafe_allow_html=True)
            
            # Input lab values
            st.markdown("### **Hasil Tes Urine Kuantitatif**")
            
            zat_terdeteksi = st.multiselect(
                "Pilih zat yang terdeteksi POSITIF:",
                JENIS_NARKOTIKA,
                default=[]
            )
            
            lab_values = {}
            
            if zat_terdeteksi:
                st.markdown("**Masukkan nilai konsentrasi untuk setiap zat:**")
                
                for zat in zat_terdeteksi:
                    cutoff_info = JENIS_NARKOTIKA_CUTOFF[zat]
                    cutoff = cutoff_info['cutoff']
                    unit = cutoff_info['unit']
                    
                    col_lab1, col_lab2 = st.columns([3, 1])
                    
                    with col_lab1:
                        value = st.number_input(
                            f"**{zat}** (cut-off: {cutoff} {unit})",
                            min_value=0.0,
                            max_value=50000.0,
                            value=float(cutoff * 2) if cutoff > 0 else 100.0,
                            step=10.0,
                            key=f"lab_{zat}"
                        )
                        lab_values[zat] = value
                    
                    with col_lab2:
                        if cutoff > 0:
                            ratio = value / cutoff
                            if ratio < 0.5:
                                st.success("Trace")
                            elif ratio < 1:
                                st.info("Below")
                            elif ratio < 3:
                                st.warning("Positive")
                            else:
                                st.error("High")
                
                # Analyze results
                lab_analysis = analyze_lab_results(lab_values)
                
                st.markdown("---")
                st.markdown("### **📊 Analisis Hasil Lab:**")
                
                for zat, analysis in lab_analysis.items():
                    with st.expander(f"📋 {zat}: {analysis['severity']}", expanded=True):
                        col_ana1, col_ana2, col_ana3 = st.columns(3)
                        
                        with col_ana1:
                            st.metric("Nilai", f"{analysis['value']:.1f} {analysis['unit']}")
                        with col_ana2:
                            st.metric("Cut-off", f"{analysis['cutoff']} {analysis['unit']}")
                        with col_ana3:
                            st.metric("Ratio", f"{analysis['ratio']:.1f}x")
                        
                        st.caption(f"**Interpretasi:** {analysis['interpretation']}")
            
            else:
                st.info("Pilih zat yang terdeteksi positif untuk input nilai kuantitatif")
        
        # ==================== VALIDASI & TOMBOL ANALISIS ====================
        st.markdown("---")
        st.markdown("## 🔍 **VALIDASI & ANALISIS**")
        
        def validate_comprehensive_input():
            """Validasi input komprehensif"""
            errors = []
            warnings = []
            
            # Critical validations
            if barang_bukti <= 0:
                errors.append("Jumlah barang bukti harus > 0 gram")
            
            if all(v == 0 for v in asam_scores.values()):
                errors.append("ASAM assessment belum diisi (semua dimensi 0)")
            
            if not zat_terdeteksi:
                warnings.append("Tidak ada zat yang terdeteksi positif dalam tes lab")
            
            # Consistency checks
            if dsm5_count >= 6 and all(v <= 1 for v in asam_scores.values()):
                warnings.append("Inkonsistensi: DSM-5 severe tapi ASAM low severity")
            
            if barang_bukti > gramatur_limit * 10 and peran == "Pengguna murni (untuk diri sendiri)":
                warnings.append("Inkonsistensi: Barang bukti sangat besar untuk pengguna murni")
            
            if cssrs_level >= 4:
                warnings.append("HIGH SUICIDE RISK detected - immediate intervention required!")
            
            if icd10_dependent and dsm5_count < 4:
                warnings.append("Inkonsistensi: ICD-10 dependent tapi DSM-5 mild/moderate")
            
            return errors, warnings
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        
        with col_btn2:
            analyze_button = st.button(
                "🔍 ANALISIS KOMPREHENSIF TAT",
                use_container_width=True,
                type="primary",
                help="Klik untuk analisis menggunakan 10+ instrumen asesmen"
            )
            
            if analyze_button:
                validation_errors, validation_warnings = validate_comprehensive_input()
                
                if validation_errors:
                    st.error("❌ **Data belum lengkap. Perbaiki error berikut:**")
                    for err in validation_errors:
                        st.error(f"• {err}")
                else:
                    if validation_warnings:
                        st.warning("⚠️ **Peringatan (tetap bisa dianalisis):**")
                        for warn in validation_warnings:
                            st.warning(f"• {warn}")
                    
                    st.session_state['analyze_clicked'] = True
                    st.rerun()
    
    # ==========================================================================
    # TAB 2: HASIL ANALISIS
    # ==========================================================================
    with tab2:
        if 'analyze_clicked' in st.session_state and st.session_state['analyze_clicked']:
            with st.spinner('🔄 Melakukan analisis komprehensif dengan 10+ instrumen...'):
                try:
                    # Calculate all scores
                    skor_medis, medis_breakdown = calculate_medical_composite_v3(
                        asam_pct, dsm5_count, icd10_count, dast10_score,
                        assist_highest_score, aces_score, gaf_score, cssrs_level,
                        ada_komorbid, komorbid_severity
                    )
                    
                    skor_hukum, hukum_breakdown = calculate_legal_score(
                        peran, barang_bukti, jenis_narkotika, status_tangkap,
                        riwayat_pidana, gramatur_limit, kooperatif, pengakuan, ada_korban
                    )
                    
                    # Apply decision rules
                    probabilities, reasoning, primary_rec, clinical_notes = apply_tat_decision_rules_v3(
                        skor_medis, skor_hukum, asam_level, dsm5_count, icd10_dependent,
                        dast10_level, cssrs_level, barang_bukti, gramatur_limit,
                        peran, fungsi_sosial, gaf_score, stage_of_change
                    )
                    
                    # Save to session state
                    st.session_state['tat_results'] = {
                        'skor_medis': skor_medis,
                        'skor_hukum': skor_hukum,
                        'asam_pct': asam_pct,
                        'asam_level': asam_level,
                        'asam_breakdown': asam_breakdown,
                        'dsm5_count': dsm5_count,
                        'dsm5_severity': dsm5_severity,
                        'dsm5_diagnosis': dsm5_diagnosis,
                        'icd10_count': icd10_count,
                        'icd10_dependent': icd10_dependent,
                        'icd10_severity': icd10_severity,
                        'dast10_score': dast10_score,
                        'dast10_level': dast10_level,
                        'dast10_rec': dast10_rec,
                        'assist_results': assist_results,
                        'assist_highest_score': assist_highest_score,
                        'assist_highest_risk': assist_highest_risk,
                        'aces_score': aces_score,
                        'aces_risk': aces_risk,
                        'aces_interp': aces_interp,
                        'cssrs_level': cssrs_level,
                        'cssrs_risk': cssrs_risk,
                        'cssrs_action': cssrs_action,
                        'gaf_score': gaf_score,
                        'gaf_interp': gaf_interp,
                        'stage_of_change': stage_of_change,
                        'medis_breakdown': medis_breakdown,
                        'hukum_breakdown': hukum_breakdown,
                        'probabilities': probabilities,
                        'reasoning': reasoning,
                        'primary_rec': primary_rec,
                        'clinical_notes': clinical_notes,
                        'lab_analysis': lab_analysis if zat_terdeteksi else {},
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'input_data': {
                            'nama_inisial': nama_inisial,
                            'usia': usia,
                            'jenis_kelamin': jenis_kelamin,
                            'pendidikan': pendidikan,
                            'pekerjaan': pekerjaan,
                            'durasi_bulan': durasi_bulan,
                            'usia_mulai': usia_mulai,
                            'zat_utama': zat_utama,
                            'frekuensi': frekuensi,
                            'pola_penggunaan': pola_penggunaan,
                            'rute_penggunaan': rute_penggunaan,
                            'fungsi_sosial': fungsi_sosial,
                            'hubungan_keluarga': hubungan_keluarga,
                            'ada_komorbid': ada_komorbid,
                            'komorbid_jenis': komorbid_jenis,
                            'komorbid_severity': komorbid_severity,
                            'peran': peran,
                            'barang_bukti': barang_bukti,
                            'jenis_narkotika': jenis_narkotika,
                            'gramatur_limit': gramatur_limit,
                            'status_tangkap': status_tangkap,
                            'riwayat_pidana': riwayat_pidana,
                            'kooperatif': kooperatif,
                            'pengakuan': pengakuan,
                            'ada_korban': ada_korban,
                            'zat_terdeteksi': zat_terdeteksi,
                            'asam_scores': asam_scores,
                            'dsm5_responses': dsm5_responses,
                            'icd10_responses': icd10_responses,
                            'dast10_responses': dast10_responses,
                            'aces_responses': aces_responses,
                            'cssrs_responses': cssrs_responses
                        }
                    }
                    
                    st.success("✅ Analisis komprehensif selesai!")
                    st.session_state['analyze_clicked'] = False
                    
                except Exception as e:
                    st.error(f"❌ Error dalam analisis: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                    st.session_state['analyze_clicked'] = False
        
        # Display results
        if 'tat_results' in st.session_state:
            results = st.session_state['tat_results']
            
            st.header("📊 HASIL ANALISIS TIM ASESMEN TERPADU (TAT) v3.0")
            st.caption(f"**Timestamp:** {results['timestamp']}")
            st.caption(f"**Klien:** {results['input_data']['nama_inisial'] or '[Confidential]'} ({results['input_data']['usia']} tahun, {results['input_data']['jenis_kelamin']})")
            
            # Check for emergencies
            if results['clinical_notes'].get('medical_emergency'):
                st.markdown("""
                <div class="danger-box">
                    <h2 style="color: #dc2626; margin: 0;">🚨🚨🚨 MEDICAL EMERGENCY</h2>
                    <p style="font-size: 1.2rem; margin: 0.5rem 0;">
                        <strong>HIGH SUICIDE RISK DETECTED</strong><br>
                        Immediate psychiatric hospitalization required.<br>
                        C-SSRS Level: {level} - {risk}
                    </p>
                </div>
                """.format(level=results['cssrs_level'], risk=results['cssrs_risk']), unsafe_allow_html=True)
            
            # Executive Summary
            st.markdown("### 📋 **RINGKASAN EKSEKUTIF**")
            
            col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
            
            with col_sum1:
                st.metric("Skor Medis", f"{results['skor_medis']:.1f}/100",
                         delta="Berat" if results['skor_medis'] > 70 else "Sedang" if results['skor_medis'] > 40 else "Ringan")
            
            with col_sum2:
                st.metric("Skor Hukum", f"{results['skor_hukum']:.1f}/100",
                         delta="Tinggi" if results['skor_hukum'] > 70 else "Sedang" if results['skor_hukum'] > 40 else "Rendah")
            
            with col_sum3:
                st.metric("ASAM Level", results['asam_level'],
                         delta=ASAM_LEVELS[results['asam_level']])
            
            with col_sum4:
                st.metric("GAF Score", results['gaf_score'],
                         delta="Good" if results['gaf_score'] >= 61 else "Impaired")
            
            st.markdown("---")
            
            # Primary Recommendation
            st.markdown("### 🎯 **REKOMENDASI UTAMA TIM TAT**")
            
            primary_prob = results['probabilities'][results['primary_rec']]
            
            if "Rawat Jalan" in results['primary_rec']:
                box_class = "success-box"
                icon = "✅"
            elif "Rawat Inap" in results['primary_rec']:
                box_class = "info-box"
                icon = "🏥"
            elif "Hukum + Rehabilitasi" in results['primary_rec']:
                box_class = "legal-box"
                icon = "⚖️"
            else:
                box_class = "warning-box"
                icon = "⚠️"
            
            st.markdown(f"""
            <div class="{box_class}">
                <h2 style="margin: 0;">{icon} {results['primary_rec']}</h2>
                <p style="font-size: 1.3rem; margin: 0.5rem 0; font-weight: bold;">
                    Tingkat Keyakinan: {primary_prob:.1f}%
                </p>
                <p style="margin: 0.5rem 0;">
                    Rekomendasi berdasarkan analisis komprehensif 10+ instrumen asesmen standar internasional
                    dan regulasi BNN.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Detailed Reasoning
            st.markdown("### 📝 **ALASAN & PERTIMBANGAN**")
            
            for reason in results['reasoning']:
                if reason.startswith("✓"):
                    st.success(reason)
                elif reason.startswith("✗"):
                    st.error(reason)
                elif reason.startswith("!"):
                    st.warning(reason)
                elif reason.startswith("🚨"):
                    st.error(reason)
                else:
                    st.info(reason)
            
            st.markdown("---")
            
            # Probabilities
            st.markdown("### 📊 **DISTRIBUSI PROBABILITAS**")
            
            prob_df = pd.DataFrame({
                'Rekomendasi': list(results['probabilities'].keys()),
                'Probabilitas': [f"{v:.1f}%" for v in results['probabilities'].values()],
                'Status': ['✅ PRIMARY' if k == results['primary_rec'] else '◻️ Alternative' 
                          for k in results['probabilities'].keys()]
            })
            
            st.dataframe(prob_df, use_container_width=True, hide_index=True)
            
            fig_prob = create_probability_chart(results['probabilities'])
            st.plotly_chart(fig_prob, use_container_width=True)
            
            st.markdown("---")
            
            # Multi-Instrument Summary
            st.markdown("### 🔬 **RINGKASAN MULTI-INSTRUMEN**")
            
            col_inst1, col_inst2, col_inst3 = st.columns(3)
            
            with col_inst1:
                st.markdown("**Diagnostic Instruments:**")
                st.markdown(f"- **DSM-5:** {results['dsm5_count']}/11 - {results['dsm5_severity']}")
                st.markdown(f"- **ICD-10:** {results['icd10_count']}/6 - {'Dependent' if results['icd10_dependent'] else 'Not Dependent'}")
                st.markdown(f"- **DAST-10:** {results['dast10_score']}/10 - {results['dast10_level']}")
            
            with col_inst2:
                st.markdown("**Risk Assessments:**")
                st.markdown(f"- **C-SSRS:** Level {results['cssrs_level']}/5 - {results['cssrs_risk']}")
                st.markdown(f"- **ACEs:** {results['aces_score']}/10 - {results['aces_risk']}")
                st.markdown(f"- **ASSIST:** {results['assist_highest_score']}/39 - {results['assist_highest_risk']}")
            
            with col_inst3:
                st.markdown("**Functional Status:**")
                st.markdown(f"- **GAF:** {results['gaf_score']}/100 - {results['gaf_interp']}")
                st.markdown(f"- **ASAM:** Level {results['asam_level']} - {ASAM_LEVELS[results['asam_level']]}")
                st.markdown(f"- **Stage:** {results['stage_of_change']}")
            
            st.markdown("---")
            
            # Clinical Notes
            if results['clinical_notes']:
                st.markdown("### 📌 **CATATAN KLINIS PENTING**")
                
                notes_display = []
                if results['clinical_notes'].get('medical_emergency'):
                    notes_display.append("🚨 **MEDICAL EMERGENCY** - Immediate intervention required")
                if results['clinical_notes'].get('suicide_protocol'):
                    notes_display.append("⚠️ Suicide prevention protocol activated")
                if results['clinical_notes'].get('law_enforcement_priority'):
                    notes_display.append("⚖️ Law enforcement priority case")
                if results['clinical_notes'].get('borderline_case'):
                    notes_display.append("🔍 Borderline case - requires TAT case conference")
                if results['clinical_notes'].get('complex_case'):
                    notes_display.append("📋 Complex case - comprehensive TAT review required")
                
                for note in notes_display:
                    if "EMERGENCY" in note:
                        st.error(note)
                    elif "⚖️" in note or "🔍" in note:
                        st.warning(note)
                    else:
                        st.info(note)
            
            st.markdown("---")
            
            # Legal Basis
            st.markdown("### ⚖️ **DASAR HUKUM REKOMENDASI**")
            
            legal_basis_map = {
                "Rehabilitasi Rawat Jalan": [
                    "✓ Pasal 54 UU 35/2009 - Kewajiban rehabilitasi untuk pecandu",
                    "✓ Pasal 127 UU 35/2009 - Penyalahguna dapat direhabilitasi",
                    "✓ SEMA No. 4 Tahun 2010 - Kriteria gramatur untuk rehabilitasi",
                    "✓ Perka BNN No. 11 Tahun 2014 - Asesmen terpadu"
                ],
                "Rehabilitasi Rawat Inap": [
                    "✓ Pasal 54 UU 35/2009 - Kewajiban rehabilitasi untuk pecandu berat",
                    "✓ Pasal 103 UU 35/2009 - Hakim dapat memerintahkan rehabilitasi",
                    "✓ SEMA No. 4 Tahun 2010 - Rehab untuk pecandu dengan komplikasi",
                    "✓ Peraturan Bersama 7 Instansi - Asesmen terpadu komprehensif"
                ],
                "Proses Hukum": [
                    "✓ Pasal 111-114 UU 35/2009 - Ketentuan pidana peredaran",
                    "✓ SEMA No. 4 Tahun 2010 - Batasan gramatur rehabilitasi",
                    "✓ Perka BNN No. 11 Tahun 2014 - Kriteria penolakan rehabilitasi"
                ],
                "Proses Hukum + Rehabilitasi": [
                    "✓ Pasal 103 ayat (2) UU 35/2009 - Rehabilitasi sambil menjalani pidana",
                    "✓ Peraturan Bersama 7 Instansi - Dual track approach",
                    "✓ SEMA No. 4 Tahun 2010 - Pengecualian kasus borderline",
                    "✓ Perka BNN No. 11 Tahun 2014 - Prosedur asesmen kompleks"
                ]
            }
            
            current_basis = legal_basis_map.get(results['primary_rec'], [])
            for basis in current_basis:
                st.markdown(basis)
            
            st.markdown("---")
            
            # Action Items
            st.markdown("### 💡 **REKOMENDASI TINDAK LANJUT**")
            
            if results['clinical_notes'].get('medical_emergency'):
                st.error("""
                🚨 **IMMEDIATE ACTIONS:**
                1. Segera hubungi psikiater on-call
                2. Implementasi suicide watch protocol
                3. Remove access to means of self-harm
                4. Psychiatric hospitalization ASAP
                5. Notify family/guardian immediately
                """)
            
            st.info("""
            📋 **STANDARD FOLLOW-UP:**
            1. Jadwalkan Case Conference Tim TAT dalam 3 hari kerja
            2. Lengkapi dokumentasi medis dan hukum
            3. Koordinasi dengan IPWL/lembaga rehabilitasi
            4. Siapkan laporan komprehensif untuk pengadilan
            5. Tentukan timeline monitoring dan evaluasi
            """)
            
            if results['clinical_notes'].get('complex_case') or results['clinical_notes'].get('borderline_case'):
                st.warning("""
                ⚠️ **SPECIAL CONSIDERATIONS:**
                - Kasus ini memerlukan diskusi mendalam dalam Case Conference
                - Undang semua stakeholder: dokter, psikolog, penyidik, jaksa, hakim
                - Pertimbangkan second opinion dari ahli adiksi senior
                - Dokumentasi lengkap sangat krusial untuk keputusan final
                """)
            
            st.markdown("---")
            
            # Export Options
            st.markdown("### 💾 **EKSPOR & DOKUMENTASI**")
            
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            
            with col_exp1:
                export_data = {
                    "laporan_tat_v3": {
                        "metadata": {
                            "version": "3.0.0 COMPREHENSIVE",
                            "timestamp": results['timestamp'],
                            "instruments": [
                                "ASAM 6D", "DSM-5", "ICD-10", "DAST-10", 
                                "ASSIST", "ACEs", "C-SSRS", "GAF", "Stages of Change"
                            ],
                            "legal_basis": [
                                "UU 35/2009", "SEMA 4/2010", 
                                "Peraturan Bersama 7 Instansi", "Perka BNN 11/2014"
                            ]
                        },
                        "hasil_analisis": results
                    }
                }
                json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"TAT_v3_Report_{results['timestamp'].replace(':', '-').replace(' ', '_')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col_exp2:
                if st.button("📋 Generate PDF", use_container_width=True, disabled=True):
                    st.info("Fitur PDF akan tersedia dalam update berikutnya")
            
            with col_exp3:
                if st.button("📤 Submit to BNN System", use_container_width=True, disabled=True):
                    st.info("Integrasi sistem BNN akan dikembangkan sesuai protokol")
            
            st.markdown("""
            <div class="legal-box">
                <strong>🔒 KEAMANAN DATA:</strong><br>
                • Data asesmen bersifat <strong>RAHASIA MEDIS</strong><br>
                • Akses terbatas untuk Tim TAT yang berwenang<br>
                • Penyimpanan sesuai UU Perlindungan Data Pribadi<br>
                • Tidak boleh disebarluaskan tanpa izin resmi
            </div>
            """, unsafe_allow_html=True)
        
        else:
            st.info("👈 Silakan isi data di tab **Input Data** dan klik tombol **Analisis Komprehensif**")
    
    # ==========================================================================
    # TAB 3: VISUALISASI DETAIL
    # ==========================================================================
    with tab3:
        if 'tat_results' in st.session_state:
            results = st.session_state['tat_results']
            
            st.header("📈 VISUALISASI DETAIL ANALISIS")
            
            # ASAM Radar Chart
            st.markdown("### 📊 **ASAM 6 DIMENSIONS RADAR**")
            asam_scores_viz = {int(k.split()[1]): v['score'] for k, v in results['asam_breakdown'].items()}
            fig_asam = create_asam_radar_chart(asam_scores_viz)
            st.plotly_chart(fig_asam, use_container_width=True)
            
            st.markdown("---")
            
            # Composite Scores
            st.markdown("### 🎯 **SKOR KOMPOSIT**")
            
            col_viz1, col_viz2 = st.columns(2)
            
            with col_viz1:
                fig_medis = create_gauge_chart(results['skor_medis'], "Skor Medis Komposit")
                st.plotly_chart(fig_medis, use_container_width=True)
            
            with col_viz2:
                fig_hukum = create_gauge_chart(results['skor_hukum'], "Skor Hukum")
                st.plotly_chart(fig_hukum, use_container_width=True)
            
            st.markdown("---")
            
            # Breakdown Charts
            st.markdown("### 📊 **BREAKDOWN DETAIL**")
            
            col_break1, col_break2 = st.columns(2)
            
            with col_break1:
                # Medical breakdown
                medis_for_chart = {}
                for key, value in results['medis_breakdown'].items():
                    medis_for_chart[key] = {
                        'score': value['score'],
                        'max': 100 * value['weight']
                    }
                fig_med_break = create_breakdown_chart(medis_for_chart, "Breakdown Skor Medis")
                st.plotly_chart(fig_med_break, use_container_width=True)
            
            with col_break2:
                fig_hukum_break = create_breakdown_chart(results['hukum_breakdown'], "Breakdown Skor Hukum")
                st.plotly_chart(fig_hukum_break, use_container_width=True)
            
            st.markdown("---")
            
            # Multi-instrument comparison
            st.markdown("### 🔬 **PERBANDINGAN MULTI-INSTRUMEN**")
            
            instruments_data = {
                'Instrumen': ['DSM-5', 'ICD-10', 'DAST-10', 'ASSIST', 'ACEs', 'C-SSRS', 'GAF (inv)'],
                'Skor': [
                    (results['dsm5_count'] / 11) * 100,
                    (results['icd10_count'] / 6) * 100,
                    (results['dast10_score'] / 10) * 100,
                    (results['assist_highest_score'] / 39) * 100,
                    (results['aces_score'] / 10) * 100,
                    (results['cssrs_level'] / 5) * 100,
                    100 - results['gaf_score']
                ]
            }
            
            fig_comparison = px.bar(
                instruments_data,
                x='Instrumen',
                y='Skor',
                title="Normalized Scores Across Instruments (0-100%)",
                color='Skor',
                color_continuous_scale=['#22c55e', '#f59e0b', '#ef4444']
            )
            fig_comparison.update_layout(height=400)
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            st.markdown("---")
            
            # Risk Matrix
            st.markdown("### 🎯 **MATRIKS RISIKO KOMPREHENSIF**")
            
            risk_matrix_data = {
                'Domain': ['Addiction Severity', 'Legal Risk', 'Suicide Risk', 'Relapse Risk', 'Functional Impairment'],
                'Level': [
                    'Severe' if results['skor_medis'] > 70 else 'Moderate' if results['skor_medis'] > 40 else 'Mild',
                    'High' if results['skor_hukum'] > 70 else 'Moderate' if results['skor_hukum'] > 40 else 'Low',
                    'High' if results['cssrs_level'] >= 4 else 'Moderate' if results['cssrs_level'] >= 2 else 'Low',
                    'High' if results['aces_score'] >= 4 or results['stage_of_change'] in ['Precontemplation', 'Relapse'] else 'Moderate',
                    'Severe' if results['gaf_score'] < 40 else 'Moderate' if results['gaf_score'] < 60 else 'Mild'
                ],
                'Score': [
                    results['skor_medis'],
                    results['skor_hukum'],
                    (results['cssrs_level'] / 5) * 100,
                    max((results['aces_score'] / 10) * 100, 50 if results['stage_of_change'] in ['Precontemplation'] else 30),
                    100 - results['gaf_score']
                ]
            }
            
            st.dataframe(pd.DataFrame(risk_matrix_data), use_container_width=True, hide_index=True)
            
            fig_risk = px.bar(
                risk_matrix_data,
                x='Domain',
                y='Score',
                color='Level',
                title="Risk Profile Across Domains",
                color_discrete_map={'Low': '#22c55e', 'Mild': '#22c55e', 'Moderate': '#f59e0b', 'High': '#ef4444', 'Severe': '#dc2626'}
            )
            fig_risk.update_layout(height=400)
            st.plotly_chart(fig_risk, use_container_width=True)
            
        else:
            st.info("👈 Silakan lakukan analisis terlebih dahulu")
    
    # ==========================================================================
    # TAB 4: LAPORAN
    # ==========================================================================
    with tab4:
        if 'tat_results' in st.session_state:
            results = st.session_state['tat_results']
            
            st.header("📋 LAPORAN RESMI TAT")
            
            with st.expander("📄 TEMPLATE LAPORAN KOMPREHENSIF", expanded=True):
                st.markdown(f"""
# BADAN NARKOTIKA NASIONAL REPUBLIK INDONESIA
## TIM ASESMEN TERPADU (TAT)
### LAPORAN HASIL ASESMEN KOMPREHENSIF v3.0

---

**NOMOR LAPORAN:** TAT/{datetime.now().year}/{datetime.now().month:02d}/[AUTO]  
**TANGGAL ASESMEN:** {results['timestamp']}  
**LOKASI ASESMEN:** [Diisi oleh TAT]

---

## A. INFORMASI KLIEN

**Inisial:** {results['input_data']['nama_inisial'] or '[CONFIDENTIAL]'}  
**Usia:** {results['input_data']['usia']} tahun  
**Jenis Kelamin:** {results['input_data']['jenis_kelamin']}  
**Pendidikan:** {results['input_data']['pendidikan']}  
**Pekerjaan:** {results['input_data']['pekerjaan']}

---

## B. HASIL ASESMEN MEDIS KOMPREHENSIF

### 1. ASAM 6 DIMENSI ASSESSMENT
**Level of Care:** {results['asam_level']} - {ASAM_LEVELS[results['asam_level']]}  
**Severity Overall:** {results['asam_pct']:.1f}%

**Detail per Dimensi:**
""")
                
                for dim, data in results['asam_breakdown'].items():
                    st.markdown(f"- **{data['name']}**: {data['score']}/4 - {data['severity']}")
                
                st.markdown(f"""

### 2. DSM-5 DIAGNOSTIC CRITERIA
**Kriteria Terpenuhi:** {results['dsm5_count']}/11  
**Diagnosis:** {results['dsm5_diagnosis']}  
**Severity Level:** {results['dsm5_severity']}

### 3. ICD-10 DEPENDENCE SYNDROME
**Kriteria Terpenuhi:** {results['icd10_count']}/6  
**Status:** {'DEPENDENT' if results['icd10_dependent'] else 'NOT DEPENDENT'}  
**Classification:** {results['icd10_severity']}

### 4. DAST-10 SCREENING
**Score:** {results['dast10_score']}/10  
**Risk Level:** {results['dast10_level']}  
**Recommendation:** {results['dast10_rec']}

### 5. ASSIST SCREENING (WHO)
**Highest Score:** {results['assist_highest_score']}/39  
**Overall Risk:** {results['assist_highest_risk']}

**Detail per Zat:**
""")
                
                for substance, data in results['assist_results'].items():
                    st.markdown(f"- **{substance}**: {data['score']}/39 - {data['risk_level']}")
                
                st.markdown(f"""

### 6. ACEs (ADVERSE CHILDHOOD EXPERIENCES)
**Score:** {results['aces_score']}/10  
**Risk Level:** {results['aces_risk']}  
**Interpretation:** {results['aces_interp']}

### 7. C-SSRS SUICIDE RISK ASSESSMENT
**Level:** {results['cssrs_level']}/5  
**Risk Category:** {results['cssrs_risk']}  
**Action Required:** {results['cssrs_action']}

### 8. GAF (GLOBAL ASSESSMENT OF FUNCTIONING)
**Score:** {results['gaf_score']}/100  
**Interpretation:** {results['gaf_interp']}

### 9. STAGES OF CHANGE
**Current Stage:** {results['stage_of_change']}  
**Characteristics:** {STAGES_OF_CHANGE[results['stage_of_change']]['characteristics']}

### 10. COMPOSITE MEDICAL SCORE
**Total Score:** {results['skor_medis']:.1f}/100  
**Category:** {'SEVERE' if results['skor_medis'] > 70 else 'MODERATE' if results['skor_medis'] > 40 else 'MILD'}

---

## C. HASIL ASESMEN HUKUM

**Peran Tersangka:** {results['input_data']['peran']}  
**Barang Bukti:** {results['input_data']['barang_bukti']}g {results['input_data']['jenis_narkotika']}  
**Gramatur SEMA:** {results['input_data']['gramatur_limit']}g  
**Ratio:** {results['input_data']['barang_bukti'] / results['input_data']['gramatur_limit']:.1f}x  
**Status Penangkapan:** {results['input_data']['status_tangkap']}  
**Riwayat Pidana:** {results['input_data']['riwayat_pidana']}  
**Kooperatif:** {'Ya' if results['input_data']['kooperatif'] else 'Tidak'}  
**Pengakuan:** {results['input_data']['pengakuan']}

**Total Skor Hukum:** {results['skor_hukum']:.1f}/100

---

## D. REKOMENDASI TIM ASESMEN TERPADU

### REKOMENDASI UTAMA: **{results['primary_rec']}**
**Tingkat Keyakinan:** {results['probabilities'][results['primary_rec']]:.1f}%

### PERTIMBANGAN UTAMA:
""")
                
                for reason in results['reasoning']:
                    st.markdown(f"- {reason}")
                
                st.markdown(f"""

### DISTRIBUSI PROBABILITAS:
""")
                
                for rec, prob in results['probabilities'].items():
                    st.markdown(f"- **{rec}**: {prob:.1f}%")
                
                st.markdown(f"""

### CATATAN KLINIS:
""")
                
                if results['clinical_notes'].get('medical_emergency'):
                    st.markdown("- **⚠️ MEDICAL EMERGENCY**: Immediate psychiatric intervention required")
                if results['clinical_notes'].get('suicide_protocol'):
                    st.markdown("- **⚠️ SUICIDE PROTOCOL**: Active monitoring and prevention measures")
                if results['clinical_notes'].get('borderline_case'):
                    st.markdown("- **🔍 BORDERLINE CASE**: Requires comprehensive TAT case conference")
                if results['clinical_notes'].get('complex_case'):
                    st.markdown("- **📋 COMPLEX CASE**: Multi-stakeholder discussion recommended")
                
                st.markdown("""

---

## E. DASAR HUKUM & REGULASI

1. **UU No. 35 Tahun 2009** tentang Narkotika (Pasal 54, 103, 127)
2. **SEMA No. 4 Tahun 2010** tentang Penanganan Pecandu Narkotika
3. **Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014**
4. **Perka BNN No. 11 Tahun 2014** tentang Tata Cara Penanganan Tersangka Pecandu

---

## F. DISCLAIMER

1. Laporan ini merupakan **ALAT BANTU** untuk Tim Asesmen Terpadu
2. Keputusan final berada di tangan **Tim TAT dan Aparat Penegak Hukum**
3. Rekomendasi bersifat **TEKNIS dan INFORMATIF**
4. Perlu **CASE CONFERENCE** untuk finalisasi keputusan
5. Dokumentasi lengkap harus disimpan sesuai **SOP BNN**

---

## G. TIM ASESMEN TERPADU

**Dokter Spesialis:**  
Nama: _________________________  
NIP: _________________________  
Tanda Tangan: _________________

**Psikolog Klinis:**  
Nama: _________________________  
NIP: _________________________  
Tanda Tangan: _________________

**Penyidik (Polri/BNN):**  
Nama: _________________________  
NIP: _________________________  
Tanda Tangan: _________________

**Jaksa Penuntut:**  
Nama: _________________________  
NIP: _________________________  
Tanda Tangan: _________________

**Hakim:**  
Nama: _________________________  
NIP: _________________________  
Tanda Tangan: _________________

**Koordinator BNN:**  
Nama: _________________________  
NIP: _________________________  
Tanda Tangan: _________________

---

**Tempat, {datetime.now().strftime('%d %B %Y')}**

**KETUA TIM ASESMEN TERPADU**



_________________________  
[Nama & NIP]

---

*Dokumen ini bersifat RAHASIA dan hanya untuk keperluan proses hukum dan rehabilitasi*
                """)
            
            # Checklist Dokumentasi
            st.markdown("---")
            st.markdown("### ✅ **CHECKLIST DOKUMENTASI WAJIB**")
            
            checklist_items = [
                "Formulir Asesmen Medis lengkap dengan lampiran",
                "Hasil Tes Urine/Lab kuantitatif asli",
                "Dokumentasi wawancara klinis (audio/video/transkrip)",
                "Formulir ASAM 6 Dimensi lengkap",
                "Formulir DSM-5 & ICD-10 lengkap",
                "Hasil DAST-10 & ASSIST",
                "Assessment ACEs, C-SSRS, GAF",
                "Formulir Asesmen Hukum lengkap",
                "Berita Acara Pemeriksaan (BAP)",
                "Fotokopi/dokumentasi Barang Bukti",
                "Riwayat kesehatan lengkap & rekam medis",
                "Surat Pernyataan Kesediaan Rehabilitasi (jika applicable)",
                "Identitas lengkap (KTP, KK, Foto)",
                "Surat Keterangan dari Keluarga",
                "Dokumentasi Case Conference TAT"
            ]
            
            completed_items = []
            for item in checklist_items:
                checked = st.checkbox(item, key=f"doc_check_{item}")
                if checked:
                    completed_items.append(item)
            
            completion_rate = len(completed_items) / len(checklist_items)
            st.progress(completion_rate, text=f"Kelengkapan: {len(completed_items)}/{len(checklist_items)} ({completion_rate*100:.0f}%)")
            
            if completion_rate == 1.0:
                st.success("✅ **DOKUMENTASI LENGKAP** - Siap untuk finalisasi")
            elif completion_rate >= 0.8:
                st.warning("⚠️ **HAMPIR LENGKAP** - Perlu melengkapi beberapa dokumen")
            else:
                st.error("❌ **BELUM LENGKAP** - Mohon lengkapi dokumentasi sebelum Case Conference")
        
        else:
            st.info("👈 Silakan lakukan analisis terlebih dahulu")
    
    # ==========================================================================
    # TAB 5: LAB RESULTS DETAIL
    # ==========================================================================
    with tab5:
        if 'tat_results' in st.session_state:
            results = st.session_state['tat_results']
            
            st.header("🔬 ANALISIS HASIL LABORATORIUM DETAIL")
            
            if results.get('lab_analysis'):
                st.markdown("### 📊 **HASIL TES URINE KUANTITATIF**")
                
                for zat, analysis in results['lab_analysis'].items():
                    with st.expander(f"🧪 {zat} - {analysis['severity']}", expanded=True):
                        col_lab1, col_lab2, col_lab3, col_lab4 = st.columns(4)
                        
                        with col_lab1:
                            st.metric("Nilai Terdeteksi", f"{analysis['value']:.1f} {analysis['unit']}")
                        
                        with col_lab2:
                            st.metric("Cut-off Standard", f"{analysis['cutoff']} {analysis['unit']}")
                        
                        with col_lab3:
                            ratio_color = "normal" if analysis['ratio'] < 1 else "inverse" if analysis['ratio'] < 3 else "off"
                            st.metric("Ratio vs Cut-off", f"{analysis['ratio']:.1f}x", delta=None)
                        
                        with col_lab4:
                            if analysis['severity'] == "Trace":
                                st.success("Trace/Negatif")
                            elif analysis['severity'] == "Below Cutoff":
                                st.info("Di bawah cut-off")
                            elif analysis['severity'] == "Positive":
                                st.warning("Positif")
                            elif analysis['severity'] == "Strong Positive":
                                st.error("Positif Kuat")
                            else:
                                st.error("Sangat Tinggi")
                        
                        st.caption(f"**Interpretasi:** {analysis['interpretation']}")
                        
                        # Visual bar
                        st.progress(min(analysis['ratio'], 10) / 10, 
                                   text=f"Konsentrasi: {analysis['ratio']:.1f}x cut-off")
                
                # Summary table
                st.markdown("---")
                st.markdown("### 📋 **RANGKUMAN HASIL LAB**")
                
                lab_summary = []
                for zat, analysis in results['lab_analysis'].items():
                    lab_summary.append({
                        'Zat': zat,
                        'Nilai': f"{analysis['value']:.1f} {analysis['unit']}",
                        'Cut-off': f"{analysis['cutoff']} {analysis['unit']}",
                        'Ratio': f"{analysis['ratio']:.1f}x",
                        'Status': analysis['severity'],
                        'Interpretasi': analysis['interpretation']
                    })
                
                st.dataframe(pd.DataFrame(lab_summary), use_container_width=True, hide_index=True)
                
                # Clinical interpretation
                st.markdown("---")
                st.markdown("### 🏥 **INTERPRETASI KLINIS**")
                
                high_concentration = [z for z, a in results['lab_analysis'].items() if a['ratio'] > 5]
                moderate_concentration = [z for z, a in results['lab_analysis'].items() if 3 < a['ratio'] <= 5]
                
                if high_concentration:
                    st.error(f"**🚨 Konsentrasi Sangat Tinggi:** {', '.join(high_concentration)}")
                    st.caption("Indikasi penggunaan recent/heavy use. Perlu monitoring withdrawal.")
                
                if moderate_concentration:
                    st.warning(f"**⚠️ Konsentrasi Tinggi:** {', '.join(moderate_concentration)}")
                    st.caption("Indikasi penggunaan regular/frequent.")
                
                # Recommendations based on lab
                st.markdown("**📋 Rekomendasi Berdasarkan Hasil Lab:**")
                
                if any(a['ratio'] > 10 for a in results['lab_analysis'].values()):
                    st.markdown("- 🚨 **Very high concentration** - Monitor untuk withdrawal syndrome")
                    st.markdown("- 🏥 **Medical detoxification** mungkin diperlukan")
                
                if len(results['lab_analysis']) >= 3:
                    st.markdown("- ⚠️ **Polisubstansi** terdeteksi - komplikasi withdrawal lebih kompleks")
                    st.markdown("- 📊 **Comprehensive medical workup** diperlukan")
                
                st.markdown("- 🔄 **Follow-up testing** direkomendasikan dalam 7-14 hari")
                st.markdown("- 📝 **Dokumentasi** hasil lab untuk monitoring progress rehabilitasi")
            
            else:
                st.info("Tidak ada data hasil laboratorium yang diinput")
        
        else:
            st.info("👈 Silakan lakukan analisis terlebih dahulu")
    
    # ==========================================================================
    # TAB 6: PANDUAN
    # ==========================================================================
    with tab6:
        st.header("ℹ️ PANDUAN LENGKAP SISTEM TAT v3.0")
        
        st.markdown("""
        ### 📖 **TENTANG SISTEM v3.0 COMPREHENSIVE**
        
        Sistem Pendukung Keputusan Tim Asesmen Terpadu (TAT) versi 3.0 ini adalah upgrade komprehensif yang mengintegrasikan **10+ instrumen asesmen standar internasional** dengan regulasi BNN Indonesia.
        
        **Instrumen yang Terintegrasi:**
        1. ✅ **ASAM 6 Dimensi** - Gold standard multidimensional assessment
        2. ✅ **DSM-5** - 11 kriteria diagnostik
        3. ✅ **ICD-10** - Dependence syndrome criteria
        4. ✅ **DAST-10** - Drug Abuse Screening Test
        5. ✅ **ASSIST** - WHO screening tool (per substance)
        6. ✅ **ACEs** - Adverse Childhood Experiences
        7. ✅ **C-SSRS** - Columbia Suicide Severity Rating Scale
        8. ✅ **GAF** - Global Assessment of Functioning
        9. ✅ **Stages of Change** - Motivational readiness
        10. ✅ **Lab Quantitative Analysis** - With cut-off values
        
        **Perbaikan dari Versi Sebelumnya:**
        - ✅ ASSIST scoring **DIPERBAIKI** (per substance, bukan total)
        - ✅ Tambahan ICD-10, DAST-10, ACEs, C-SSRS, GAF
        - ✅ Bobot skor komposit **DIREVISI** berdasarkan evidence-based
        - ✅ Decision rules **LEBIH KOMPREHENSIF** dengan clinical notes
        - ✅ Emergency detection (suicide risk, medical emergency)
        - ✅ Lab quantitative analysis dengan cut-off values
        
        ---
        
        ### 📋 **CARA PENGGUNAAN SISTEM**
        
        #### **FASE 1: PERSIAPAN (Pre-Assessment)**
        1. **Kumpulkan Dokumen:**
           - BAP (Berita Acara Pemeriksaan)
           - Hasil tes urine/lab **kuantitatif**
           - Rekam medis (jika ada)
           - Identitas lengkap
        
        2. **Bentuk Tim TAT Minimal:**
           - 1 Dokter Spesialis Jiwa/Adiksi
           - 1 Psikolog Klinis
           - 1 Penyidik (Polri/BNN)
           - 1 Jaksa
           - 1 Hakim (jika sudah proses sidang)
           - 1 Koordinator BNN
        
        3. **Lakukan Wawancara Klinis:**
           - Minimum 90-120 menit
           - Gunakan structured interview
           - Dokumentasikan (audio/video jika memungkinkan)
        
        #### **FASE 2: INPUT DATA (Assessment)**
        1. **Tab Input Data - Identitas:**
           - Isi informasi dasar klien
           - Data ini untuk dokumentasi internal
        
        2. **Tab Medical (1/3) - Basic & Diagnostic:**
           - Info medis dasar
           - **DSM-5**: Centang kriteria yang terpenuhi
           - **ICD-10**: Centang kriteria dependence
        
        3. **Tab Medical (2/3) - Screening:**
           - **DAST-10**: 10 pertanyaan YA/TIDAK
           - **ASSIST**: Per zat, 3-7 pertanyaan (simplified)
        
        4. **Tab Medical (3/3) - Comprehensive:**
           - **ASAM 6 Dimensi**: Severity 0-4 per dimensi
           - **ACEs**: 10 kategori trauma masa kecil
           - **C-SSRS**: 5 pertanyaan suicide risk
           - **GAF**: Pilih range functioning
           - **Stages of Change**: Pilih tahap motivasi
           - **Fungsi Sosial & Komorbid**
        
        5. **Tab Legal:**
           - Peran tersangka
           - Barang bukti (gram)
           - Status penangkapan
           - Riwayat pidana
           - Kooperatif & pengakuan
        
        6. **Tab Lab Tests:**
           - Input nilai kuantitatif (ng/mL)
           - Sistem akan compare dengan cut-off
        
        #### **FASE 3: ANALISIS & REVIEW**
        1. **Klik Tombol Analisis**
           - Sistem validasi input
           - Proses analisis komprehensif
           - Generate rekomendasi
        
        2. **Review Hasil di Tab Hasil Analisis:**
           - **Executive Summary**: Overview singkat
           - **Primary Recommendation**: Rekomendasi utama + confidence level
           - **Reasoning**: Alasan detail
           - **Multi-Instrument Summary**: Hasil semua instrumen
           - **Clinical Notes**: Catatan khusus (emergency, borderline case, dll)
        
        3. **Check Visualisasi di Tab Visualisasi:**
           - ASAM Radar Chart
           - Gauge charts untuk skor komposit
           - Breakdown detail
           - Risk matrix
        
        #### **FASE 4: DOKUMENTASI & CASE CONFERENCE**
        1. **Generate Laporan (Tab Laporan):**
           - Template laporan komprehensif
           - Checklist dokumentasi
           - Export JSON
        
        2. **Case Conference Tim TAT:**
           - Present hasil sistem
           - Diskusi mendalam
           - Pertimbangan faktor kontekstual
           - Keputusan kolektif
        
        3. **Finalisasi & Submit:**
           - Tanda tangan semua anggota TAT
           - Submit ke pengadilan/instansi terkait
           - Archive dokumentasi
        
        ---
        
        ### ⚠️ **KRITERIA KHUSUS & RED FLAGS**
        
        #### **🚨 MEDICAL EMERGENCIES - Immediate Action**
        - **C-SSRS Level 4-5**: Intent with/without plan → Psychiatric hospitalization ASAP
        - **ASAM Dimension 1 atau 2 = 4**: Severe withdrawal/medical → ICU/Emergency
        - **GAF < 20**: Danger to self/others → Immediate supervision
        
        #### **⚖️ LEGAL DISQUALIFIERS - Rehabilitasi Tidak Eligible**
        - **Barang bukti > 20x gramatur SEMA**: Strongly indicates trafficking
        - **Peran: Pengedar besar/bandar**: Law enforcement priority
        - **Residivis + BB > 5x gramatur**: Pattern of dealing
        
        #### **🔍 BORDERLINE CASES - Requires TAT Conference**
        - **BB 1-5x gramatur + Dependent**: Perlu evaluasi mendalam
        - **BB > 5x + DSM-5 severe**: Dual consideration needed
        - **Inkonsistensi data**: Medical vs legal tidak match
        
        ---
        
        ### 📊 **INTERPRETASI SKOR KOMPOSIT MEDIS**
        
        **Bobot Instrumen (Total 100%):**
        - ASAM 6 Dimensi: **35%** (comprehensive multidimensional)
        - DSM-5: **20%** (diagnostic gold standard)
        - ICD-10: **15%** (international diagnostic)
        - DAST-10: **10%** (screening)
        - ASSIST: **8%** (WHO screening)
        - ACEs: **5%** (trauma history)
        - GAF: **4%** (functioning)
        - C-SSRS: **3%** (suicide risk)
        - Komorbid: **+5%** (adjustment)
        
        **Kategori Skor Medis:**
        - **0-30**: Mild addiction - Rawat jalan suitable
        - **31-60**: Moderate addiction - Consider intensive outpatient/inpatient
        - **61-80**: Severe addiction - Inpatient recommended
        - **81-100**: Very severe - Medically-managed intensive inpatient
        
        **Kategori Skor Hukum:**
        - **0-30**: Low legal concern - Rehabilitation eligible
        - **31-60**: Moderate concern - Borderline case
        - **61-80**: High concern - Strong indication of dealing
        - **81-100**: Very high - Law enforcement priority
        
        ---
        
        ### 🔬 **INTERPRETASI HASIL LAB**
        
        **Cut-off Values Standard:**
        - Metamfetamin: 1000 ng/mL
        - Morfin: 300 ng/mL
        - Kokain: 300 ng/mL
        - Amfetamin: 1000 ng/mL
        - Benzodiazepin: 300 ng/mL
        - THC: 50 ng/mL
        - MDMA: 500 ng/mL
        
        **Interpretasi Ratio:**
        - **< 0.5x cut-off**: Trace/Negatif
        - **0.5-1x**: Below cut-off (possible old use)
        - **1-3x**: Positive (recent use)
        - **3-10x**: Strong positive (heavy/frequent use)
        - **> 10x**: Very high (very recent/very heavy use)
        
        **Clinical Implications:**
        - Ratio > 10x: Monitor untuk withdrawal syndrome
        - Polisubstansi (≥3 zat): Komplikasi lebih kompleks
        - Nilai ekstrem: Pertimbangkan medical detox
        
        ---
        
        ### ⚖️ **DASAR HUKUM LENGKAP**
        
        #### **1. UU No. 35 Tahun 2009 tentang Narkotika**
        
        **Pasal 54:**
        "Pecandu Narkotika dan korban penyalahgunaan narkotika wajib menjalani rehabilitasi medis dan rehabilitasi sosial."
        
        **Pasal 103:**
        (1) Hakim yang memeriksa perkara Pecandu Narkotika dapat:
            a. memutus untuk memerintahkan yang bersangkutan menjalani pengobatan dan/atau perawatan melalui rehabilitasi jika Pecandu Narkotika tersebut terbukti bersalah melakukan tindak pidana Narkotika; atau
            b. menetapkan untuk memerintahkan yang bersangkutan menjalani pengobatan dan/atau perawatan melalui rehabilitasi jika Pecandu Narkotika tersebut tidak terbukti bersalah melakukan tindak pidana Narkotika.
        (2) Masa menjalani pengobatan dan/atau perawatan bagi Pecandu Narkotika sebagaimana dimaksud pada ayat (1) huruf a diperhitungkan sebagai masa menjalani hukuman.
        
        **Pasal 127:**
        (1) Setiap Penyalah Guna:
            a. Narkotika Golongan I bagi diri sendiri dipidana dengan pidana penjara paling lama 4 (empat) tahun;
        (2) Dalam memutus perkara sebagaimana dimaksud pada ayat (1), hakim wajib memperhatikan ketentuan sebagaimana dimaksud dalam Pasal 54, Pasal 55, dan Pasal 103.
        (3) Dalam hal Penyalah Guna sebagaimana dimaksud pada ayat (1) dapat dibuktikan atau terbukti sebagai korban penyalahgunaan Narkotika, Penyalah Guna tersebut wajib menjalani rehabilitasi medis dan rehabilitasi sosial.
        
        #### **2. SEMA No. 4 Tahun 2010**
        
        **Poin 3 - Kriteria Rehabilitasi:**
        Hakim dapat memerintahkan yang bersangkutan menjalani pengobatan dan/atau perawatan melalui rehabilitasi apabila terbukti:
        a. Terdakwa pada saat ditangkap oleh Penyidik Polri dan Penyidik BNN dalam kondisi tertangkap tangan
        b. Pada saat tertangkap tangan ditemukan barang bukti pemakaian 1 (satu) hari dengan perincian sebagai berikut:
           - Kelompok Methamphetamine (sabu) = 1 gram
           - Kelompok MDMA (ekstasi) = 2,4 gram (8 butir)
           - Kelompok Heroin = 1,8 gram
           - Kelompok Kokain = 1,8 gram
           - Kelompok Ganja = 5 gram
        c. Perlu surat uji laboratorium bahwa yang bersangkutan positif menggunakan narkotika berdasarkan permintaan penyidik
        d. Surat keterangan dari dokter jiwa/psikiater
        
        #### **3. Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014**
        
        **Pasal 5:**
        (1) Penanganan terhadap Pecandu Narkotika dan Korban Penyalahgunaan Narkotika dilakukan melalui mekanisme asesmen terpadu oleh Tim Asesmen Terpadu.
        
        **Pasal 8:**
        (1) Untuk melaksanakan Asesmen Terpadu sebagaimana dimaksud dalam Pasal 7, dibentuk Tim Asesmen Terpadu oleh instansi sebagaimana dimaksud dalam Pasal 1 angka 2, 3, 4, 5, 6, dan 7.
        (2) Tim Asesmen Terpadu sebagaimana dimaksud pada ayat (1) terdiri dari Tim Dokter dan Tim Hukum yang ditetapkan oleh pimpinan masing-masing instansi.
        
        #### **4. Perka BNN No. 11 Tahun 2014**
        
        **Pasal 7:**
        Asesmen terpadu dilaksanakan oleh Tim Asesmen Terpadu yang dibentuk oleh Kepala BNN.
        
        **Pasal 8:**
        (2) Biaya Pelaksanaan asesmen yang dilakukan oleh Tim Asesmen Terpadu dibebankan pada anggaran Badan Narkotika Nasional.
        
        ---
        
        ### ❓ **FAQ (Frequently Asked Questions)**
        
        **Q: Apakah sistem ini menggantikan Tim TAT?**
        A: **TIDAK**. Sistem ini adalah ALAT BANTU. Keputusan final tetap di tangan Tim TAT dan aparat penegak hukum.
        
        **Q: Mengapa ASSIST sekarang per substance, bukan total?**
        A: Karena itulah cara yang BENAR sesuai WHO guidelines. ASSIST menilai risiko PER ZAT, bukan total keseluruhan.
        
        **Q: Apa bedanya DSM-5 dan ICD-10?**
        A: DSM-5 adalah sistem diagnostik Amerika (11 kriteria), ICD-10 adalah sistem WHO internasional (6 kriteria, butuh ≥3 untuk dependence). Keduanya digunakan untuk validasi silang.
        
        **Q: Kenapa perlu ACEs assessment?**
        A: Trauma masa kecil (ACEs) adalah faktor risiko KUAT untuk addiction dan relapse. Semakin tinggi ACEs score, semakin tinggi risiko.
        
        **Q: Kapan C-SSRS harus dilakukan?**
        A: SELALU. Suicide risk assessment adalah MANDATORY untuk semua kasus addiction karena risiko suicide 6-20x lebih tinggi pada populasi addict.
        
        **Q: Jika C-SSRS Level 5 (high risk), apa yang harus dilakukan?**
        A: IMMEDIATE PSYCHIATRIC HOSPITALIZATION. Ini medical emergency. Hubungi psikiater on-call, implementasi suicide watch, remove means, notify family.
        
        **Q: Bagaimana jika barang bukti 3x gramatur tapi klien clearly dependent (DSM-5 severe)?**
        A: Ini BORDERLINE CASE. Perlu intensive TAT case conference. Sistem akan recommend "Proses Hukum + Rehabilitasi" atau "Rehabilitasi Rawat Inap" dengan catatan khusus.
        
        **Q: Apakah first offender otomatis eligible untuk rehabilitasi?**
        A: TIDAK otomatis. Masih harus memenuhi: (1) gramatur SEMA, (2) memang dependent/pecandu (confirmed by instruments), (3) bukan pengedar/bandar.
        
        **Q: Bagaimana dengan kasus injecting drug users (IDU)?**
        A: IDU adalah HIGH RISK (HIV, Hepatitis, endocarditis). Otomatis butuh medical screening lengkap dan intensive care. Rehabilitasi rawat inap strongly recommended.
        
        **Q: Apakah sistem bisa detect malingering (pura-pura pecandu)?**
        A: Sistem punya consistency checks. Tapi final judgment tetap pada klinisi yang berpengalaman. Malingering sulit dideteksi hanya dengan self-report instruments.
        
        **Q: Data disimpan dimana?**
        A: Sistem TIDAK menyimpan data di server. Data hanya di session browser. Export JSON untuk dokumentasi lokal sesuai SOP BNN.
        
        ---
        
        ### 💡 **TIPS & BEST PRACTICES**
        
        #### **Untuk Dokter/Psikolog:**
        - ✅ Lakukan rapport building sebelum assessment
        - ✅ Gunakan multiple informants (keluarga, teman) jika memungkinkan
        - ✅ Cross-check self-report dengan lab results
        - ✅ Perhatikan defensive responding atau minimization
        - ✅ Dokumentasi lengkap sangat penting
        - ✅ Jangan hanya rely pada sistem - gunakan clinical judgment
        
        #### **Untuk Penegak Hukum:**
        - ✅ Dokumentasi barang bukti dengan foto/video detail
        - ✅ Chain of custody harus jelas
        - ✅ Jika possible, witness penangkapan
        - ✅ Koordinasi erat dengan tim medis untuk assessment timing
        - ✅ Pahami perbedaan user vs dealer
        
        #### **Untuk Tim TAT:**
        - ✅ Case conference WAJIB untuk borderline/complex cases
        - ✅ Undang semua stakeholders
        - ✅ Dokumentasi reasoning untuk keputusan
        - ✅ Follow-up monitoring post-decision
        - ✅ Evaluasi efektivitas rehabilitasi secara berkala
        
        ---
        
        ### 📞 **KONTAK & SUPPORT**
        
        **Hotline BNN:** 184 (24 jam)  
        **Website:** https://bnn.go.id  
        **IPWL:** https://ipwl.bnn.go.id  
        **Email:** info@bnn.go.id
        
        **Untuk Technical Support Sistem:**  
        Hubungi Koordinator BNN Provinsi atau Tim IT BNN Pusat
        
        ---
        
        ### 📚 **REFERENSI ILMIAH**
        
        1. American Society of Addiction Medicine (ASAM). (2013). ASAM Criteria: Treatment Criteria for Addictive, Substance-Related, and Co-Occurring Conditions (3rd ed.).
        
        2. American Psychiatric Association. (2013). Diagnostic and Statistical Manual of Mental Disorders (5th ed.).
        
        3. World Health Organization. (2010). The Alcohol, Smoking and Substance Involvement Screening Test (ASSIST): Manual for use in primary care.
        
        4. Skinner, H. A. (1982). The Drug Abuse Screening Test (DAST-10). Addictive Behaviors, 7(4), 363-371.
        
        5. Felitti, V. J., et al. (1998). Relationship of childhood abuse and household dysfunction to many of the leading causes of death in adults: The Adverse Childhood Experiences (ACE) Study. American Journal of Preventive Medicine, 14(4), 245-258.
        
        6. Posner, K., et al. (2011). The Columbia-Suicide Severity Rating Scale: Initial validity and internal consistency findings. American Journal of Psychiatry, 168(12), 1266-1277.
        
        7. Prochaska, J. O., & DiClemente, C. C. (1983). Stages and processes of self-change of smoking: Toward an integrative model of change. Journal of Consulting and Clinical Psychology, 51(3), 390-395.
        
        ---
        
        <div class="success-box">
        <strong>✅ SISTEM READY TO USE</strong><br>
        Sistem TAT v3.0 COMPREHENSIVE ini telah terintegrasi dengan 10+ instrumen standar internasional dan fully compliant dengan regulasi BNN. Silakan gunakan untuk mendukung proses asesmen profesional Anda.
        </div>
        
        <div class="warning-box">
        <strong>⚠️ REMINDER:</strong><br>
        Sistem ini adalah ALAT BANTU, bukan pengganti penilaian klinis profesional. Keputusan final SELALU ada di tangan Tim Asesmen Terpadu yang terdiri dari profesional multidisiplin.
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# JALANKAN APLIKASI
# =============================================================================
if __name__ == "__main__":
    main()
