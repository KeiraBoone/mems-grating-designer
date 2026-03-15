import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import math
from datetime import datetime

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="MEMS Tunable Diffraction Grating Designer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔬 MEMS Tunable Diffraction Grating Designer")
st.markdown("Design and analysis tool for MEMS-actuated tunable diffraction gratings made for MIT class 6.2600/3.155: Micro/Nano Processing Technology, Spring 2026")

# ============================================================================
# MATERIAL PRESETS
# ============================================================================

MATERIAL_PRESETS = {
    "Silicon (Standard)": {
        "E": 170e9,
        "nu": 0.28,
        "rho": 2330,
        "sigma_yield": 1.0e9,
        "E_breakdown": 150e6,
        "description": "Standard single-crystal Si. Best for MEMS."
    },
    "Silicon (Polycrystalline)": {
        "E": 160e9,
        "nu": 0.27,
        "rho": 2320,
        "sigma_yield": 0.8e9,
        "E_breakdown": 130e6,
        "description": "PolysSi. Slightly softer than single-crystal."
    },
    "GaAs (Gallium Arsenide)": {
        "E": 85e9,
        "nu": 0.31,
        "rho": 5320,
        "sigma_yield": 0.4e9,
        "E_breakdown": 100e6,
        "description": "For integrated photonics applications."
    },
    "SiN (Silicon Nitride)": {
        "E": 250e9,
        "nu": 0.23,
        "rho": 3100,
        "sigma_yield": 1.5e9,
        "E_breakdown": 180e6,
        "description": "Stiffer, used for high-frequency MEMS."
    },
    "SiO₂ (Silicon Dioxide)": {
        "E": 72e9,
        "nu": 0.17,
        "rho": 2200,
        "sigma_yield": 0.1e9,
        "E_breakdown": 160e6,
        "description": "Very brittle. Not recommended for springs."
    },
    "Aluminum (Al)": {
        "E": 70e9,
        "nu": 0.33,
        "rho": 2700,
        "sigma_yield": 0.3e9,
        "E_breakdown": 60e6,
        "description": "Softer, sometimes used for contacts."
    },
}

# ============================================================================
# SIDEBAR - MATERIAL SELECTION
# ============================================================================

st.sidebar.header("⚙️ Material & Constants")
# --- Project metadata inputs ---
project_title = st.sidebar.text_input("Project Title", value="Tunable MEMS Diffraction Grating")
created_by = st.sidebar.text_input("Created by", value="Your Name / Team")
rendered_by = st.sidebar.text_input("Rendered by", value="MEMS Designer")
manual_summary = st.sidebar.text_area(
    "Manual Summary (for report export)",
    value="Enter your custom summary here…",
    height=120
)

material_choice = st.sidebar.selectbox(
    "Select Material",
    options=list(MATERIAL_PRESETS.keys()),
    help="Choose material for spring beams"
)

material = MATERIAL_PRESETS[material_choice]
st.sidebar.info(f"**{material_choice}**: {material['description']}")

with st.sidebar.expander("📝 Edit Material Properties", expanded=False):
    st.write("*Modify if using custom material*")


    E_silicon = st.number_input(
        "Young's Modulus E (GPa)",
        value=float(material["E"] / 1e9),
        min_value=10.0,
        max_value=500.0,
        step=10.0
    ) * 1e9

    nu_silicon = st.number_input(
        "Poisson's Ratio (ν)",
        value=float(material["nu"]),
        min_value=0.0,
        max_value=0.5,
        step=0.01
    )

    rho_silicon = st.number_input(
        "Density (kg/m³)",
        value=float(material["rho"]),
        min_value=500.0,
        max_value=10000.0,
        step=100.0
    )

    sigma_yield = st.number_input(
        "Yield Stress (MPa)",
        value=float(material["sigma_yield"] / 1e6),
        min_value=50.0,
        max_value=2000.0,
        step=50.0
    ) * 1e6

    E_breakdown = st.number_input(
        "E-Field Breakdown (MV/m)",
        value=float(material["E_breakdown"] / 1e6),
        min_value=30.0,
        max_value=300.0,
        step=10.0
    ) * 1e6

# Physical constants
epsilon_0 = 8.85e-12
mu_kinetic = 0.3

# ============================================================================
# SIDEBAR - DESIGN PARAMETERS (ALL EXPOSED)
# ============================================================================

st.sidebar.divider()
st.sidebar.header("⚙️ Design Parameters")

st.sidebar.subheader("1️⃣ Comb Drive")
n_fingers = st.sidebar.slider(
    "Comb finger pairs",
    min_value=10.0, max_value=1000.0, value=200.0, step=10.0,
    help="Number of interlocking finger pairs. More fingers = linearly more electrostatic force."
)
V_applied = st.sidebar.slider(
    "Applied voltage (V) - DC or AC Peak",
    min_value=10.0, max_value=150.0, value=15.0, step=5.0,
    help="Voltage applied across the comb drive. Force scales with the square of the voltage (V²)."
)
g_gap = st.sidebar.slider(
    "Gap between fingers (μm)",
    min_value=1.0, max_value=10.0, value=3.5, step=0.5,
    help="Distance between adjacent comb fingers. Instructor minimum is 3 μm to guarantee fabrication clearance. Smaller gaps drastically increase force."
)
comb_overlap = st.sidebar.slider(
    "Comb overlap length (μm)",
    min_value=5.0, max_value=200.0, value=20.0, step=5.0,
    help="The initial length that the fingers overlap. Determines baseline capacitance."
)
finger_width = st.sidebar.slider(
    "Comb finger width (μm)",
    min_value=1.0, max_value=10.0, value=3.0, step=0.5,
    help="Width of a single comb finger. Impacts layout area and stiffness of the fingers themselves."
)

st.sidebar.subheader("2️⃣ Device Body")
t_thickness = st.sidebar.slider(
    "Device thickness (μm)",
    min_value=5.0, max_value=100.0, value=50.0, step=5.0,
    help="Thickness of the SOI device layer. Thicker devices increase mass, force, and out-of-plane stiffness."
)
w_widest_moving = st.sidebar.slider(
    "Widest moving structure (μm)",
    min_value=5.0, max_value=100.0, value=20.0, step=1.0,
    help="Used to calculate BOE release time. The BOE must etch exactly half this distance to completely free the structure."
)
rho_mass = st.sidebar.slider(
    "Moving mass (mg)",
    min_value=0.001, max_value=20.0, value=1.0, step=0.001,
    help="Estimated mass of the central shuttle and grating. Lowers resonant frequency as it increases."
)

st.sidebar.subheader("3️⃣ Springs")
L_support = st.sidebar.slider(
    "Support beam length (μm)",
    min_value=20.0, max_value=500.0, value=200.0, step=10.0,
    help="Length of the flexures. Stiffness decreases cubically (1/L³) with length."
)
w_beam = st.sidebar.slider(
    "Support beam width (μm)",
    min_value=1.0, max_value=20.0, value=3.0, step=1.0,
    help="Width of the flexures. In-plane stiffness increases cubically (w³) with width."
)
n_springs = st.sidebar.slider(
    "Number of support springs",
    min_value=2.0, max_value=8.0, value=4.0, step=1.0,
    help="Total number of flexures holding the shuttle. Stiffness scales linearly with this number."
)
spring_boundary_condition = st.sidebar.selectbox(
    "Spring boundary condition",
    options=["Guided-End / Fixed-Fixed (Standard MEMS shuttle)", "Cantilever (Fixed-Free)"],
    index=0,
    help="Guided-end beams (like a crab-leg or folded flexure) are 4x stiffer than cantilevers of the same dimensions."
)
spring_bending_mode = st.sidebar.selectbox(
    "Spring bending mode",
    options=["In-plane bending (lateral comb drive)", "Out-of-plane bending"],
    index=0,
    help="Determines the area moment of inertia. In-plane uses (t*w³)/12, out-of-plane uses (w*t³)/12."
)

