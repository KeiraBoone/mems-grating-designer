import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
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
st.markdown("Complete design and analysis tool for MEMS-actuated tunable diffraction gratings")

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
# SIDEBAR - DESIGN PARAMETERS
# ============================================================================

st.sidebar.divider()
st.sidebar.header("⚙️ Design Parameters")

st.sidebar.subheader("1️⃣ Comb Drive")
n_fingers = st.sidebar.slider(
    "Comb finger pairs",
    min_value=10.0, max_value=500.0, value=100.0, step=10.0
)
V_applied = st.sidebar.slider(
    "Applied voltage (V)",
    min_value=10.0, max_value=150.0, value=75.0, step=5.0
)
g_gap = st.sidebar.slider(
    "Gap between fingers (μm)",
    min_value=0.5, max_value=10.0, value=2.0, step=0.5
)

st.sidebar.subheader("2️⃣ Device")
t_thickness = st.sidebar.slider(
    "Device thickness (μm)",
    min_value=5.0, max_value=50.0, value=20.0, step=5.0
)
rho_mass = st.sidebar.slider(
    "Moving mass (mg)",
    min_value=1.0, max_value=20.0, value=5.0, step=1.0
)

st.sidebar.subheader("3️⃣ Springs (MOST CRITICAL)")
L_support = st.sidebar.slider(
    "Support beam length (μm)",
    min_value=20.0, max_value=500.0, value=100.0, step=10.0
)
w_beam = st.sidebar.slider(
    "Support beam width (μm)",
    min_value=1.0, max_value=20.0, value=3.0, step=1.0
)
n_springs = st.sidebar.slider(
    "Number of support springs",
    min_value=2.0, max_value=8.0, value=4.0, step=1.0
)

st.sidebar.subheader("4️⃣ Grating")
Lambda_pitch = st.sidebar.slider(
    "Grating pitch (μm)",
    min_value=1.0, max_value=50.0, value=12.0, step=1.0
)
grating_side = st.sidebar.slider(
    "Grating side length (μm)",
    min_value=100.0, max_value=1000.0, value=600.0, step=100.0
)
pitch_change_factor = st.sidebar.slider(
    "Pitch change factor (ΔΛ / x)",
    min_value=0.0, max_value=0.2, value=0.0285, step=0.005
)

st.sidebar.subheader("5️⃣ Optical")
wavelength = st.sidebar.slider(
    "Target wavelength (nm)",
    min_value=400.0, max_value=2000.0, value=1310.0, step=50.0
)
m_order = st.sidebar.selectbox("Diffraction order", options=[1, 2, 3])
grating_uniformity = st.sidebar.slider(
    "Grating uniformity",
    min_value=0.5, max_value=1.0, value=0.95, step=0.05
)


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def calculate_spring_stiffness(E, w, t, L, n_springs):
    k_single = (3 * E * w * t**3) / (4 * L**3)
    return k_single * n_springs, k_single

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
    return (3 * F * L) / (2 * w * t**2)

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
# CALCULATIONS
# ============================================================================

k_total, k_single = calculate_spring_stiffness(
    E_silicon, w_beam * 1e-6, t_thickness * 1e-6, L_support * 1e-6, n_springs
)

F_elec = calculate_electrostatic_force(n_fingers, epsilon_0, t_thickness, V_applied, g_gap)
x_disp = calculate_displacement(F_elec, k_total)
f_resonant = calculate_resonant_frequency(k_total, rho_mass)

theta_target = calculate_diffraction_angle(m_order, wavelength, Lambda_pitch, in_radians=True)
theta_1 = calculate_diffraction_angle(1, wavelength, Lambda_pitch)
theta_2 = calculate_diffraction_angle(2, wavelength, Lambda_pitch)
theta_3 = calculate_diffraction_angle(3, wavelength, Lambda_pitch)

dtheta_dlambda = calculate_angular_dispersion(m_order, Lambda_pitch, wavelength)
R, N_lines = calculate_spectral_resolution(m_order, grating_side, Lambda_pitch)

eff_m0 = calculate_efficiency_by_order(0, grating_uniformity) * 100
eff_m1 = calculate_efficiency_by_order(1, grating_uniformity) * 100
eff_m2 = calculate_efficiency_by_order(2, grating_uniformity) * 100
eff_m3 = calculate_efficiency_by_order(3, grating_uniformity) * 100

pitch_change_m = x_disp * pitch_change_factor
pitch_change_nm = pitch_change_m * 1e9
new_pitch = Lambda_pitch - (pitch_change_m * 1e6)

