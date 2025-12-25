import streamlit as st
from utils.base_model import calculate_solar_output

# ---------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Solar Ninja",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# 2. Custom CSS (Website Look - Grey BG, White Blocks)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* 1. Global Background */
    .stApp {
        background-color: #F2F4F8; /* Light Grey Background */
    }

    /* 2. White Blocks (Containers) - We will style standard Streamlit containers implicitly via wrapping or simple grouping */
    /* Оскільки ми не можемо напряму стилізувати st.container, ми використовуємо css injection для головних блоків */
    
    div.block-container {
        padding-top: 2rem;
    }

    /* 3. Headers */
    h1, h2, h3 {
        color: #333333;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* 4. Buttons (Calculate & Download) */
    .stButton > button {
        background-color: #FF8C00 !important; /* Orange */
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        background-color: #e07b00 !important;
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }

    /* 5. Metrics styling */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #E0E0E0;
    }
    div[data-testid="stMetricLabel"] {
        color: #666666;
    }
    div[data-testid="stMetricValue"] {
        color: #333333;
        font-weight: 700;
    }
    
    /* 6. Custom styling for Sliders to approximate "Orange" and "Green" */
    /* Це складний хак для Streamlit, оскільки він не має класів для окремих слайдерів.
       Ми змінимо загальний акцент на Помаранчевий. */
    div[data-baseweb="slider"] div[data-testid="stTickBar"] {
        background: #FF8C00; 
    }
    
    /* Стиль для білих карток (використовується через markdown div) */
    .white-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. Header
# ---------------------------------------------------------
st.title("⚔️ Solar Ninja")
st.markdown("##### Professional Solar Energy Estimator")
st.write("") # Spacer

# ---------------------------------------------------------
# 4. Inputs Section (White Block)
# ---------------------------------------------------------
# Ми використовуємо контейнер і імітуємо білий блок, розміщуючи його вміст "всередині" візуально
with st.container():
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Configuration")
    
    with st.form("main_form"):
        # Рядок 1: Координати (Київ)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Location Coordinates**")
            col_lat, col_lon = st.columns(2)
            # Defaults: Kyiv (50.45, 30.52)
            latitude = col_lat.number_input("Latitude", value=50.4500, format="%.4f")
            longitude = col_lon.number_input("Longitude", value=30.5200, format="%.4f")
        
        with c2:
            st.markdown("**System Parameters**")
            # Orange Slider idea (System Power)
            system_power_kw = st.slider("System Power (kW)", 1.0, 50.0, 10.0, step=0.5)
            # "Green" slider idea (Tilt) - we keep it standard style but in same block
            user_tilt = st.slider("Panel Tilt (degrees)", 0, 90, 45)

        st.write("")
        # Кнопка на всю ширину або по центру
        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
        with btn_col2:
            submitted = st.form_submit_button("CALCULATE ESTIMATE 🚀", use_container_width=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Logic & Outputs
# ---------------------------------------------------------

if submitted:
    # Розрахунок
    with st.spinner("Calculating Solar Potential..."):
        result = calculate_solar_output(
            latitude=latitude,
            longitude=longitude,
            system_power_kw=system_power_kw,
            user_tilt=user_tilt
        )
        
    monthly_df = result["monthly_df"]
    monthly_best = result["monthly_best"]
    annual_energy = result["annual_energy"]
    annual_optimal_tilt = result["annual_optimal_tilt"]
    pdf_buffer = result["pdf"]
    fig = result["fig"]

    # -----------------------------------------------------
    # RESULT BLOCK (White Card)
    # -----------------------------------------------------
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Results Analysis")
    
    # 1. Metrics Row
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Annual Energy", f"{annual_energy:,.0f} kWh")
    with m2:
        st.metric("Optimal Tilt Angle", f"{annual_optimal_tilt}°")
    with m3:
        # Різниця
        diff = annual_optimal_tilt - user_tilt
        st.metric("Tilt Difference", f"{diff:+.1f}°", delta="Deviation from optimal", delta_color="inverse")
    
    st.divider()

    # 2. Chart & Table
    row_chart, row_table = st.columns([2, 1])
    
    with row_chart:
        st.markdown("**Monthly Energy Production**")
        st.pyplot(fig, use_container_width=True)
        
    with row_table:
        st.markdown("**Monthly Data Table**")
        st.dataframe(
            monthly_df, 
            hide_index=True, 
            use_container_width=True, 
            height=300
        )

    st.divider()
    
    # 3. Actions (Download)
    d1, d2 = st.columns([3, 1])
    with d1:
        with st.expander("View Detailed Optimization Data"):
            st.dataframe(monthly_best, use_container_width=True)
    with d2:
        st.download_button(
            label="📥 Download Report (PDF)",
            data=pdf_buffer,
            file_name="Solar_Ninja_Kyiv_Report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Start screen hint
    st.info("👆 Click **CALCULATE ESTIMATE** to run the model for the default location (Kyiv).")