st.sidebar.subheader("4️⃣ Grating Geometry")
Lambda_pitch = st.sidebar.slider(
    "Grating pitch (μm)",
    min_value=1.0, max_value=20.0, value=10.0, step=1.0,
    help="The period of the grating (Λ). Instructor suggested < 12 μm to achieve larger, more easily measurable diffraction angles."
)
grating_side = st.sidebar.slider(
    "Grating side length (μm)",
    min_value=100.0, max_value=1000.0, value=500.0, step=50.0,
    help="Physical size of the grating square. Needs to be large enough to capture the entire laser spot."
)
pitch_change_factor = st.sidebar.slider(
    "Pitch change factor (ΔΛ / x)",
    min_value=0.0, max_value=0.2, value=0.01, step=0.005,
    help="Coupling ratio: how much the grating pitch changes per 1 μm of shuttle displacement."
)
duty_cycle = st.sidebar.slider(
    "Duty cycle (fill factor)",
    min_value=0.1, max_value=0.9, value=0.5, step=0.05,
    help="Ratio of the beam width to the total pitch length. 0.5 means equal line and space."
)

st.sidebar.subheader("5️⃣ Optical & Testing")
incidence_angle_deg = st.sidebar.slider(
    "Incidence angle (degrees)",
    min_value=0.0, max_value=89.0, value=0.0, step=1.0,
    help="Angle of the incoming laser relative to normal (0 = straight down)."
)
wavelength = st.sidebar.slider(
    "Target wavelength (nm)",
    min_value=400.0, max_value=2000.0, value=632.80, step=0.01,
    help="Wavelength of the test laser. 632 nm is standard for a red HeNe lab laser."
)
m_order = st.sidebar.selectbox(
    "Diffraction order to track", 
    options=[1, 2, 3],
    help="Which diffraction spot you are measuring. 1st order is usually the brightest."
)
detector_distance_cm = st.sidebar.slider(
    "Detector distance (cm)",
    min_value=0.5, max_value=200.0, value=10.0, step=0.5,
    help="Distance from the grating to the camera/screen where you are measuring the spots."
)
incident_power_mW = st.sidebar.slider(
    "Incident optical power (mW)",
    min_value=0.1, max_value=50.0, value=1.0, step=0.1,
    help="Power of your input laser. Used to calculate the optical power split between diffraction orders."
)
reflectivity = st.sidebar.slider(
    "Reflectivity factor",
    min_value=0.1, max_value=1.0, value=0.3, step=0.05,
    help="Percentage of light reflected by the device surface (e.g., bare silicon vs. aluminum coated)."
)

st.sidebar.subheader("6️⃣ Dynamics & Models")
Q_assumed = st.sidebar.slider(
    "Assumed quality factor Q",
    min_value=1.0, max_value=200.0, value=50.0, step=1.0,
    help="Sharpness of resonance. At resonant frequency, AC displacement is roughly Q times the static DC displacement."
)
modal_mass_factor = st.sidebar.slider(
    "Modal mass factor",
    min_value=0.1, max_value=1.0, value=1.0, step=0.01,
    help="Effective mass modifier. A perfectly rigid shuttle is 1.0, a simple cantilever tip is ~0.24."
)
comb_force_model = st.sidebar.selectbox(
    "Comb force model",
    options=["Lateral comb-drive (correct)", "Parallel-plate (reference)"],
    index=0,
    help="Lateral comb drive force is independent of displacement. Parallel plate force increases as the gap closes."
)
grating_equation_model = st.sidebar.selectbox(
    "Grating equation model",
    options=["Normal incidence", "Oblique incidence (sinθm = mλ/Λ - sinθi)"],
    index=0,
    help="Whether the laser hits the grating perfectly straight down (Normal) or at an angle (Oblique)."
)

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def calculate_spring_stiffness(E, w, t, L, n_springs):
    # In‑plane bending (lateral comb drive): I = t*w^3/12
    I = (t * w**3) / 12
    k_single = (3 * E * I) / (L**3)
    k_total = k_single * n_springs
    return k_total, k_single

def calculate_electrostatic_force(n, epsilon_0, t, V, g):
    t_m = t * 1e-6
    g_m = g * 1e-6
    return (n * epsilon_0 * t_m * V**2) / (2 * g_m)  # comb‑drive lateral force

def calculate_displacement(F_e, k):
    return F_e / k if k > 0 else 0

def calculate_resonant_frequency(k, m):
    if k <= 0 or m <= 0:
        return 0
    return (1 / (2 * np.pi)) * np.sqrt(k / (m * 1e-6))

def calculate_diffraction_angle(m, wavelength, Lambda, in_radians=False):
    sin_theta = (m * wavelength * 1e-9) / (Lambda * 1e-6)
    if sin_theta > 1.0:
        return None
    theta = np.arcsin(sin_theta)
    return theta if in_radians else np.degrees(theta)

def calculate_angular_dispersion(m, Lambda, wavelength):
    sin_theta = (m * wavelength * 1e-9) / (Lambda * 1e-6)
    if sin_theta >= 1:
        return 0
    cos_theta = np.sqrt(1 - sin_theta**2)
    return (m / ((Lambda * 1e-6) * cos_theta)) * 1e-9 * 1e6

def calculate_spectral_resolution(m, grating_side, Lambda):
    N_lines = int((grating_side * 1e-6) / (Lambda * 1e-6))
    return m * N_lines, N_lines

def calculate_efficiency_by_order(m, uniformity=0.95):
    base_efficiency = {0: 0.10, 1: 0.75, 2: 0.15, 3: 0.03}
    return base_efficiency.get(m, 0.01) * uniformity

def calculate_tuning_range(pitch_change_m, Lambda, wavelength):
    return (pitch_change_m / (Lambda * 1e-6)) * (wavelength * 1e-9) * 1e9

def calculate_voltage_for_target_displacement(target_x, k, n, epsilon_0, t, g):
    target_F = target_x * 1e-6 * k
    t_m = t * 1e-6
    g_m = g * 1e-6
    return np.sqrt((2 * target_F * g_m) / (n * epsilon_0 * t_m))

def calculate_stress_in_beam(F, w, t, L):
    # In‑plane bending: σ = 3 F L / (2 t w^2)
    return (3 * F * L) / (2 * t * w**2)

def calculate_fabrication_feasibility(g, L, w):
    issues = []
    recs = []
    if g < 0.5:
        issues.append("Gap < 0.5 μm: Not achievable with optical lithography")
    elif g < 1.5:
        issues.append("Gap < 1.5 μm: Very tight tolerances, high failure rate")
        recs.append("Consider e-beam lithography")
    elif g < 2.0:
        recs.append("Gap near lower limit; tight process control needed")
    if w < 1.0:
        issues.append("Beam width < 1 μm: Will collapse during fabrication")
    elif w < 2.0:
        recs.append("Beam width tight; careful DRIE profile needed")
    if L > 300:
        recs.append("Beam length > 300 μm: May need serpentine routing")
    return issues, recs

# Unit-converted helpers for step-by-step math
w_beam_m = w_beam * 1e-6
t_thickness_m = t_thickness * 1e-6
L_support_m = L_support * 1e-6
g_gap_m = g_gap * 1e-6
lambda_m = wavelength * 1e-9
Lambda_m = Lambda_pitch * 1e-6

# ============================================================================
# CALCULATIONS (COMPREHENSIVE + ACCURATE)
# Replace your entire CALCULATIONS block with this.
# ============================================================================

# ---- 0) Unit conversions ----
w_beam_m = w_beam * 1e-6
t_thickness_m = t_thickness * 1e-6
L_support_m = L_support * 1e-6
g_gap_m = g_gap * 1e-6

lambda_m = wavelength * 1e-9
Lambda_m = Lambda_pitch * 1e-6
grating_side_m = grating_side * 1e-6



