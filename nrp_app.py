import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="NRP Calculator",
    page_icon="🎯",
    layout="wide"
)

# Title
st.title("🎯 National Reserve Program - Interactive Calculator")
st.markdown("---")

# Sidebar for inputs
with st.sidebar:
    st.header("📊 Input Parameters")
    
    st.subheader("🇩🇪 Germany (DE)")
    stock_de = st.number_input("Stock (units)", value=120, key="stock_de")
    forecast_de = st.number_input("Weekly Forecast", value=30, key="forecast_de")
    cppu_de = st.number_input("CPPU ($)", value=3.00, step=0.1, key="cppu_de")
    
    st.subheader("🇫🇷 France (FR)")
    stock_fr = st.number_input("Stock (units)", value=80, key="stock_fr")
    forecast_fr = st.number_input("Weekly Forecast", value=25, key="forecast_fr")
    cppu_fr = st.number_input("CPPU ($)", value=2.80, step=0.1, key="cppu_fr")
    
    st.subheader("🇪🇸 Spain (ES)")
    stock_es = st.number_input("Stock (units)", value=0, key="stock_es")
    forecast_es = st.number_input("Weekly Forecast", value=15, key="forecast_es")
    cppu_es = st.number_input("CPPU ($)", value=2.00, step=0.1, key="cppu_es")
    
    st.subheader("🇮🇹 Italy (IT)")
    stock_it = st.number_input("Stock (units)", value=0, key="stock_it")
    forecast_it = st.number_input("Weekly Forecast", value=10, key="forecast_it")
    cppu_it = st.number_input("CPPU ($)", value=1.80, step=0.1, key="cppu_it")
    
    st.markdown("---")
    st.subheader("🌍 Global Parameters")
    
    po_status = st.selectbox(
        "PO Status",
        ["No PO (CR > 25%)", "No PO (CR < 25%)", "Incoming PO", "EoL Product"]
    )
    
    po_arrival = st.number_input("PO Arrival (weeks)", value=8.0, step=0.5)
    lead_time = st.number_input("Vendor Lead Time (days)", value=14)
    cr_rate = st.number_input("Confirmation Rate (%)", value=30, min_value=0, max_value=100)
    oor_cost = st.number_input("OOR Cost ($)", value=1.50, step=0.1)
    max_woc = st.number_input("Max Healthy WoC", value=7)