delta_lambda = calculate_tuning_range(pitch_change_m, Lambda_pitch, wavelength)

if new_pitch > 0 and theta_target is not None:
    theta_new = calculate_diffraction_angle(m_order, wavelength, new_pitch, in_radians=True)
    angle_shift_urad = (theta_new - theta_target) * 1e6 if theta_new is not None else 0
else:
    angle_shift_urad = 0

E_field = V_applied / g_gap
F_per_beam = F_elec / n_springs
stress_beam = calculate_stress_in_beam(F_per_beam, w_beam * 1e-6, t_thickness * 1e-6, L_support * 1e-6)
stress_ratio = stress_beam / sigma_yield
# Extra mechanical calculations
I_beam = (w_beam_m * t_thickness_m**3) / 12  # Area moment of inertia
compliance = 1 / k_total                     # m/N
strain_max = stress_beam / E_silicon         # unitless
safety_factor = sigma_yield / stress_beam if stress_beam > 0 else np.inf

# Max allowable force before yield (from bending stress formula)
F_max_yield = (2 * w_beam_m * t_thickness_m**2 * sigma_yield) / (3 * L_support_m)

# Max displacement before yield
x_max_yield = F_max_yield / k_total

# Max voltage before yield (comb-drive force equation inverted)
V_max_yield = np.sqrt((2 * F_max_yield * g_gap_m) / (n_fingers * epsilon_0 * t_thickness_m))

# Spring energy stored at current displacement
U_spring = 0.5 * k_total * x_disp**2

# Angular resonant frequency
omega_n = 2 * np.pi * f_resonant

fab_issues, fab_recommendations = calculate_fabrication_feasibility(g_gap, L_support, w_beam)

# ============================================================================
# TOP METRICS
# ============================================================================

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Spring Stiffness", f"{k_total:.2f} N/m", f"({k_single:.2f} each)")
with col2:
    st.metric("Electrostatic Force", f"{F_elec*1e6:.2f} μN")
with col3:
    st.metric(f"Displacement @ {V_applied:.0f}V", f"{x_disp*1e6:.3f} μm")
with col4:
    st.metric("Resonant Frequency", f"{f_resonant:.1f} Hz")

st.divider()

# ============================================================================
# SIMPLE TABS (MECH / OPTICAL / ELECTRICAL / FABRICATION / VALIDATION / SUMMARY)
# ============================================================================

tabs = st.tabs(["Mechanical", "Optical", "Electrical", "Fabrication", "Validation", "Summary", "Design Solver"])

with tabs[0]:
    st.subheader("Spring Stiffness")
    st.latex(r"k = \frac{3Ewt^3}{4L^3}")

    with st.expander("Show calculation steps (stiffness)"):
        st.code(f"""
k_single = (3*E*w*t^3)/(4*L^3)
= (3*{E_silicon:.3e}*{w_beam_m:.3e}*{t_thickness_m:.3e}^3)/(4*{L_support_m:.3e}^3)
= {k_single:.3e} N/m

k_total = k_single * n_springs
= {k_single:.3e} * {n_springs:.0f}
= {k_total:.3e} N/m
        """)

    st.write(f"Spring stiffness: {k_total:.2f} N/m")
    st.write(f"Displacement: {x_disp*1e6:.3f} μm")
    st.write(f"Max stress: {stress_beam/1e6:.2f} MPa")

    with st.expander("Show calculation steps (stress)"):
        st.code(f"""
σ_max = (3*F*L)/(2*w*t^2)

F_per_beam = {F_per_beam:.3e} N
L = {L_support_m:.3e} m
w = {w_beam_m:.3e} m
t = {t_thickness_m:.3e} m

σ_max = (3*{F_per_beam:.3e}*{L_support_m:.3e})/(2*{w_beam_m:.3e}*{t_thickness_m:.3e}^2)
= {stress_beam:.3e} Pa
= {stress_beam/1e6:.2f} MPa
        """)

    st.subheader("Force Balance")
    st.latex(r"F_e = kx")

    with st.expander("Show calculation steps (force balance)"):
        st.code(f"""
x = F_e / k
= ({F_elec:.3e}) / ({k_total:.3e})
= {x_disp:.3e} m
= {x_disp*1e6:.3f} μm
        """)

    st.subheader("Resonant Frequency")
    st.latex(r"f = \frac{1}{2\pi}\sqrt{\frac{k}{m}}")

    with st.expander("Show calculation steps (frequency)"):
        st.code(f"""
f = (1/2π)*sqrt(k/m)
= (1/2π)*sqrt({k_total:.3e} / ({rho_mass:.3e}e-6))
= {f_resonant:.3f} Hz
ω_n = 2πf = {omega_n:.3f} rad/s
        """)

    st.subheader("Advanced Mechanical Metrics")
    st.write(f"Moment of inertia I: {I_beam:.3e} m⁴")
    st.write(f"Compliance (1/k): {compliance:.3e} m/N")
    st.write(f"Max strain: {strain_max:.3e}")
    st.write(f"Safety factor: {safety_factor:.2f}")

    with st.expander("Show calculation steps (strain + safety)"):
        st.code(f"""
strain = σ/E
= {stress_beam:.3e} / {E_silicon:.3e}
= {strain_max:.3e}

Safety factor = σ_yield / σ_max
= {sigma_yield:.3e} / {stress_beam:.3e}
= {safety_factor:.2f}
        """)

    st.subheader("Yield‑Limit Displacement & Voltage")
    st.write(f"Max force before yield: {F_max_yield:.3e} N")
    st.write(f"Max displacement before yield: {x_max_yield*1e6:.2f} μm")
    st.write(f"Max voltage before yield: {V_max_yield:.1f} V")

    with st.expander("Show calculation steps (yield limits)"):
        st.code(f"""
F_max = (2*w*t^2*σ_yield)/(3*L)
= (2*{w_beam_m:.3e}*{t_thickness_m:.3e}^2*{sigma_yield:.3e})/(3*{L_support_m:.3e})
= {F_max_yield:.3e} N

x_max = F_max / k
= {F_max_yield:.3e} / {k_total:.3e}
= {x_max_yield:.3e} m = {x_max_yield*1e6:.2f} μm

V_max = sqrt((2*F_max*g)/(n*ε0*t))
= {V_max_yield:.2f} V
        """)

    st.subheader("Stored Mechanical Energy")
    st.write(f"Spring energy: {U_spring:.3e} J")

    with st.expander("Show calculation steps (energy)"):
        st.code(f"""
U = 1/2 * k * x^2
= 0.5 * {k_total:.3e} * ({x_disp:.3e})^2
= {U_spring:.3e} J
        """)