comb_overlap_m = comb_overlap * 1e-6
finger_width_m = finger_width * 1e-6

m_mass_kg = rho_mass * 1e-6
m_eff = modal_mass_factor * m_mass_kg

theta_i = np.deg2rad(incidence_angle_deg)
detector_distance_m = detector_distance_cm / 100.0

# ---- 1) Spring stiffness (equation version depends on bending axis) ----
# k_single = 3 E I / L^3
if spring_bending_mode == "In-plane bending (lateral comb drive)":
    # I = t w^3 / 12
    I_beam = (t_thickness_m * w_beam_m**3) / 12.0
    k_single = (3.0 * E_silicon * I_beam) / (L_support_m**3)
    k_eq_used = "k_single = (3 E t w^3)/(4 L^3)  [in-plane bending]"
else:
    # I = w t^3 / 12
    I_beam = (w_beam_m * t_thickness_m**3) / 12.0
    k_single = (3.0 * E_silicon * I_beam) / (L_support_m**3)
    k_eq_used = "k_single = (3 E w t^3)/(4 L^3)  [out-of-plane bending]"
k_total = k_single * n_springs
compliance = 1.0 / k_total if k_total > 0 else np.inf

# ---- 2) Comb-drive force (equation version selectable) ----
if comb_force_model == "Lateral comb-drive (correct)":
    # Lateral comb-drive: F = (n ε0 t V^2)/(2 g)
    F_elec = (n_fingers * epsilon_0 * t_thickness_m * V_applied**2) / (2.0 * g_gap_m)
    comb_eq_used = "F = (n ε0 t V^2)/(2 g)  [lateral comb]"
else:
    # Parallel-plate reference: F = ε0 A V^2 / (2 g^2), A≈n t overlap
    A_plate = n_fingers * t_thickness_m * comb_overlap_m
    F_elec = (epsilon_0 * A_plate * V_applied**2) / (2.0 * g_gap_m**2)
    comb_eq_used = "F = (ε0 A V^2)/(2 g^2)  [parallel-plate ref]"

# ---- 3) Static displacement ----
# x = F / k
# x_disp = F_elec / k_total if k_total > 0 else 0.0

# ---- 3) Static displacement & AC Resonance ----
# x = F / k
x_disp_DC = F_elec / k_total if k_total > 0 else 0.0
x_disp_AC_res = x_disp_DC * Q_assumed  # AC drive at resonance amplifies displacement by Q

# ---- 4) Resonance + damping ----
# f = (1/2π)*sqrt(k/m_eff)
f_res = (1.0/(2.0*np.pi)) * np.sqrt(k_total/m_eff) if (m_eff > 0) else 0.0
omega_n = 2.0 * np.pi * f_res
zeta = 1.0/(2.0*Q_assumed) if Q_assumed > 0 else 0.0
bandwidth = f_res/Q_assumed if Q_assumed > 0 else 0.0
c_damping = 2.0 * zeta * np.sqrt(k_total * m_eff) if (k_total > 0 and m_eff > 0) else 0.0

# ---- 5) Electric field ----
# E = V/g ; in V/μm = MV/m
E_field_MVm = V_applied / g_gap if g_gap > 0 else np.inf

# ---- 6) Stress / strain / safety factor (per beam) ----
F_per_beam = F_elec / n_springs
if spring_bending_mode == "In-plane bending (lateral comb drive)":
    # σ = 3 F L / (2 t w^2)
    stress_beam = (3.0 * F_per_beam * L_support_m) / (2.0 * t_thickness_m * w_beam_m**2)
    stress_eq_used = "σ = 3 F L / (2 t w^2)  [in-plane]"
else:
    # σ = 3 F L / (2 w t^2)
    stress_beam = (3.0 * F_per_beam * L_support_m) / (2.0 * w_beam_m * t_thickness_m**2)
    stress_eq_used = "σ = 3 F L / (2 w t^2)  [out-of-plane]"

stress_ratio = stress_beam / sigma_yield if sigma_yield > 0 else np.inf
safety_factor = sigma_yield / stress_beam if stress_beam > 0 else np.inf
strain_max = stress_beam / E_silicon if E_silicon > 0 else 0.0

# ---- 7) Yield limit (force + displacement) ----
if spring_bending_mode == "In-plane bending (lateral comb drive)":
    F_yield_per = (2.0 * t_thickness_m * w_beam_m**2 * sigma_yield) / (3.0 * L_support_m)
else:
    F_yield_per = (2.0 * w_beam_m * t_thickness_m**2 * sigma_yield) / (3.0 * L_support_m)
F_yield_total = F_yield_per * n_springs
x_yield = F_yield_total / k_total if k_total > 0 else np.inf

# ---- 8) Mechanical energy stored (Static DC) ----
# U = 1/2 k x^2
U_spring = 0.5 * k_total * x_disp_DC**2

# ---- 9) Capacitance + electrical energy ----
# C = n ε0 t L_ov / g
C_comb = (n_fingers * epsilon_0 * t_thickness_m * comb_overlap_m) / g_gap_m if g_gap_m > 0 else np.inf
Q_charge = C_comb * V_applied
U_elec = 0.5 * C_comb * V_applied**2

# ---- 10) Voltage required for target displacement (2 μm default) ----
V_for_2um = np.sqrt((2 * k_total * 2e-6 * g_gap_m) / (n_fingers * epsilon_0 * t_thickness_m)) if (n_fingers > 0) else np.inf

# ---- 11) Optical: diffraction angles ----
def calc_theta(m):
    if grating_equation_model == "Normal incidence":
        s = (m * lambda_m) / Lambda_m
    else:
        s = (m * lambda_m) / Lambda_m - np.sin(theta_i)
    if s > 1 or s < -1:
        return None
    return np.arcsin(s)

theta_by_order = {m: calc_theta(m) for m in [0, 1, 2, 3]}
theta_target = theta_by_order[m_order]
theta_target_deg = np.degrees(theta_target) if theta_target is not None else None

# ---- 12) Angular dispersion ----
# dθ/dλ = m/(Λ cosθ)
dtheta_dlambda_rad = (m_order / (Lambda_m * np.cos(theta_target))) if theta_target is not None else 0.0
dtheta_dlambda_urad_nm = dtheta_dlambda_rad * 1e-9 * 1e6

# ---- 13) Detector spot positions ----
def spot_pos(theta):
    return detector_distance_m * np.tan(theta) if theta is not None else None

spot_positions = {m: spot_pos(theta_by_order[m]) for m in [0,1,2,3]}
spot_sep_01 = (spot_positions[1] - spot_positions[0]) if (spot_positions[1] is not None) else None

# ---- 14) Pitch tuning / wavelength tuning (Using AC Resonance for maximum observable shift) ----
pitch_change_m = x_disp_AC_res * pitch_change_factor
pitch_change_nm = pitch_change_m * 1e9
new_pitch_m = Lambda_m - pitch_change_m
delta_lambda_nm = (pitch_change_m / Lambda_m) * lambda_m * 1e9 if Lambda_m > 0 else 0.0

theta_new = calc_theta(m_order) if new_pitch_m > 0 else None
angle_shift_urad = (theta_new - theta_target) * 1e6 if (theta_new is not None and theta_target is not None) else 0.0

# ---- 15) Resolution ----
N_lines = int(grating_side_m / Lambda_m) if Lambda_m > 0 else 0
R = m_order * N_lines
delta_lambda_min_nm = wavelength / R if R > 0 else np.inf

# ---- 16) Efficiency & power split (binary grating model) ----
def eta(m):
    if m == 0:
        return duty_cycle**2
    return (np.sin(m*np.pi*duty_cycle)/(m*np.pi))**2

eff_m0 = 100 * eta(0) * reflectivity
eff_m1 = 100 * eta(1) * reflectivity
eff_m2 = 100 * eta(2) * reflectivity
eff_m3 = 100 * eta(3) * reflectivity
eff_accounted = eff_m0 + eff_m1 + eff_m2 + eff_m3
eff_loss = max(0, 100 - eff_accounted)

