import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="NRP Calculator",
    page_icon="🎯",
    layout="wide"
)

# Title with documentation link
col_title, col_link = st.columns([4, 1])
with col_title:
    st.title("🎯 National Reserve Program - Interactive Calculator")
with col_link:
    st.markdown("### [📚 View Logic Documentation](https://quip-amazon.com/s98vAFbWomhP/National-Reserve-program-20)")

st.markdown("---")

# Sidebar for GLOBAL parameters only
with st.sidebar:
    st.header("🌍 Global Parameters")
    
    po_status = st.selectbox(
        "PO Status",
        ["No PO (CR > 25%)", "No PO (CR < 25%)", "Incoming PO", "EoL Product"]
    )
    
    po_arrival = st.number_input("PO Arrival (weeks)", value=8.0, step=0.5)
    lead_time = st.number_input("Vendor Lead Time (days)", value=14)
    cr_rate = st.number_input("Confirmation Rate (%)", value=30, min_value=0, max_value=100)
    oor_cost = st.number_input("OOR Cost ($)", value=1.50, step=0.1)
    max_woc = st.number_input("Max Healthy WoC", value=7)
    
    st.markdown("---")
    calculate_button = st.button("🚀 Calculate NRP Optimization", type="primary", use_container_width=True)

# MARKETPLACE INPUTS AS TABLE
st.subheader("📊 Marketplace Input Parameters")

# Create input table
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🇩🇪 Germany (DE)")
    stock_de = st.number_input("Stock (units)", value=120, key="stock_de", label_visibility="visible")
    forecast_de = st.number_input("Weekly Forecast", value=30, key="forecast_de", label_visibility="visible")
    cppu_de = st.number_input("CPPU ($)", value=3.00, step=0.1, key="cppu_de", label_visibility="visible")

with col2:
    st.markdown("### 🇫🇷 France (FR)")
    stock_fr = st.number_input("Stock (units)", value=80, key="stock_fr", label_visibility="visible")
    forecast_fr = st.number_input("Weekly Forecast", value=25, key="forecast_fr", label_visibility="visible")
    cppu_fr = st.number_input("CPPU ($)", value=2.80, step=0.1, key="cppu_fr", label_visibility="visible")

with col3:
    st.markdown("### 🇪🇸 Spain (ES)")
    stock_es = st.number_input("Stock (units)", value=0, key="stock_es", label_visibility="visible")
    forecast_es = st.number_input("Weekly Forecast", value=15, key="forecast_es", label_visibility="visible")
    cppu_es = st.number_input("CPPU ($)", value=2.00, step=0.1, key="cppu_es", label_visibility="visible")

with col4:
    st.markdown("### 🇮🇹 Italy (IT)")
    stock_it = st.number_input("Stock (units)", value=0, key="stock_it", label_visibility="visible")
    forecast_it = st.number_input("Weekly Forecast", value=10, key="forecast_it", label_visibility="visible")
    cppu_it = st.number_input("CPPU ($)", value=1.80, step=0.1, key="cppu_it", label_visibility="visible")

st.markdown("---")