with tabs[1]:
    st.header("Optical Analysis")

    # Local unit conversions for step-by-step math
    lambda_m = wavelength * 1e-9
    Lambda_m = Lambda_pitch * 1e-6
    L_det = 0.01  # 1 cm detector distance

    # --- Grating equation ---
    st.subheader("Diffraction Grating Equation")
    st.latex(r"m\lambda = \Lambda \sin(\theta)")

    sin_theta = (m_order * lambda_m) / Lambda_m
    if sin_theta <= 1:
        theta_rad = np.arcsin(sin_theta)
        theta_deg = np.degrees(theta_rad)
    else:
        theta_rad = None
        theta_deg = None

    with st.expander("Show calculation steps (Grating equation)"):
        st.code(f"""
sin(θ) = (m*λ)/Λ
= ({m_order}*{lambda_m:.3e})/({Lambda_m:.3e})
= {sin_theta:.3e}

θ = asin({sin_theta:.3e})
= {theta_deg:.4f}°
        """)

    st.write(f"Diffraction angle (m={m_order}): {theta_deg if theta_deg else 'N/A'}°")

    # --- Order angles table ---
    st.subheader("Diffraction Angles by Order")
    order_data = []
    for m in [0, 1, 2, 3]:
        if m == 0:
            order_data.append({"Order m": 0, "sinθ": 0, "θ (deg)": 0})
        else:
            s = (m * lambda_m) / Lambda_m
            if s > 1:
                order_data.append({"Order m": m, "sinθ": f"{s:.3f}", "θ (deg)": "N/A"})
            else:
                order_data.append({"Order m": m, "sinθ": f"{s:.3f}", "θ (deg)": f"{np.degrees(np.arcsin(s)):.3f}"})
    st.dataframe(pd.DataFrame(order_data), use_container_width=True)

    # --- Pitch change + angle shift ---
    st.subheader("Pitch Change and Angle Shift")
    st.write(f"Pitch change factor: {pitch_change_factor:.4f}")

    with st.expander("Show calculation steps (Pitch change + angle shift)"):
        st.code(f"""
ΔΛ = x * pitch_change_factor
= {x_disp:.3e} * {pitch_change_factor:.4f}
= {pitch_change_m:.3e} m

New pitch = Λ - ΔΛ
= {Lambda_pitch:.2f} μm - {pitch_change_m*1e6:.3f} μm
= {new_pitch:.3f} μm

Δθ = θ_new - θ_old
= {angle_shift_urad:.3f} μrad
        """)

    st.write(f"Pitch change: {pitch_change_nm:.2f} nm")
    st.write(f"Angle shift: {angle_shift_urad:.2f} μrad")

    # --- Angular dispersion ---
    st.subheader("Angular Dispersion")
    st.latex(r"\frac{d\theta}{d\lambda} = \frac{m}{\Lambda\cos(\theta)}")

    if theta_rad is not None:
        dtheta_dlambda = (m_order / (Lambda_m * np.cos(theta_rad))) * 1e-9 * 1e6
    else:
        dtheta_dlambda = 0

    with st.expander("Show calculation steps (Angular dispersion)"):
        st.code(f"""
dθ/dλ = m/(Λ*cosθ)
= {m_order}/({Lambda_m:.3e}*cos({theta_rad:.3e}))
= {dtheta_dlambda:.3f} μrad/nm
        """)

    st.write(f"Angular dispersion: {dtheta_dlambda:.2f} μrad/nm")

    # Linear dispersion on detector
    linear_disp_um = dtheta_dlambda * L_det  # μm per nm
    st.write(f"Linear dispersion at 1 cm: {linear_disp_um:.2f} μm/nm")

    # --- Tuning range ---
    st.subheader("Tuning Range")
    st.write(f"Δλ = {delta_lambda:.4f} nm")

    with st.expander("Show calculation steps (Tuning range)"):
        st.code(f"""
Δλ = (ΔΛ/Λ)*λ
= ({pitch_change_m:.3e}/{Lambda_m:.3e})*{lambda_m:.3e}
= {delta_lambda:.3e} nm
        """)

    # --- Spectral resolution ---
    st.subheader("Spectral Resolution")
    st.latex(r"R = mN")

    with st.expander("Show calculation steps (Resolution)"):
        st.code(f"""
N = grating_side/Λ
= {grating_side:.1f} μm / {Lambda_pitch:.2f} μm
= {N_lines} lines

R = m*N
= {m_order}*{N_lines}
= {R}

Δλ_min = λ/R
= {wavelength:.1f}/{R}
= {wavelength/R:.4f} nm
        """)

    st.write(f"Resolving power: R = {R}")
    st.write(f"Minimum resolvable Δλ: {wavelength/R:.4f} nm")

    # --- Order power split ---
    st.subheader("Order Power Split (Efficiency)")
    st.write(f"m=0: {eff_m0:.1f}%  |  m=1: {eff_m1:.1f}%  |  m=2: {eff_m2:.1f}%  |  m=3: {eff_m3:.1f}%")
    st.write(f"Unaccounted loss: {100 - (eff_m0 + eff_m1 + eff_m2 + eff_m3):.1f}%")