P0 = incident_power_mW * (eff_m0/100)
P1 = incident_power_mW * (eff_m1/100)
P2 = incident_power_mW * (eff_m2/100)
P3 = incident_power_mW * (eff_m3/100)

# ---- 17) Fabrication checks ----
fab_issues, fab_recommendations = calculate_fabrication_feasibility(g_gap, L_support, w_beam)

# ============================================================================
# TOP METRICS
# ============================================================================

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Spring Stiffness", f"{k_total:.2f} N/m", f"({k_single:.2f} each)")
with col2:
    st.metric("Resonant Frequency", f"{f_res:.1f} Hz")
with col3:
    st.metric(f"Static DC Disp. (@ {V_applied:.0f}V)", f"{x_disp_DC*1e6:.3f} μm")
with col4:
    st.metric(f"AC Resonant Blur (@ {V_applied:.0f}V)", f"{x_disp_AC_res*1e6:.2f} μm", "Used for optics")

st.divider()

# ============================================================================
# SIMPLE TABS (MECH / OPTICAL / ELECTRICAL / FABRICATION / VALIDATION / SUMMARY)
# ============================================================================

# ============================================================================
# TABS 0–3 (FULL, EXPANDED)
# ============================================================================

tabs = st.tabs([
    "Mechanical",
    "Optical",
    "Electrical",
    "Fabrication",
    "Validation",
    "Summary",
    "Design Solver",
    "Beam & Measurement",
    "Sensitivity & Error Budget",
    "Gaussian Beam Optics"
])

# -------------------------
# TAB 0: Mechanical
# -------------------------
with tabs[0]:
    st.header("Mechanical — Full Model, All Work")

    st.subheader("1) Spring stiffness")
    st.latex(r"k_{single}=\frac{3EI}{L^3}")
    if spring_bending_mode == "In-plane bending (lateral comb drive)":
        st.latex(r"I=\frac{t w^3}{12}\;\Rightarrow\;k_{single}=\frac{3E t w^3}{4L^3}")
    else:
        st.latex(r"I=\frac{w t^3}{12}\;\Rightarrow\;k_{single}=\frac{3E w t^3}{4L^3}")

    st.expander("Variables + design knobs", expanded=False).markdown("""
**Variables** - **E**: Young’s modulus (Pa)  
- **w**: beam width (m)  
- **t**: beam thickness (m)  
- **L**: beam length (m)  
- **I**: area moment of inertia (m⁴)  
- **k_single**: stiffness of one beam (N/m)  
- **k_total**: stiffness of all springs in parallel (N/m)

**Design knobs** - Increase **L** → stiffness drops as **1/L³** - Increase **w** → stiffness rises as **w³** (in‑plane)  
- Increase **t** → stiffness rises (linear in‑plane, cubic out‑of‑plane)  
- Increase **# springs** → stiffness rises linearly  
    """)

    st.expander("Show all work (stiffness)", expanded=False).code(f"""
Mode: {spring_bending_mode}
E = {E_silicon:.3e} Pa
w = {w_beam_m:.3e} m
t = {t_thickness_m:.3e} m
L = {L_support_m:.3e} m
I = {I_beam:.3e} m^4

k_single = 3 E I / L^3
= 3*{E_silicon:.3e}*{I_beam:.3e} / ({L_support_m:.3e})^3
= {k_single:.3e} N/m

k_total = k_single * n_springs
= {k_single:.3e} * {n_springs:.0f}
= {k_total:.3e} N/m

Equation: {k_eq_used}
    """)

    st.subheader("2) Static & Dynamic Displacement")
    st.latex(r"x = \frac{F}{k}")

    st.expander("Show all work (displacement)", expanded=False).code(f"""
F = {F_elec:.3e} N
k = {k_total:.3e} N/m

--- Static DC ---
x_DC = F/k = {x_disp_DC:.3e} m = {x_disp_DC*1e6:.3f} μm

--- AC Resonance ---
Q_assumed = {Q_assumed}
x_AC = x_DC * Q = {x_disp_AC_res:.3e} m = {x_disp_AC_res*1e6:.3f} μm
    """)

    st.subheader("3) Resonant frequency + damping")
    st.latex(r"f = \frac{1}{2\pi}\sqrt{\frac{k}{m_{eff}}}")
    st.latex(r"\zeta=\frac{1}{2Q},\quad BW=\frac{f}{Q}")

    st.expander("Show all work (frequency & damping)", expanded=False).code(f"""
m_eff = {m_eff:.3e} kg
f = (1/2π)*sqrt(k/m_eff)
= (1/2π)*sqrt({k_total:.3e}/{m_eff:.3e})
= {f_res:.3f} Hz

ω = 2πf = {omega_n:.3f} rad/s
Q = {Q_assumed:.1f}
ζ = 1/(2Q) = {zeta:.4f}
Bandwidth = f/Q = {bandwidth:.3f} Hz
c = 2ζ√(km) = {c_damping:.3e} Ns/m
    """)

    st.subheader("4) Stress / strain / safety factor")
    if spring_bending_mode == "In-plane bending (lateral comb drive)":
        st.latex(r"\sigma=\frac{3FL}{2tw^2}")
    else:
        st.latex(r"\sigma=\frac{3FL}{2wt^2}")
    st.latex(r"\varepsilon=\sigma/E")

    st.expander("Show all work (stress)", expanded=False).code(f"""
F_per_beam = {F_per_beam:.3e} N
σ = {stress_beam:.3e} Pa = {stress_beam/1e6:.2f} MPa
σ_yield = {sigma_yield/1e6:.1f} MPa
σ/σ_yield = {stress_ratio:.3e} ({stress_ratio*100:.2f}%)
Safety factor = {safety_factor:.2f}
Strain = σ/E = {strain_max:.3e}
Equation: {stress_eq_used}
    """)

    st.subheader("5) Yield limits + stored energy")
    st.latex(r"U=\frac{1}{2}kx^2")

    st.expander("Show all work (yield + energy)", expanded=False).code(f"""
F_yield_per = {F_yield_per:.3e} N
F_yield_total = {F_yield_total:.3e} N
x_yield = F_yield_total/k_total = {x_yield:.3e} m = {x_yield*1e6:.2f} μm
U_spring = 0.5*k*x^2 = {U_spring:.3e} J
    """)

