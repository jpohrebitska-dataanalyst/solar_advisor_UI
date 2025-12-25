import streamlit as st
from utils.base_model import calculate_solar_output

# ---------------------------------------------------------
# 1. Page Configuration (Wide Mode & Title)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Solar Ninja — Basic Model",
    page_icon="⚔️",
    layout="wide",  # Використовуємо всю ширину екрану
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. Custom CSS for UI "Face-lift"
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Стиль для метрик (карток) */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464b59;
        padding: 15px 0px 15px 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetricLabel"] {
        color: #b0b0b0; /* Світло-сірий для підписів */
    }
    div[data-testid="stMetricValue"] {
        color: #FF8C00; /* Solar Ninja Orange */
    }
    
    /* Кнопка "Calculate" */
    .stButton > button {
        width: 100%;
        background-color: #FF8C00;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 10px;
    }
    .stButton > button:hover {
        background-color: #e07b00;
        color: white;
    }
    
    /* Заголовок у сайдбарі */
    .sidebar-header {
        font-size: 20px;
        font-weight: bold;
        color: #FF8C00;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. Sidebar (Inputs)
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/emoji/96/000000/crossed-swords.png", width=60) # Ninja icon
    st.markdown('<div class="sidebar-header">Configuration</div>', unsafe_allow_html=True)
    
    with st.form("input_form"):
        st.subheader("📍 Location")
        latitude = st.number_input("Latitude", value=50.45, format="%.4f", help="Decimal degrees (e.g., 50.45)")
        longitude = st.number_input("Longitude", value=30.52, format="%.4f", help="Decimal degrees (e.g., 30.52)")
        
        st.markdown("---")
        st.subheader("⚡ System Params")
        system_power_kw = st.number_input("System Power (kW)", value=10.0, step=0.5)
        user_tilt = st.number_input("Panel Tilt (°)", value=45.0, step=1.0, min_value=0.0, max_value=90.0)

        st.markdown("---")
        submitted = st.form_submit_button("🚀 Calculate Output")
    
    st.markdown(
        """
        <div style='margin-top: 30px; font-size: 12px; color: gray;'>
        <b>Solar Ninja — Basic Model</b><br>
        v1.0.0 | Analytics Tool
        </div>
        """, 
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# 4. Main Area
# ---------------------------------------------------------
st.title("⚔️ Solar Ninja Dashboard")

if not submitted:
    # "Placeholder" - що показувати, коли користувач ще не натиснув кнопку
    st.info("👈 Please enter your parameters in the sidebar and click **Calculate Output**.")
    st.markdown("""
    ### What calculates this model:
    * **Annual Energy Output** based on historical solar data.
    * **Optimal Tilt Angle** for your specific latitude.
    * **Monthly Breakdown** of potential generation.
    * **PDF Report** generation for clients.
    """)

if submitted:
    with st.spinner("⚔️ Solar Ninja is crunching numbers..."):
        # Виклик функції розрахунку
        result = calculate_solar_output(
            latitude=latitude,
            longitude=longitude,
            system_power_kw=system_power_kw,
            user_tilt=user_tilt
        )

    # Розпаковка
    monthly_df = result["monthly_df"]
    monthly_best = result["monthly_best"]
    annual_energy = result["annual_energy"]
    annual_optimal_tilt = result["annual_optimal_tilt"]
    pdf_buffer = result["pdf"]
    fig = result["fig"]

    # --- SECTION A: KPI CARDS ---
    st.subheader("📊 Key Performance Indicators")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric("Annual Energy", f"{annual_energy:,.0f} kWh", delta="Estimated")
    with kpi2:
        st.metric("Optimal Tilt", f"{annual_optimal_tilt}°", delta=f"{annual_optimal_tilt - user_tilt:.1f}° vs user", delta_color="off")
    with kpi3:
        st.metric("System Size", f"{system_power_kw} kW")
    with kpi4:
        st.metric("Location", f"{latitude:.2f}, {longitude:.2f}")

    st.markdown("---")

    # --- SECTION B: CHARTS & TABLES ---
    
    col_chart, col_data = st.columns([2, 1]) # Графік ширший за таблицю (2:1)

    with col_chart:
        st.subheader("Monthly Production Trend")
        # Відображаємо Matplotlib фігуру (вона тепер прозора і гарна)
        st.pyplot(fig, use_container_width=True)

    with col_data:
        st.subheader("Monthly Data")
        # Стилізуємо таблицю, щоб вона виглядала компактно
        st.dataframe(
            monthly_df, 
            hide_index=True, 
            use_container_width=True,
            height=350 # Фіксуємо висоту, щоб збігалася з графіком
        )

    # --- SECTION C: ANALYTICS & DOWNLOAD ---
    st.markdown("---")
    c1, c2 = st.columns([1, 1])

    with c1:
        with st.expander("Show Optimal Tilt Analytics (Detailed)"):
            st.write("This table shows the best tilt angle for *each specific month* to maximize output.")
            st.dataframe(monthly_best, use_container_width=True)

    with c2:
        st.success("✅ Report generated successfully!")
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_buffer,
            file_name="Solar_Ninja_Report.pdf",
            mime="application/pdf",
            type="primary" 
        )