with tabs[2]:
    st.subheader("Comb‑Drive Force")
    st.latex(r"F = \frac{n\varepsilon_0 t V^2}{2g}")

    with st.expander("Show calculation steps"):
        st.code(f"""
F = (n*ε0*t*V^2)/(2g)
= ({n_fingers}*{epsilon_0:.3e}*{t_thickness_m:.3e}*{V_applied**2:.1f})/(2*{g_gap_m:.3e})
= {F_elec:.3e} N
= {F_elec*1e6:.2f} μN
        """)

    st.write(f"Electrostatic force: {F_elec*1e6:.2f} μN")
    st.write(f"E‑field: {E_field:.2f} MV/m")

    st.subheader("Voltage Needed for Target Displacement")
    st.latex(r"V = \sqrt{\frac{2Fg}{n\varepsilon_0 t}}")

    with st.expander("Show calculation steps"):
        target_x = 2.0
        V_needed = calculate_voltage_for_target_displacement(target_x, k_total, n_fingers, epsilon_0, t_thickness, g_gap)
        st.code(f"""
Target x = {target_x} μm
F = k*x = {k_total:.3e} * {target_x*1e-6:.3e}
V = sqrt((2*F*g)/(n*ε0*t))
= {V_needed:.2f} V
        """)

with tabs[3]:
    st.header("Fabrication Feasibility Analysis")

    st.subheader("Process Flow (from slides)")
    st.markdown("""
    **Step 1 — SOI Wafer**  
    • Device layer with embedded oxide stop layer  
    • Sacrificial release layer already built in  

    **Step 2 — Photolithography**  
    • Resist: **AZ10XT**  
    • Tool: **MLA150**  
    • Define comb fingers + grating beams  

    **Step 3 — DRIE Etch (Deep Reactive Ion Etch)**  
    • Tool: **DRIE‑STS‑MMPLEX**  
    • Deep silicon etch to BOX layer  

    **Step 4 — Ashing**  
    • Tool: **Asher‑Chuck‑ES**  
    • Removes photoresist  

    **Step 5 — BOE Release Etch**  
    • ~15 min/μm  
    • Removes buried oxide → frees moving structures  

    **Step 6 — Piranha Clean + PVD**  
    • Tool: **Endura PVD**  
    • Deposits **Al contacts**  

    """)

    st.divider()
    st.subheader("Feature Size Analysis")

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        st.write(f"**Comb Gap: {g_gap:.2f} μm**")
        if g_gap < 0.5:
            st.error("❌ Impossible - below optical diffraction limit")
        elif g_gap < 1.5:
            st.error("❌ Very difficult - tight process control, high failure")
            st.write("*Recommend: e-beam lithography*")
        elif g_gap < 2.0:
            st.warning("⚠️ Tight - careful mask alignment needed")
        elif g_gap < 5.0:
            st.success("✅ Good - standard optical lithography achievable")
        else:
            st.info("ℹ️ Loose - easy to fabricate but reduced force")

    with col_f2:
        st.write(f"**Beam Width: {w_beam:.2f} μm**")
        if w_beam < 0.5:
            st.error("❌ Impossible - will collapse")
        elif w_beam < 1.0:
            st.error("❌ Very risky - likely to fail")
        elif w_beam < 2.0:
            st.warning("⚠️ Tight - DRIE profile critical")
        else:
            st.success("✅ Good - standard fabrication")

    with col_f3:
        st.write(f"**Beam Length: {L_support:.2f} μm**")
        if L_support < 20:
            st.warning("⚠️ Very short - stiff springs")
        elif L_support < 300:
            st.success("✅ Good - fits on standard chips")
        else:
            st.warning("⚠️ Long - may need serpentine routing")

    st.divider()
    st.subheader("Issues & Recommendations")

    if fab_issues:
        st.error("**Fabrication Issues:**")
        for issue in fab_issues:
            st.write(f"- ❌ {issue}")
    else:
        st.success("**No major fabrication issues detected!**")

    if fab_recommendations:
        st.info("**Recommendations:**")
        for rec in fab_recommendations:
            st.write(f"- 💡 {rec}")