# -------------------------
# TAB 1: Optical
# -------------------------
with tabs[1]:
    st.header("Optical — Full Model, All Work")

    st.subheader("1) Grating equation")
    if grating_equation_model == "Normal incidence":
        st.latex(r"m\lambda=\Lambda\sin\theta_m")
    else:
        st.latex(r"\sin\theta_m=\frac{m\lambda}{\Lambda}-\sin\theta_i")

    st.expander("Variables + design knobs", expanded=False).markdown("""
**Variables**  
- **m**: diffraction order  
- **λ**: wavelength  
- **Λ**: grating pitch  
- **θi**: incident angle  
- **θm**: diffraction angle  

**Design knobs**  
- Λ ↓ → larger angles, higher dispersion  
- m ↑ → higher order angles (if order exists)  
- θi ≠ 0 shifts all order angles  
    """)

    st.expander("Show all work (angles)", expanded=False).code(
        "\n".join([f"m={m}: θ={np.degrees(theta_by_order[m]):.4f}°" if theta_by_order[m] is not None else f"m={m}: order does not exist"
                   for m in [0,1,2,3]])
    )

    st.subheader("2) Angular dispersion")
    st.latex(r"\frac{d\theta}{d\lambda}=\frac{m}{\Lambda\cos\theta}")
    st.expander("Show all work (dispersion)", expanded=False).code(f"""
dθ/dλ = {dtheta_dlambda_rad:.3e} rad/m
= {dtheta_dlambda_urad_nm:.2f} μrad/nm
    """)

    st.subheader("3) Detector spot positions")
    st.expander("Show all work (spot positions)", expanded=False).code(
        "\n".join([f"m={m}: x={spot_positions[m]:.6e} m" if spot_positions[m] is not None else f"m={m}: no spot"
                   for m in [0,1,2,3]])
    )
    if spot_sep_01 is not None:
        st.write(f"Separation between m=0 and m=1: {spot_sep_01*1e6:.2f} μm")

    st.subheader("4) Pitch tuning + wavelength tuning")
    st.latex(r"\Delta\Lambda=x_{AC}\alpha,\quad \Delta\lambda\approx(\Delta\Lambda/\Lambda)\lambda")
    st.expander("Show all work (tuning)", expanded=False).code(f"""
x_AC = {x_disp_AC_res:.3e} m
α = {pitch_change_factor:.4f}
ΔΛ = x_AC * α = {pitch_change_nm:.2f} nm
Δλ = (ΔΛ/Λ) * λ = {delta_lambda_nm:.4f} nm
Δθ = {angle_shift_urad:.2f} μrad
    """)

    st.subheader("5) Resolution")
    st.latex(r"R=mN,\quad \Delta\lambda_{min}=\lambda/R")
    st.expander("Show all work (resolution)", expanded=False).code(f"""
N = {N_lines}
R = {R}
Δλ_min = {delta_lambda_min_nm:.4f} nm
    """)

    st.subheader("6) Efficiency + power split (binary grating)")
    st.write(f"η0={eff_m0:.2f}% | η1={eff_m1:.2f}% | η2={eff_m2:.2f}% | η3={eff_m3:.2f}%")
    st.write(f"P0={P0:.2f} mW | P1={P1:.2f} mW | P2={P2:.2f} mW | P3={P3:.2f} mW")

# -------------------------
# TAB 2: Mechanics & Dynamics
# -------------------------
with tabs[2]:
    st.header("Mechanics & Dynamics")
    
    st.markdown("### 1. Electrostatic Actuation (Comb Drive)")
    st.markdown("The lateral force generated by a comb drive is independent of the displacement (until the fingers bottom out). It depends on the number of finger pairs, the gap, the structural thickness, and the square of the applied voltage.")
    st.latex(r"F_{elec} = n \frac{\epsilon_0 t}{g} V^2")
    st.markdown(f"**Calculated Force:** {F_elec * 1e6:.2f} μN (at {V_applied} V)")
    
    st.markdown("### 2. Spring Restoring Force")
    if "Guided-End" in spring_boundary_condition:
        st.markdown("For a guided-end (fixed-fixed shuttle) beam, the stiffness per beam is:")
        if "In-plane" in spring_bending_mode:
            st.latex(r"k = \frac{12 E I}{L^3} = \frac{E t w^3}{L^3}")
        else:
            st.latex(r"k = \frac{12 E I}{L^3} = \frac{E w t^3}{L^3}")
    else:
        st.markdown("For a cantilever (fixed-free) beam, the stiffness per beam is:")
        if "In-plane" in spring_bending_mode:
            st.latex(r"k = \frac{3 E I}{L^3} = \frac{E t w^3}{4 L^3}")
        else:
            st.latex(r"k = \frac{3 E I}{L^3} = \frac{E w t^3}{4 L^3}")
            
    st.markdown(f"**Total Stiffness ($k_{{total}}$):** {k_total:.2f} N/m (across {n_springs} springs)")
    
    st.markdown("### 3. Static vs. Dynamic Displacement")
    st.markdown("Static DC displacement is simply Hooke's Law ($x = F/k$). However, as noted in the design review, this static displacement is often too small to resolve optically. By driving the comb drive with an AC signal at the system's resonant frequency, the displacement is amplified by the quality factor ($Q$).")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Static (DC) Displacement:**\n\n**{x_disp_DC * 1e6:.3f} μm**")
    with col2:
        st.success(f"**Resonant (AC) Displacement:**\n\n**{x_disp_AC_res * 1e6:.3f} μm** (assuming Q={Q_assumed})")
        
    st.markdown("### 4. Resonant Frequency")
    st.latex(r"f_0 = \frac{1}{2\pi} \sqrt{\frac{k_{total}}{m_{eff}}}")
    st.markdown(f"**Calculated Resonance:** {f_res:.1f} Hz (using {rho_mass} mg mass)")


# -------------------------
# TAB 3: Fabrication & Layout Constraints
# -------------------------
with tabs[3]:
    st.header("Fabrication & KLayout Constraints")
    st.markdown("This section translates the physical dimensions into actionable layout rules, specifically addressing the instructors' concerns regarding the BOE release and structural stiction.")
    
    st.subheader("1. BOE Etch Time & Anchor Underetch")
    st.markdown("To fully release the moving structures from the underlying oxide layer, the BOE (Buffered Oxide Etch) must penetrate under the widest suspended feature. However, this same etch will simultaneously attack the oxide under your fixed anchors.")
    
    st.latex(r"d_{release} = \frac{w_{widest}}{2}")
    st.latex(r"t_{etch} = d_{release} \times 15 \text{ min/}\mu\text{m}")
    st.latex(r"w_{anchor\_min} > 2 \times d_{release} + w_{safety}")
    
    # Calculations
    boe_etch_rate = 15.0 # minutes per micron
    release_distance = w_widest_moving / 2.0
    boe_time_mins = release_distance * boe_etch_rate
    anchor_minimum_size = (release_distance * 2) + 10.0 # 10um safety margin
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Required Release Etch:**\n\nDistance: **{release_distance:.1f} μm**\nTime: **{boe_time_mins:.1f} minutes**")
    with col2:
        st.warning(f"**Minimum Anchor Size:**\n\nMust be **> {anchor_minimum_size:.1f} μm** wide to survive the {boe_time_mins:.1f} min etch.")
    
    st.markdown("---")
    
    st.subheader("2. Stiction & Stress Mitigation")
    st.markdown("""
    **Instructor Feedback:** *"A lot of suspended stuff with the whole interferometer and comb drive... if there is any stress built into the device layer or wafer this whole thing could collapse and stick to the bottom."*
    """)
    st.markdown("""
    * **Collapse Risk:** The 500 μm grating is massive. If the restoring force of the springs is too weak in the *out-of-plane* direction, capillary forces during drying or built-in compressive stress could snap the grating down to the substrate.
    * **Corner Rounding:** Sharp 90° corners on the support springs will act as stress concentrators, drastically increasing the chance of fracture during release or AC resonance. **Fillet all inside corners** in KLayout.
    """)
    
    st.markdown("---")
    
    st.subheader("3. GDS Layout Checklist")
    st.markdown("Before exporting your final `.gds` file for the multiproject chip, verify the following:")
    
    st.checkbox(f"**Minimum Feature Size:** Comb gaps are ≥ 3 μm (Currently set to {g_gap} μm).", value=(g_gap >= 3.0))
    st.checkbox(f"**Anchor Survival:** All fixed pads/anchors are > {anchor_minimum_size:.1f} μm in width/length.")
    st.checkbox("**Backup Structures Included:** Placed standalone, simpler comb-drives alongside the main device so you still have measurable data if the massive grating collapses.")
    st.checkbox("**Measurement Pads:** Sized appropriately for probe needles (e.g., 100x100 μm) and spaced far enough apart.")


# -------------------------
# TAB 4: Validation / Test Mapping (Detailed)
# -------------------------
with tabs[4]:
    st.header("Validation / Test Mapping (Detailed)")
    st.markdown("""
    This section provides a comprehensive roadmap for testing the fabricated MEMS device, directly addressing the feedback from the project pitch design review. It outlines the specific equipment needed, the physical limitations of static testing, and the specific setups for dynamic and optical verification.
    """)

st.divider()

    # --- A) SEM Metrology ---
st.subheader("A) SEM / Dimensional Metrology")
    # ADDED 'r' HERE