# Calculate button logic
# Calculate button logic
if calculate_button:
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
    
    # CPPU_avg for MPs with stock
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
    
    # Calculate CP BEFORE optimization
    def calculate_cp_before(s_de, s_fr, s_es, s_it, f_de, f_fr, f_es, f_it, c_de, c_fr, c_es, c_it, s_eu, f_eu, oor):
        if f_eu == 0:
            return 0
        woc = s_eu / f_eu
        
        # Units sold per MP (proportional to forecast)
        units_de = f_de * woc
        units_fr = f_fr * woc
        units_es = f_es * woc
        units_it = f_it * woc
        
        # Calculate CP (with OOR penalty for zero-stock MPs)
        cp_de = units_de * c_de
        cp_fr = units_fr * c_fr
        cp_es = units_es * (c_es - oor if s_es == 0 else c_es)
        cp_it = units_it * (c_it - oor if s_it == 0 else c_it)
        
        return cp_de + cp_fr + cp_es + cp_it
    
    cp_before = calculate_cp_before(
        stock_de, stock_fr, stock_es, stock_it,
        forecast_de, forecast_fr, forecast_es, forecast_it,
        cppu_de, cppu_fr, cppu_es, cppu_it,
        S_EU, F_EU, oor_cost
    )
    
    # Display EU Summary
    st.subheader("📈 EU Summary Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total EU Stock", f"{S_EU:.0f} units")
    with col2:
        st.metric("Total Forecast", f"{F_EU:.1f} units/week")
    with col3:
        st.metric("Current WoC", f"{WoC_EU:.2f} weeks")
    with col4:
        st.metric("Avg CPPU (Stock MPs)", f"${CPPU_avg:.2f}")
    with col5:
        st.metric("Stock Arrival", f"{'Never (EoL)' if T_arrival_weeks >= 999 else f'{T_arrival_weeks:.1f}w'}")
    
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
    
    if len(zero_stock_mps) == 0:
        st.info("✅ All marketplaces have stock. No NRP optimization needed.")
    else:
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
                "Forecast": mp["forecast"],
                "CPPU": mp["cppu"],
                "CPPU Effective": cppu_effective,
                "Pass CPPU": pass_cppu,
                "New WoC": WoC_new,
                "Pass WoC Health": pass_woc_health,
                "Pass Depletion": pass_woc_depletion,
                "Decision": decision
            })
            
            if decision == "TURN_OFF":
                F_EU_remaining -= mp["forecast"]
        
        # ============= FIX 1: Calculate active MPs correctly =============
        # Start with all MPs
        all_mps = ["DE", "FR", "ES", "IT"]
        
        # Get turned off MPs
        turned_off = [d['MP'] for d in decisions if d['Decision'] == 'TURN_OFF']
        
        # Active MPs = all MPs minus turned off ones
        kept_active = [mp for mp in all_mps if mp not in turned_off]
        # ================================================================
        
        # Calculate CP AFTER optimization
        active_forecast_de = forecast_de if "DE" in kept_active else 0
        active_forecast_fr = forecast_fr if "FR" in kept_active else 0
        active_forecast_es = forecast_es if "ES" in kept_active else 0
        active_forecast_it = forecast_it if "IT" in kept_active else 0
        
        f_total_after = active_forecast_de + active_forecast_fr + active_forecast_es + active_forecast_it
        
        if f_total_after > 0:
            cp_after = (
                (active_forecast_de / f_total_after) * S_EU * cppu_de +
                (active_forecast_fr / f_total_after) * S_EU * cppu_fr +
                (active_forecast_es / f_total_after) * S_EU * cppu_es +
                (active_forecast_it / f_total_after) * S_EU * cppu_it
            )
        else:
            cp_after = 0
        
        # Display decisions with IMPROVED LAYOUT
        st.subheader("📋 Marketplace Decision Analysis")
        
        for d in decisions:
            with st.expander(f"🔍 {d['MP']} - {d['Decision']}", expanded=True):
                # Decision banner
                if d['Decision'] == 'TURN_OFF':
                    st.success("✅ TURN OFF THIS MARKETPLACE")
                else:
                    st.warning("⚠️ KEEP ACTIVE")
                
                # THREE COLUMNS FOR THREE STEPS (IMPROVED LAYOUT)
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### Step 1: CPPU Check")
                    st.write(f"**CPPU Original:** ${d['CPPU']:.2f}")
                    st.write(f"**OOR Cost:** -${oor_cost:.2f}")
                    st.write(f"**CPPU Effective:** ${d['CPPU Effective']:.2f}")
                    st.write(f"**vs Avg CPPU:** ${CPPU_avg:.2f}")
                    if d['Pass CPPU']:
                        st.success("✓ PASS - Not profitable with OOR")
                    else:
                        st.error("✗ FAIL - Still profitable, keep active")
                
                with col2:
                    st.markdown("#### Step 2: WoC Health")
                    st.write(f"**New WoC:** {d['New WoC']:.2f} weeks")
                    st.write(f"**Max Allowed:** {max_woc} weeks")
                    st.write(f"**Forecast Removed:** {d['Forecast']} units/week")
                    if d['Pass WoC Health']:
                        st.success(f"✓ PASS - Remains healthy")
                    else:
                        st.error(f"✗ FAIL - Would exceed {max_woc} weeks")
                
                with col3:
                    st.markdown("#### Step 3: Depletion Timing")
                    st.write(f"**Will Deplete In:** {d['New WoC']:.2f} weeks")
                    st.write(f"**Stock Arrives In:** {'Never' if T_arrival_weeks >= 999 else f'{T_arrival_weeks:.1f} weeks'}")
                    st.write(f"**Buffer:** {(T_arrival_weeks - d['New WoC']):.2f} weeks" if T_arrival_weeks < 999 else "N/A (EoL)")
                    if d['Pass Depletion']:
                        st.success("✓ PASS - Will deplete before arrival")
                    else:
                        st.error("✗ FAIL - Won't deplete in time")
        
        # Final state
        st.markdown("---")
        st.subheader("🎯 Final State After Optimization")
        
        final_woc = S_EU / F_EU_remaining if F_EU_remaining > 0 else 999
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("New WoC", f"{final_woc:.2f} weeks", delta=f"{final_woc - WoC_EU:+.2f} weeks")
        with col2:
            st.metric("Active Forecast", f"{F_EU_remaining:.1f} units/week", delta=f"{F_EU_remaining - F_EU:.1f}")
        with col3:
            st.metric("Turned Off MPs", ", ".join(turned_off) if turned_off else "None")
        with col4:
            st.metric("Active MPs", ", ".join(kept_active))  # ← FIX: Removed "if kept_active else All"
        
        # ==================== COMPARISON TABLE ====================
        st.markdown("---")
        st.subheader("📊 Before vs After Comparison Table")
        
        # ============= FIX 3: Better explanation of CBF calculation =============
        # CBF units BEFORE: All units sold to zero-stock MPs require cross-border shipment
        cbf_units_before = 0
        if stock_es == 0:
            cbf_units_before += (forecast_es * WoC_EU)  # ES demand × weeks of stock
        if stock_it == 0:
            cbf_units_before += (forecast_it * WoC_EU)  # IT demand × weeks of stock
        if stock_de == 0:
            cbf_units_before += (forecast_de * WoC_EU)
        if stock_fr == 0:
            cbf_units_before += (forecast_fr * WoC_EU)
        
        # CBF units AFTER: Only active zero-stock MPs need CBF (turned-off MPs = 0 CBF)
        cbf_units_after = 0
        for mp_name, stock, forecast in [("DE", stock_de, forecast_de), ("FR", stock_fr, forecast_fr), 
                                          ("ES", stock_es, forecast_es), ("IT", stock_it, forecast_it)]:
            if stock == 0 and mp_name in kept_active:  # Zero stock AND still active
                cbf_units_after += (forecast * final_woc)
        # ========================================================================
        
        cbf_savings = (cbf_units_before - cbf_units_after) * oor_cost
        cp_improvement = cp_after - cp_before
        cp_improvement_pct = (cp_improvement / cp_before * 100) if cp_before > 0 else 0
        
        comparison_data = {
            "Metric": [
                "Total Stock (units)",
                "Active Forecast (units/week)",
                "Weeks of Coverage",
                "Active Marketplaces",
                "Cross-Border Units",
                "OOR Shipping Cost",
                "Total Contribution Profit",
                "CP Improvement"
            ],
            "Before NRP": [
                f"{S_EU:.0f}",
                f"{F_EU:.1f}",
                f"{WoC_EU:.2f}",
                "DE, FR, ES, IT",
                f"{cbf_units_before:.0f}",  # ← FIX 2: Integer display
                f"${cbf_units_before * oor_cost:.2f}",
                f"${cp_before:.2f}",
                "-"
            ],
            "After NRP": [
                f"{S_EU:.0f}",
                f"{F_EU_remaining:.1f}",
                f"{final_woc:.2f}",
                ", ".join(kept_active),  # ← FIX 1: Now correct
                f"{cbf_units_after:.0f}",  # ← FIX 2: Integer display
                f"${cbf_units_after * oor_cost:.2f}",
                f"${cp_after:.2f}",
                f"+${cp_improvement:.2f} ({cp_improvement_pct:+.1f}%)"
            ],
            "Change": [
                "0",
                f"{F_EU_remaining - F_EU:.1f}",
                f"{final_woc - WoC_EU:+.2f}",
                f"{len(turned_off)} turned off",
                f"{int(cbf_units_after - cbf_units_before)}",  # ← FIX 2: Integer
                f"-${cbf_savings:.2f}",
                f"+${cp_improvement:.2f}",
                f"{cp_improvement_pct:+.1f}%"
            ]
        }
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        
        # Highlight key improvements
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 CP Improvement", f"${cp_improvement:.2f}", delta=f"{cp_improvement_pct:+.1f}%")
        with col2:
            st.metric("📦 CBF Units Avoided", f"{int(cbf_units_before - cbf_units_after)}", delta=f"-{((cbf_units_before - cbf_units_after) / cbf_units_before * 100) if cbf_units_before > 0 else 0:.1f}%")
        with col3:
            st.metric("💵 OOR Cost Saved", f"${cbf_savings:.2f}", delta="Savings")
        
        # ==================== ADDITIONAL VISUALIZATIONS ====================
        st.markdown("---")
        st.subheader("📈 Advanced Analytics & Visualizations")
        
        # Row 1: WoC Comparison + CP Breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            # WoC Comparison Chart
            fig_woc = go.Figure()
            fig_woc.add_trace(go.Bar(
                x=["Before NRP", "After NRP"],
                y=[WoC_EU, final_woc],
                text=[f"{WoC_EU:.2f}w", f"{final_woc:.2f}w"],
                textposition='auto',
                marker_color=['#667eea', '#28a745']
            ))
            
            fig_woc.add_hline(y=max_woc, line_dash="dash", line_color="red", 
                          annotation_text=f"Max Healthy WoC ({max_woc})")
            
            if T_arrival_weeks < 999:
                fig_woc.add_hline(y=T_arrival_weeks, line_dash="dash", line_color="orange",
                              annotation_text=f"PO Arrival ({T_arrival_weeks:.1f}w)")
            
            fig_woc.update_layout(
                title="Weeks of Coverage Comparison",
                yaxis_title="Weeks",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig_woc, use_container_width=True)
        
        with col2:
            # CP Breakdown by Marketplace
            cp_breakdown_before = []
            cp_breakdown_after = []
            mp_labels = []
            
            for mp_name, stock, forecast, cppu in [
                ("DE", stock_de, forecast_de, cppu_de),
                ("FR", stock_fr, forecast_fr, cppu_fr),
                ("ES", stock_es, forecast_es, cppu_es),
                ("IT", stock_it, forecast_it, cppu_it)
            ]:
                mp_labels.append(mp_name)
                
                # Before
                units_before = (forecast / F_EU * S_EU) if F_EU > 0 else 0
                cp_mp_before = units_before * (cppu - oor_cost if stock == 0 else cppu)
                cp_breakdown_before.append(cp_mp_before)
                
                # After
                is_active = mp_name in kept_active
                if is_active and f_total_after > 0:
                    forecast_after = forecast if mp_name in kept_active else 0
                    units_after = (forecast_after / f_total_after * S_EU)
                    cp_mp_after = units_after * cppu
                else:
                    cp_mp_after = 0
                cp_breakdown_after.append(cp_mp_after)
            
            fig_cp = go.Figure()
            fig_cp.add_trace(go.Bar(
                name='Before NRP',
                x=mp_labels,
                y=cp_breakdown_before,
                marker_color='#667eea'
            ))
            fig_cp.add_trace(go.Bar(
                name='After NRP',
                x=mp_labels,
                y=cp_breakdown_after,
                marker_color='#28a745'
            ))
            
            fig_cp.update_layout(
                title="Contribution Profit by Marketplace",
                yaxis_title="CP ($)",
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig_cp, use_container_width=True)
        
        # Row 2: Stock Depletion Timeline + Decision Matrix
        col1, col2 = st.columns(2)
        
        with col1:
            # Stock Depletion Timeline
            weeks = list(range(0, int(max(final_woc, WoC_EU, T_arrival_weeks if T_arrival_weeks < 999 else 10)) + 2))
            stock_before = [max(0, S_EU - (F_EU * w)) for w in weeks]
            stock_after = [max(0, S_EU - (F_EU_remaining * w)) for w in weeks]
            
            fig_timeline = go.Figure()
            fig_timeline.add_trace(go.Scatter(
                x=weeks,
                y=stock_before,
                mode='lines+markers',
                name='Before NRP',
                line=dict(color='#667eea', width=3)
            ))
            fig_timeline.add_trace(go.Scatter(
                x=weeks,
                y=stock_after,
                mode='lines+markers',
                name='After NRP',
                line=dict(color='#28a745', width=3)
            ))
            
            if T_arrival_weeks < 999:
                fig_timeline.add_vline(x=T_arrival_weeks, line_dash="dash", line_color="orange",
                                   annotation_text="PO Arrival")
            
            fig_timeline.update_layout(
                title="Stock Depletion Timeline",
                xaxis_title="Weeks",
                yaxis_title="Remaining Stock (units)",
                height=400
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        with col2:
            # Decision Matrix Heatmap
            decision_matrix = []
            for d in decisions:
                decision_matrix.append({
                    "MP": d["MP"],
                    "CPPU Check": 1 if d["Pass CPPU"] else 0,
                    "WoC Health": 1 if d["Pass WoC Health"] else 0,
                    "Depletion Timing": 1 if d["Pass Depletion"] else 0,
                })
            
            df_matrix = pd.DataFrame(decision_matrix)
            
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=df_matrix[["CPPU Check", "WoC Health", "Depletion Timing"]].values.T,
                x=df_matrix["MP"],
                y=["CPPU Check", "WoC Health", "Depletion Timing"],
                colorscale=[[0, '#dc3545'], [1, '#28a745']],
                text=[["✗" if val == 0 else "✓" for val in row] for row in df_matrix[["CPPU Check", "WoC Health", "Depletion Timing"]].values.T],
                texttemplate="%{text}",
                textfont={"size": 20, "color": "white"},
                showscale=False
            ))
            
            fig_heatmap.update_layout(
                title="Decision Matrix: Check Results",
                height=400
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Row 3: Detailed Metrics Table
        st.markdown("---")
        st.subheader("📋 Detailed Calculation Metrics")
        
        detailed_metrics = []
        for mp_name, stock, forecast, cppu in [
            ("DE", stock_de, forecast_de, cppu_de),
            ("FR", stock_fr, forecast_fr, cppu_fr),
            ("ES", stock_es, forecast_es, cppu_es),
            ("IT", stock_it, forecast_it, cppu_it)
        ]:
            is_zero_stock = stock == 0
            is_turned_off = mp_name in turned_off
            
            units_sold_before = (forecast / F_EU * S_EU) if F_EU > 0 else 0
            cp_before_mp = units_sold_before * (cppu - oor_cost if is_zero_stock else cppu)
            
            if is_turned_off:
                units_sold_after = 0
                cp_after_mp = 0
            else:
                forecast_after = forecast
                units_sold_after = (forecast_after / f_total_after * S_EU) if f_total_after > 0 else 0
                cp_after_mp = units_sold_after * cppu
            
            detailed_metrics.append({
                "Marketplace": f"{mp_name}",
                "Stock": stock,
                "Forecast": forecast,
                "CPPU": f"${cppu:.2f}",
                "Status": "❌ Turned Off" if is_turned_off else "✅ Active",
                "Units Sold (Before)": f"{int(units_sold_before)}",  # ← FIX 2: Integer
                "Units Sold (After)": f"{int(units_sold_after)}",   # ← FIX 2: Integer
                "CP Before": f"${cp_before_mp:.2f}",
                "CP After": f"${cp_after_mp:.2f}",
                "CP Change": f"+${cp_after_mp - cp_before_mp:.2f}"
            })
        
        df_detailed = pd.DataFrame(detailed_metrics)
        st.dataframe(df_detailed, use_container_width=True, hide_index=True)
        
        # ============= FIX 3: Add explanation box for OOR calculation =============
        with st.expander("ℹ️ How are Cross-Border (OOR) Units Calculated?", expanded=False):
            st.markdown("""
            ### Before NRP:
            **Cross-border units** = Units sold to marketplaces with **zero stock**
            
            **Formula:** `CBF Units = Forecast × WoC` for each zero-stock MP
            
            **Example (Current Scenario):**
            """)
            
            if stock_es == 0 or stock_it == 0:
                explanation_data = []
                if stock_es == 0:
                    explanation_data.append({
                        "MP": "ES",
                        "Stock": 0,
                        "Forecast": f"{forecast_es} units/week",
                        "WoC": f"{WoC_EU:.2f} weeks",
                        "Calculation": f"{forecast_es} × {WoC_EU:.2f}",
                        "CBF Units": f"{forecast_es * WoC_EU:.1f}"
                    })
                if stock_it == 0:
                    explanation_data.append({
                        "MP": "IT",
                        "Stock": 0,
                        "Forecast": f"{forecast_it} units/week",
                        "WoC": f"{WoC_EU:.2f} weeks",
                        "Calculation": f"{forecast_it} × {WoC_EU:.2f}",
                        "CBF Units": f"{forecast_it * WoC_EU:.1f}"
                    })
                
                df_explanation = pd.DataFrame(explanation_data)
                st.dataframe(df_explanation, use_container_width=True, hide_index=True)
                
                st.markdown(f"""
                **Total CBF Before NRP:** {cbf_units_before:.1f} units
                
                **Why?** These MPs have no local stock, so ALL customer orders must be fulfilled 
                from other countries (DE/FR with stock), incurring ${oor_cost:.2f} extra shipping cost per unit.
                
                ### After NRP:
                When we **turn off** zero-stock MPs, their customers can't order anymore, so:
                - **CBF units = 0** for turned-off MPs
                - **Savings = {cbf_units_before:.1f} units × ${oor_cost:.2f} = ${cbf_units_before * oor_cost:.2f}**
                """)
            else:
                st.info("All marketplaces have stock, so no cross-border shipments needed!")
        # =========================================================================
        
        # Summary insights
        st.markdown("---")
        st.subheader("💡 Key Insights")
        
        insights = []
        
        if len(turned_off) > 0:
            insights.append(f"✅ **{len(turned_off)} marketplace(s) turned off:** {', '.join(turned_off)}")
            insights.append(f"📈 **WoC increased from {WoC_EU:.2f} to {final_woc:.2f} weeks** (+{final_woc - WoC_EU:.2f} weeks)")
        else:
            insights.append("ℹ️ **No marketplaces turned off** - optimization not beneficial in this scenario")
        
        if cp_improvement > 0:
            insights.append(f"💰 **CP improved by ${cp_improvement:.2f}** ({cp_improvement_pct:+.1f}%)")
        else:
            insights.append(f"💰 **CP impact: ${cp_improvement:.2f}** - optimization may reduce profit")
        
        if cbf_savings > 0:
            insights.append(f"📦 **Avoided {int(cbf_units_before - cbf_units_after)} cross-border shipments**, saving ${cbf_savings:.2f}")
        
        if final_woc < T_arrival_weeks or T_arrival_weeks >= 999:
            insights.append(f"✅ **Stock will deplete before next PO arrival** - no revenue loss risk")
        else:
            insights.append(f"⚠️ **Warning: Stock may not deplete in time** - review forecast accuracy")
        
        if final_woc > max_woc:
            insights.append(f"❌ **Alert: WoC exceeds healthy threshold** ({final_woc:.2f} > {max_woc}) - markdown risk")
        
        for insight in insights:
            st.markdown(insight)

else:
    st.info("👈 Set your parameters in the **sidebar** and marketplace inputs above, then click **Calculate** to see results")
    
    # Show sample data preview
    st.markdown("### 📝 Sample Input Preview")
    sample_data = pd.DataFrame({
        "Marketplace": ["🇩🇪 DE", "🇫🇷 FR", "🇪🇸 ES", "🇮🇹 IT"],
        "Stock": [120, 80, 0, 0],
        "Forecast": [30, 25, 15, 10],
        "CPPU": ["$3.00", "$2.80", "$2.00", "$1.80"]
    })
    st.dataframe(sample_data, use_container_width=True, hide_index=True)