with tabs[4]:
    st.write("Validation checks will go here.")

with tabs[5]:
    st.header("Summary")
    st.subheader("Auto‑Generated Summary")
    st.write(f"""
    **Project:** {project_title}  
    **Created by:** {created_by}  
    **Rendered by:** {rendered_by}  

    **Key Results**
    - Spring stiffness: {k_total:.2f} N/m  
    - Electrostatic force: {F_elec*1e6:.2f} μN  
    - Displacement: {x_disp*1e6:.3f} μm  
    - Resonant frequency: {f_resonant:.1f} Hz  
    - Optical tuning: {delta_lambda:.3f} nm  
    - Angular dispersion: {dtheta_dlambda:.2f} μrad/nm  
    """)

    st.subheader("Manual Summary (Editable)")
    st.text_area("Final Summary Block", value=manual_summary, height=200)

    st.markdown("---")
    st.markdown("✅ **Ready for copy into report / slides**")

with tabs[6]:
    st.header("Design Solver (Inverse Design)")

    target_f = st.number_input("Target resonant frequency (Hz)", value=float(f_resonant), step=100.0)
    target_x = st.number_input("Target displacement (μm)", value=2.0, step=0.1)
    target_V = st.number_input("Available voltage (V)", value=float(V_applied), step=5.0)

    # Required stiffness for target frequency
    k_req = (2*np.pi*target_f)**2 * (rho_mass*1e-6)
    L_req = ((3*E_silicon*w_beam_m*t_thickness_m**3*n_springs)/(4*k_req))**(1/3) * 1e6

    # Required voltage for target displacement
    V_req = calculate_voltage_for_target_displacement(target_x, k_total, n_fingers, epsilon_0, t_thickness, g_gap)

    # Required finger count if voltage fixed
    F_req = k_total * (target_x*1e-6)
    n_req = (2*F_req*g_gap_m)/(epsilon_0*t_thickness_m*target_V**2)

    st.subheader("Recommended Values")
    st.write(f"Required stiffness for {target_f:.0f} Hz: **{k_req:.2f} N/m**")
    st.write(f"Recommended beam length: **{L_req:.1f} μm** (with current w, t, n_springs)")
    st.write(f"Required voltage for {target_x:.1f} μm: **{V_req:.2f} V**")
    st.write(f"Required finger count for {target_x:.1f} μm at {target_V:.0f} V: **{n_req:.0f} fingers**")