st.markdown(r"""
    **Goal:** Verify that the fabricated geometry strictly matches the KLayout GDS design dimensions ($g, w, L, \Lambda$) and assess fabrication defects.
    
    **Why it matters:** Electrostatic force is inversely proportional to the gap ($F \propto 1/g$), and spring stiffness is inversely proportional to the cube of the length ($k \propto 1/L^3$). Even a 0.5 μm overetch during the DRIE process will drastically lower the resonant frequency and increase the required driving voltage. Furthermore, because of the massive 500 μm grating, we must inspect the device for stiction (where the structure collapses and bonds to the substrate due to capillary forces after the BOE wet etch).
    """)

st.expander("What to measure (SEM Checklist)", expanded=False).markdown(r"""
    - **Comb gap ($g$):** Verify it meets the $\geq$ 3 μm limit set by instructors.
    - **Beam width ($w$) & length ($L$):** Crucial for back-calculating true stiffness.
    - **Grating pitch ($\Lambda$):** Check for uniform duty cycle and exact period.
    - **Anchor Undercut:** Measure the oxide remaining under the anchors to verify the 15 min/μm BOE etch calculations.
    - **Sidewall Profile:** Look for verticality. Slanted sidewalls induce out-of-plane forces in lateral comb drives.
    - **Stiction Check:** Tilt the SEM stage to verify the main grating shuttle is fully suspended.
    """)

    # --- B) Static Displacement ---
st.subheader("B) Static Displacement Test (Limitations)")
st.latex(r"x(V)=\frac{F(V)}{k} = \left( n \frac{\epsilon_0 t}{g} V^2 \right) \frac{1}{k}")
    # ADDED 'r' HERE
st.markdown(r"""
    **Method:** Land probe needles on the anchor pads using a standard probe station. Apply a DC voltage in step increments using a DC power supply and measure the displacement under an optical microscope.
    
    **Instructor Note & Physical Limits:** As brought up in the pitch review, standard static DC displacement is often sub-micron. The Abbe diffraction limit of a standard optical microscope restricts resolution to roughly $\sim 0.2$ μm under visible light. Therefore, *you likely will not be able to see the comb drive move under DC bias*. This test serves merely to verify electrical continuity (no shorts) before moving to dynamic testing.
    """)

st.expander("Prediction from current design", expanded=False).code(f"""
x_DC = F/k
F = {F_elec:.3e} N at V={V_applied:.0f} V
k = {k_total:.3e} N/m
x_DC = {x_disp_DC:.3e} m = {x_disp_DC*1e6:.3f} μm (Likely below optical resolution)
    """)

    # --- C) Optical Diffraction ---
st.subheader("C) Optical Diffraction Test")
st.latex(r"m\lambda = \Lambda \sin(\theta_m)")
   # ADDED 'r' HERE
st.markdown(r"""
    **Method & Setup:** 1. Mount the MEMS chip vertically on an optical breadboard in a darkroom.
    2. Pass a HeNe laser ($\lambda$ = 632.8 nm) through a focusing lens (calculated focal length from Tab 7) so the beam waist is entirely contained within the 500 μm grating, avoiding diffraction from the substrate edges.
    3. Project the diffracted beams onto a screen or wall at a known, large distance ($L_{screen}$).
    4. Measure the physical distance ($y$) between the 0th-order (center) and 1st-order spots to calculate the baseline angle: \tan(\theta) = y / L_{screen}.
    5. As voltage is applied, track the change in $y$ to calculate the tuning angle \Delta \theta(V).
    """)

st.expander("Predicted diffraction angle & tuning", expanded=False).code(f"""
λ = {wavelength:.1f} nm
Λ = {Lambda_pitch:.2f} μm
m = {m_order}

θ = {theta_target_deg:.4f}° (baseline)
Δθ (Static DC) = {angle_shift_urad:.2f} μrad 
Δθ (AC Resonance) = {angle_shift_urad * Q_assumed:.2f} μrad (Maximum expected shift)
    """)

    # --- D) Dynamic / Resonance ---
st.subheader("D) Dynamic / Resonance Test (Primary Method)")
st.latex(r"f_0=\frac{1}{2\pi}\sqrt{\frac{k}{m_{eff}}}")
    # ADDED 'r' HERE
st.markdown(r"""
    **Method & Setup:** To overcome the visual limitations of the static test, we will drive the comb using a signal generator borrowed from the optics lab. 
    1. Apply an AC voltage combined with a DC bias ($V = V_{dc} + V_{ac}\sin(\omega t)$). The DC bias is required to prevent frequency doubling, as electrostatic force scales with $V^2$.
    2. Sweep the driving frequency near the calculated resonance.
    3. Observe the comb fingers or grating edges under the microscope. At resonance, the displacement is multiplied by the quality factor ($Q$), creating a wide, visible "blur" representing the peak-to-peak amplitude.
    4. Record the frequency where the blur is widest to determine the true $f_0$. This allows us to back-calculate the actual spring stiffness and mass.
    """)

bandwidth = f_res / Q_assumed if Q_assumed > 0 else 0.0
    
st.expander("Predicted resonance & Visual Blur", expanded=False).code(f"""
f_res = {f_res:.2f} Hz
Q_assumed = {Q_assumed:.1f} (in air)
Bandwidth ≈ f_res/Q = {bandwidth:.2f} Hz

Peak-to-Peak Visual Blur (2 * x_AC) = {(x_disp_AC_res * 1e6) * 2:.3f} μm
*This width should be easily resolvable under the microscope*
    """)


# -------------------------
# TAB 5: Summary
# -------------------------
with tabs[5]:
    st.header("Summary (Auto‑Generated + Manual)")
    st.markdown("Use this tab as the high-level executive summary for your final 6.2600 report.")

    st.subheader("Project Metadata")
    st.write(f"**Project:** {project_title}")
    st.write(f"**Created by:** {created_by}")
    st.write(f"**Rendered by:** {rendered_by}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Key Mechanical Results")
        st.markdown(f"""
        - **Spring model:** {k_eq_used}
        - **Total stiffness ($k_{{total}}$):** {k_total:.2f} N/m
        - **Electrostatic force ($F_{{elec}}$):** {F_elec*1e6:.2f} μN (at {V_applied} V)
        - **Static DC Displacement:** {x_disp_DC*1e6:.3f} μm *(Baseline)*
        - **AC Resonant Displacement:** {x_disp_AC_res*1e6:.3f} μm *(Assuming Q={Q_assumed})*
        - **Resonant Frequency ($f_0$):** {f_res:.2f} Hz
        - **Max Stress ($\sigma_{{max}}$):** {stress_beam/1e6:.2f} MPa
        - **Safety Factor:** {safety_factor:.2f}
        """)

    with col2:
        st.subheader("Key Optical Results")
        st.markdown(f"""
        - **Grating pitch ($\Lambda$):** {Lambda_pitch:.2f} μm
        - **Wavelength ($\lambda$):** {wavelength:.1f} nm
        - **Tracked Order ($m$):** {m_order}
        - **Baseline Angle ($\theta$):** {theta_target_deg:.4f}°
        - **Tuning Shift ($\Delta\theta$):** {angle_shift_urad * Q_assumed:.2f} μrad *(At AC Resonance)*
        - **Wavelength Shift ($\Delta\lambda$):** {delta_lambda_nm:.4f} nm
        - **Resolving Power ($R$):** {R}
        - **Min Resolvable ($\Delta\lambda_{{min}}$):** {delta_lambda_min_nm:.4f} nm
        - **Order {m_order} Efficiency ($\eta_{m_order}$):** {eff_m1:.2f}% ({P1:.2f} mW)
        """)

    st.divider()
    
    st.subheader("Fabrication & Testing Quick Look")
    st.markdown(f"""
    - **Minimum BOE Release Etch:** {(w_widest_moving / 2.0):.1f} μm (Approx. {(w_widest_moving / 2.0) * 15.0:.1f} mins)
    - **Minimum Safe Anchor Size:** {((w_widest_moving / 2.0) * 2) + 10.0:.1f} μm
    - **Optical Measurement:** Camera must resolve **> {angle_shift_urad * Q_assumed:.2f} μrad** to detect the resonant blur.
    """)

    st.subheader("Manual Summary (Editable)")
    st.text_area("Final Summary Block (Write your report abstract/conclusion here)", value=manual_summary, height=200)