# Calculate button
if st.sidebar.button("🚀 Calculate", type="primary"):
    # EU Totals
    S_EU = stock_de + stock_fr + stock_es + stock_it
    F_EU = forecast_de + forecast_fr + forecast_es + forecast_it
    WoC_EU = S_EU / F_EU if F_EU > 0 else 0
    
    # T_arrival calculation
    if po_status == "EoL Product":
        T_arrival_weeks = 999
    elif po_status == "Incoming PO":
        T_arrival_weeks = po_arrival
    elif po_status == "No PO (CR < 25%)":
        T_arrival_weeks = (2 * lead_time) / 7
    else:
        T_arrival_weeks = lead_time / 7
    
    # CPPU_avg
    cppu_sum = 0
    forecast_sum = 0
    if stock_de > 0:
        cppu_sum += cppu_de * forecast_de
        forecast_sum += forecast_de
    if stock_fr > 0:
        cppu_sum += cppu_fr * forecast_fr
        forecast_sum += forecast_fr
    if stock_es > 0:
        cppu_sum += cppu_es * forecast_es
        forecast_sum += forecast_es
    if stock_it > 0:
        cppu_sum += cppu_it * forecast_it
        forecast_sum += forecast_it
    
    CPPU_avg = cppu_sum / forecast_sum if forecast_sum > 0 else 0
    
    # Display EU Summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total EU Stock", f"{S_EU:.0f} units")
    with col2:
        st.metric("Total Forecast", f"{F_EU:.1f} units/week")
    with col3:
        st.metric("Current WoC", f"{WoC_EU:.2f} weeks")
    with col4:
        st.metric("Avg CPPU", f"${CPPU_avg:.2f}")
    
    st.markdown("---")
    
    # Find zero-stock MPs
    zero_stock_mps = []
    if stock_it == 0:
        zero_stock_mps.append({"name": "IT", "forecast": forecast_it, "cppu": cppu_it})
    if stock_es == 0:
        zero_stock_mps.append({"name": "ES", "forecast": forecast_es, "cppu": cppu_es})
    if stock_fr == 0:
        zero_stock_mps.append({"name": "FR", "forecast": forecast_fr, "cppu": cppu_fr})
    if stock_de == 0:
        zero_stock_mps.append({"name": "DE", "forecast": forecast_de, "cppu": cppu_de})
    
    zero_stock_mps.sort(key=lambda x: x["forecast"])
    
    # Sequential optimization
    F_EU_remaining = F_EU
    decisions = []
    
    for mp in zero_stock_mps:
        cppu_effective = mp["cppu"] - oor_cost
        pass_cppu = cppu_effective <= CPPU_avg
        
        WoC_new = S_EU / (F_EU_remaining - mp["forecast"]) if (F_EU_remaining - mp["forecast"]) > 0 else 999
        pass_woc_health = WoC_new <= max_woc
        pass_woc_depletion = T_arrival_weeks >= 999 or WoC_new < T_arrival_weeks
        
        decision = "TURN_OFF" if (pass_cppu and pass_woc_health and pass_woc_depletion) else "KEEP_ACTIVE"
        
        decisions.append({
            "MP": mp["name"],
            "CPPU Effective": cppu_effective,
            "Pass CPPU": pass_cppu,
            "New WoC": WoC_new,
            "Pass WoC Health": pass_woc_health,
            "Pass Depletion": pass_woc_depletion,
            "Decision": decision
        })
        
        if decision == "TURN_OFF":
            F_EU_remaining -= mp["forecast"]
    
    # Display decisions
    st.subheader("📋 Marketplace Decisions")
    
    for d in decisions:
        with st.expander(f"🔍 {d['MP']} - {d['Decision']}", expanded=True):
            if d['Decision'] == 'TURN_OFF':
                st.success("✅ TURN OFF THIS MARKETPLACE")
            else:
                st.warning("⚠️ KEEP ACTIVE")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Step 1: CPPU Check**")
                st.write(f"CPPU Effective: ${d['CPPU Effective']:.2f}")
                st.write(f"vs Avg CPPU: ${CPPU_avg:.2f}")
                if d['Pass CPPU']:
                    st.success("✓ PASS - Not profitable with OOR")
                else:
                    st.error("✗ FAIL - Still profitable")
            
            with col2:
                st.write("**Step 2: WoC Health**")
                st.write(f"New WoC: {d['New WoC']:.2f} weeks")
                if d['Pass WoC Health']:
                    st.success(f"✓ PASS - Under {max_woc} weeks")
                else:
                    st.error(f"✗ FAIL - Would exceed {max_woc} weeks")
            
            st.write("**Step 3: Depletion Timing**")
            st.write(f"Will deplete in: {d['New WoC']:.2f} weeks")
            st.write(f"Stock arrives in: {'Never' if T_arrival_weeks >= 999 else f'{T_arrival_weeks:.1f} weeks'}")
            if d['Pass Depletion']:
                st.success("✓ PASS - Will deplete before arrival")
            else:
                st.error("✗ FAIL - Won't deplete in time")
    
    # Final state
    st.markdown("---")
    st.subheader("🎯 Final State After Optimization")
    
    final_woc = S_EU / F_EU_remaining if F_EU_remaining > 0 else 999
    turned_off = [d['MP'] for d in decisions if d['Decision'] == 'TURN_OFF']
    kept_active = [d['MP'] for d in decisions if d['Decision'] == 'KEEP_ACTIVE']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("New WoC", f"{final_woc:.2f} weeks")
    with col2:
        st.metric("Turned Off", ", ".join(turned_off) if turned_off else "None")
    with col3:
        st.metric("Active MPs", ", ".join(kept_active) if kept_active else "All")
    
    # Visualization
    st.markdown("---")
    st.subheader("📊 Visual Analysis")
    
    # Create comparison chart
    df_comparison = pd.DataFrame({
        "Scenario": ["Before NRP", "After NRP"],
        "WoC": [WoC_EU, final_woc],
        "Active MPs": [4, 4 - len(turned_off)]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_comparison["Scenario"],
        y=df_comparison["WoC"],
        name="Weeks of Coverage",
        marker_color=['#667eea', '#28a745']
    ))
    
    fig.add_hline(y=max_woc, line_dash="dash", line_color="red", 
                  annotation_text=f"Max Healthy WoC ({max_woc})")
    
    if T_arrival_weeks < 999:
        fig.add_hline(y=T_arrival_weeks, line_dash="dash", line_color="orange",
                      annotation_text=f"PO Arrival ({T_arrival_weeks:.1f}w)")
    
    fig.update_layout(
        title="WoC Comparison: Before vs After NRP",
        yaxis_title="Weeks of Coverage",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Adjust parameters in the sidebar and click **Calculate** to see results")