# -------------------------
# TAB 6: Design Solver
# -------------------------
with tabs[6]:
    st.header("Design Solver (Inverse Design)")

    st.subheader("Choose target outputs")
    target_f = st.number_input("Target resonance f (Hz)", value=float(max(100.0, f_res)), step=100.0)
    target_x = st.number_input("Target displacement x (μm)", value=2.0, step=0.1)
    available_V = st.number_input("Available voltage (V)", value=float(V_applied), step=5.0)

    # Required stiffness for target f
    k_req = (2*np.pi*target_f)**2 * m_eff

    # Required force for target x
    F_req = k_req * (target_x*1e-6)

    # Required voltage for target x given current geometry
    V_req = np.sqrt((2 * F_req * g_gap_m) / (n_fingers * epsilon_0 * t_thickness_m))

    # Required number of fingers for target x at available V
    n_req = (2 * F_req * g_gap_m) / (epsilon_0 * t_thickness_m * available_V**2) if available_V>0 else np.inf

    st.subheader("Solver Outputs")
    st.write(f"Required stiffness k_req = **{k_req:.2f} N/m**")
    st.write(f"Required force F_req = **{F_req*1e6:.2f} μN**")
    st.write(f"Required voltage V_req = **{V_req:.2f} V**")
    st.write(f"Required finger pairs n_req = **{n_req:.1f}**")

    st.expander("Show all work (solver math)", expanded=False).code(f"""
k_req = (2π f)^2 * m_eff
= (2π*{target_f:.3e})^2 * {m_eff:.3e}
= {k_req:.3e} N/m

F_req = k_req * x_target
= {k_req:.3e} * {target_x*1e-6:.3e}
= {F_req:.3e} N

V_req = sqrt((2 F_req g)/(n ε0 t))
= {V_req:.3f} V

n_req = (2 F_req g)/(ε0 t V^2)
= {n_req:.3e}
    """)



# -------------------------
# TAB 7: Beam & Measurement Geometry (Expanded)
# -------------------------
with tabs[7]:
    st.header("Beam & Measurement Geometry")
    st.markdown("""
    This section calculates the exact physical layout of the optical bench needed to test the device. As requested in the design review, we must calculate the required lens to match the laser spot to the grating size, and verify that the diffracted spots will actually be measurable on a standard camera detector.
    """)

    st.divider()

    # --- 1) Laser Spot Size ---
    st.subheader("1) Laser spot size vs grating size (Gaussian Optics)")
    st.markdown("""
    **Instructor Feedback:** *"Take a beam that’s a millimeter and focus it down to 500 microns and figure out the focal length of the lens you’d need... Grating needs to be big enough to accommodate the laser spot but no bigger than that."*
    
    To avoid scattering light off the surrounding comb drive and springs (which creates optical noise), the focused beam waist ($2w_0$) must perfectly fit inside the fabricated grating area.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        beam_diameter_mm = st.number_input("Laser beam diameter before lens (mm)", value=1.0, step=0.1)
    with col2:
        desired_spot_um = st.number_input("Desired spot diameter on grating (μm)", value=500.0, step=50.0)

    w_in = (beam_diameter_mm/2) * 1e-3
    w0 = (desired_spot_um/2) * 1e-6
    f_required = (np.pi * w0 * w_in) / lambda_m if lambda_m > 0 else 0.0

    st.latex(r"w_0 = \frac{\lambda f}{\pi w_{in}}\quad\Rightarrow\quad f=\frac{\pi w_0 w_{in}}{\lambda}")

    st.expander("Show all work (focal length)", expanded=False).code(f"""
w_in (Input radius) = {w_in:.3e} m
w_0  (Waist radius) = {w0:.3e} m
λ    (Wavelength)   = {lambda_m:.3e} m

f = (π * w_0 * w_in) / λ
  = {f_required:.3e} m
  = {f_required*1e3:.2f} mm
    """)

    st.write(f"### Required focal length: **{f_required*1e3:.2f} mm**")

    # Safety check against physical grating size
    grating_side_m = grating_side * 1e-6
    if grating_side_m < desired_spot_um*1e-6:
        st.error(f"⚠️ **Beam clipping:** The focused spot ({desired_spot_um} μm) is larger than your physical grating ({grating_side} μm). Light will hit the substrate, severely reducing efficiency and adding noise.")
    else:
        st.success(f"✅ **Perfect Fit:** Grating side ({grating_side} μm) ≥ beam spot ({desired_spot_um} μm). Light is safely captured.")

    st.divider()

    # --- 2) Spot Separation ---
    st.subheader("2) Diffraction spot separation on detector")
    st.markdown("""
    Once the beam hits the grating, it splits into multiple diffraction orders. To measure the pitch change, we need to know exactly how far apart the 0th-order (straight through/reflected) and 1st-order spots will be on your detector screen.
    """)
    st.latex(r"y_m = L_{detector} \cdot \tan(\theta_m)")
    
    if theta_by_order[1] is not None:
        sep_01 = detector_distance_m * (np.tan(theta_by_order[1]) - np.tan(theta_by_order[0]))
        st.write(f"Physical spot separation (m=0 to m=1) on screen: **{sep_01*1e3:.3f} mm** (at a distance of {detector_distance_m * 100:.1f} cm)")
    else:
        st.warning("m=1 order does not exist at this wavelength/pitch. The pitch is likely too small (sub-wavelength).")

    st.divider()

    # --- 3) Angular Resolution ---
    st.subheader("3) Angular resolution & Measurement Feasibility")
    st.markdown("""
    **Instructor Feedback:** *"Light converges then diffracts away... if diffraction spots are large enough it would be easy as you can use this to measure diffraction angle because you are going to get fringes."*
    
    If you are using a digital camera/CCD to measure the spot, the camera's pixel size limits the smallest angle shift you can detect. Furthermore, because static DC displacement is too small, we must verify that the **AC Resonance** blur is wider than a single pixel.
    """)
    
    pixel_pitch_um = st.number_input("Detector pixel pitch (μm)", value=5.0, step=1.0, help="Standard smartphone/webcam pixel sizes range from 1.2 to 5.0 μm.")
    ang_res_urad = (pixel_pitch_um*1e-6 / detector_distance_m) * 1e6 if detector_distance_m>0 else 0

    # Calculate expected AC blur angle shift
    ac_angle_shift_urad = angle_shift_urad * Q_assumed

    st.write(f"Detector angular resolution limit: **{ang_res_urad:.2f} μrad**")
    st.write(f"Predicted DC tuning shift: **{angle_shift_urad:.2f} μrad** (Usually unresolvable)")
    st.write(f"Predicted AC Resonance shift (blur): **{ac_angle_shift_urad:.2f} μrad** (Using Q={Q_assumed})")

    st.markdown("**Feasibility Check:**")
    if ac_angle_shift_urad > (ang_res_urad * 2): # factor of 2 to ensure it crosses at least 2 pixels to be a 'blur'
        st.success(f"✅ **Measurable:** The AC tuning shift ({ac_angle_shift_urad:.1f} μrad) is significantly larger than the pixel resolution. You will clearly see the spot widen/blur on the camera.")
    elif ac_angle_shift_urad > ang_res_urad:
        st.warning("⚠️ **Borderline:** The AC tuning shift is barely larger than a single pixel. Consider increasing the detector distance ($L$) or using a camera with smaller pixels.")
    else:
        st.error("❌ **Unmeasurable:** Even at resonance, the tuning shift is smaller than your pixel resolution. You MUST increase the detector distance or increase the applied voltage.")


# -------------------------
# TAB 8: Sensitivity & Error Budget
# -------------------------
with tabs[8]:
    st.header("Sensitivity & Error Budget")

    st.subheader("1) Comb force sensitivity to gap and voltage")
    dg = st.number_input("Gap error ±Δg (μm)", value=0.2, step=0.05)
    dV = st.number_input("Voltage error ±ΔV (V)", value=1.0, step=0.5)

    # Force scaling: F ∝ V^2 / g
    F_plus = (n_fingers * epsilon_0 * t_thickness_m * (V_applied+dV)**2) / (2 * (g_gap_m - dg*1e-6))
    F_minus = (n_fingers * epsilon_0 * t_thickness_m * (V_applied-dV)**2) / (2 * (g_gap_m + dg*1e-6))

    st.write(f"Nominal force: **{F_elec*1e6:.2f} μN**")
    st.write(f"Force range with errors: **{F_minus*1e6:.2f} to {F_plus*1e6:.2f} μN**")

    st.subheader("2) Spring stiffness sensitivity to length error")
    dL = st.number_input("Length error ±ΔL (μm)", value=5.0, step=1.0)
    k_plus = k_single * (L_support/(L_support-dL))**3
    k_minus = k_single * (L_support/(L_support+dL))**3

    st.write(f"Nominal k_single: **{k_single:.2f} N/m**")
    st.write(f"Range with ΔL: **{k_minus:.2f} to {k_plus:.2f} N/m**")

    st.subheader("3) Displacement sensitivity")
    x_plus = F_plus / (k_plus*n_springs) if (k_plus*n_springs) > 0 else 0
    x_minus = F_minus / (k_minus*n_springs) if (k_minus*n_springs) > 0 else 0
    
    st.write(f"Nominal displacement (DC): **{x_disp_DC*1e6:.3f} μm**")
    st.write(f"Range with errors (DC): **{x_minus*1e6:.3f} to {x_plus*1e6:.3f} μm**")

    st.subheader("4) Optical angle error from pitch error")
    dLambda = st.number_input("Pitch error ±ΔΛ (nm)", value=50.0, step=10.0)
    Lambda_plus = (Lambda_pitch + dLambda*1e-3)*1e-6
    Lambda_minus = (Lambda_pitch - dLambda*1e-3)*1e-6

    theta_plus = np.arcsin((m_order*lambda_m)/Lambda_plus) if (m_order*lambda_m/Lambda_plus)<=1 else None
    theta_minus = np.arcsin((m_order*lambda_m)/Lambda_minus) if (m_order*lambda_m/Lambda_minus)<=1 else None

    if theta_plus and theta_minus:
        dtheta_err = (theta_plus - theta_minus)*1e6
        st.write(f"Angle error from pitch uncertainty: **{dtheta_err:.2f} μrad**")
    else:
        st.warning("Pitch error causes order to vanish at this wavelength.")

# -------------------------
# TAB 9: Gaussian Beam Optics
# -------------------------
with tabs[9]:
    st.header("Gaussian Beam Optics & Focusing (Detailed)")

    st.subheader("Input beam + lens parameters")
    beam_diam_mm = st.number_input("Input beam diameter at lens (1/e²) [mm]", value=1.0, step=0.1)
    M2 = st.number_input("Beam quality M²", value=1.1, step=0.1)
    f_mm = st.number_input("Lens focal length [mm]", value=50.0, step=5.0)
    z_focus_to_grating_mm = st.number_input("Focus-to-grating distance [mm]", value=0.0, step=1.0)
    z_focus_to_detector_cm = st.number_input("Focus-to-detector distance [cm]", value=detector_distance_cm, step=1.0)

    # Convert
    w_in = (beam_diam_mm/2) * 1e-3
    f = f_mm * 1e-3
    z_g = z_focus_to_grating_mm * 1e-3
    z_d = z_focus_to_detector_cm / 100.0
    P_W = incident_power_mW * 1e-3

    # Gaussian beam equations
    w0 = (M2 * lambda_m * f) / (np.pi * w_in) if w_in > 0 else np.inf
    z_R = (np.pi * w0**2) / (M2 * lambda_m) if lambda_m > 0 else np.inf
    theta_div = (M2 * lambda_m) / (np.pi * w0) if w0 > 0 else np.inf

    # Beam size at grating and detector
    w_g = w0 * np.sqrt(1 + (z_g/z_R)**2)
    w_d = w0 * np.sqrt(1 + (z_d/z_R)**2)

    # NA and f-number
    NA = w_in / f if f > 0 else 0
    f_number = f / (2*w_in) if w_in > 0 else np.inf

    # Intensity at grating (Gaussian peak)
    I0 = 2 * P_W / (np.pi * w_g**2) if w_g > 0 else 0

    # Fraction of Gaussian power intercepted by grating (square approx)
    # fraction ≈ [erf(G/(√2 w))]^2
    if w_g > 0:
        frac = (math.erf(grating_side_m/(math.sqrt(2)*w_g)))**2
    else:
        frac = 0
    P_on_grating = P_W * frac

    st.subheader("Results")
    st.write(f"Beam waist w₀: **{w0*1e6:.2f} μm**")
    st.write(f"Rayleigh range z_R: **{z_R*1e3:.2f} mm**")
    st.write(f"Divergence half‑angle: **{theta_div*1e3:.2f} mrad**")
    st.write(f"Beam radius at grating: **{w_g*1e6:.2f} μm** (diameter {2*w_g*1e6:.2f} μm)")
    st.write(f"Beam radius at detector: **{w_d*1e6:.2f} μm** (diameter {2*w_d*1e6:.2f} μm)")
    st.write(f"NA ≈ **{NA:.3f}** | f/# ≈ **{f_number:.2f}**")
    st.write(f"Peak intensity at grating: **{I0:.2e} W/m²**")
    st.write(f"Power captured by grating: **{P_on_grating*1e3:.2f} mW** ({frac*100:.1f}%)")

    st.subheader("Equations used")
    st.latex(r"w_0=\frac{M^2 \lambda f}{\pi w_{in}}")
    st.latex(r"z_R=\frac{\pi w_0^2}{M^2 \lambda}")
    st.latex(r"w(z)=w_0\sqrt{1+(z/z_R)^2}")
    st.latex(r"\theta_{div}=\frac{M^2\lambda}{\pi w_0}")
    st.latex(r"NA \approx \frac{w_{in}}{f}")
    st.latex(r"I_0=\frac{2P}{\pi w^2}")
    st.latex(r"F \approx \left[\mathrm{erf}\left(\frac{G}{\sqrt{2}w}\right)\right]^2")

    st.expander("Show all work (Gaussian beam)", expanded=False).code(f"""
w_in = {w_in:.3e} m
f = {f:.3e} m
λ = {lambda_m:.3e} m
M² = {M2:.2f}

w0 = (M²*λ*f)/(π*w_in)
= ({M2:.2f}*{lambda_m:.3e}*{f:.3e})/(π*{w_in:.3e})
= {w0:.3e} m

z_R = π w0^2 / (M² λ)
= {z_R:.3e} m

θ_div = M² λ / (π w0)
= {theta_div:.3e} rad

w_g = w0 * sqrt(1+(z_g/z_R)^2)
= {w_g:.3e} m

w_d = w0 * sqrt(1+(z_d/z_R)^2)
= {w_d:.3e} m

NA = w_in/f = {NA:.3f}
f/# = f/(2w_in) = {f_number:.2f}

I0 = 2P/(π w_g^2)
= 2*{P_W:.3e}/(π*{w_g:.3e}^2)
= {I0:.3e} W/m²

Fraction on grating:
F = [erf(G/(√2 w_g))]^2
= {frac:.3f}
P_on_grating = {P_on_grating*1e3:.2f} mW
    """)
