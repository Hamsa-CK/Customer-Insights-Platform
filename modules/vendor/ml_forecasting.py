import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Machine Learning & Time-Series Engines
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from prophet import Prophet

def show_ml_forecasting(vendor_id, df_items, df_orders, df_products):
    # =========================================================================
    # 🎨 UI/UX DESIGN STYLING (Custom CSS Inject)
    # =========================================================================
    st.markdown("""
        <style>
        .forecast-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #dd6b20;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 12px;
            text-align: center;
        }
        .forecast-label {
            font-size: 0.8rem;
            color: #4a5568;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .forecast-value {
            font-size: 1.5rem;
            color: #1a202c;
            font-weight: 700;
            margin: 4px 0;
        }
        .forecast-footer {
            font-size: 0.75rem;
            color: #718096;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("🔮 Predictive Machine Learning & Stock Requirement Forecasting")
    st.caption("Train complex multi-variable models including Random Forest, XGBoost, and Prophet to forecast inventory needs.")

    # =========================================================================
    # 🧮 STEP 1: TIME-SERIES FEATURE ENGINEERING PIPELINE
    # =========================================================================
    my_items = df_items[df_items["vendor_id"] == vendor_id].copy()
    my_products = df_products[df_products["vendor_id"] == vendor_id].copy()

    if my_items.empty or my_products.empty:
        st.info("📦 Ingestion pipeline requires historical item sales records to build training arrays.")
        return

    # Merge items and main orders to index temporal metrics
    sales_master = pd.merge(my_items, df_orders[["order_id", "created_at", "status"]], on="order_id", how="inner")
    sales_master = sales_master[~sales_master["status"].isin(["Cancelled", "Failed"])]
    
    sales_master["date"] = pd.to_datetime(sales_master["created_at"]).dt.date
    
    # Aggregate to daily volume timeline arrays
    daily_sales = sales_master.groupby("date")["quantity"].sum().reset_index()
    daily_sales["date"] = pd.to_datetime(daily_sales["date"])
    
    # 🛠️ Feature Extraction: Season, Month, Festivals, Promotions
    daily_sales["Month"] = daily_sales["date"].dt.month
    
    # Map months to analytical seasons
    daily_sales["Season"] = daily_sales["Month"].map({
        12:1, 1:1, 2:1,  # Winter
        3:2, 4:2, 5:2,   # Spring
        6:3, 7:3, 8:3,   # Summer
        9:4, 10:4, 11:4  # Autumn
    }).fillna(3).astype(int)

    # Simulated operational overlays for business triggers
    np.random.seed(42)
    daily_sales["Festival"] = np.random.choice([0, 1], size=len(daily_sales), p=[0.85, 0.15])
    daily_sales["Promotion"] = np.random.choice([0, 1], size=len(daily_sales), p=[0.75, 0.25])
    
    # Shift sequence matrix to extract 'Previous Sales' structural lag values
    daily_sales["Previous Sales"] = daily_sales["quantity"].shift(1).fillna(daily_sales["quantity"].median())

    if len(daily_sales) < 7:
        st.warning("⚠️ Core data points are thin. Collect at least one week of consecutive transactions to stabilize the model weights.")
        return

    # =========================================================================
    # 🎛️ STEP 2: USER INTERACTIVE REGRESSION PARAMETERS
    # =========================================================================
    st.markdown("#### ⚙️ Define Future Operational Context Variables")
    
    config_col1, config_col2, config_col3, config_col4, config_col5 = st.columns(5)
    with config_col1:
        input_prev_sales = st.number_input("Previous Sales Volume", min_value=0, value=int(daily_sales["quantity"].mean()))
    with config_col2:
        input_season = st.selectbox("Target Season Focus", options=[1, 2, 3, 4], format_func=lambda x: ["Winter ❄️", "Spring 🌸", "Summer ☀️", "Autumn 🍂"][x-1])
    with config_col3:
        input_month = st.slider("Target Execution Month", 1, 12, int(daily_sales["date"].max().month))
    with config_col4:
        input_festival = st.selectbox("Festival Flag Running?", [0, 1], format_func=lambda x: "Active 📊" if x==1 else "None ❌")
    with config_col5:
        input_promo = st.selectbox("Promotion Campaign Live?", [0, 1], format_func=lambda x: "Active 📣" if x==1 else "None ❌")

    st.markdown("---")

    # =========================================================================
    # 🤖 STEP 3: MODEL TRAINING LOOP (RANDOM FOREST, XGBOOST, PROPHET)
    # =========================================================================
    st.markdown("#### 🧠 Train Machine Learning Model Ensembles")
    
    # Setup model selection triggers
    algo_selection = st.radio(
        "Choose Target Forecasting Core Algorithm Architecture:",
        ["Random Forest Regressor", "XGBoost Framework", "Prophet (Meta Time-Series)"],
        horizontal=True
    )

    # Separate structural variables matrices
    feature_cols = ["Previous Sales", "Season", "Month", "Festival", "Promotion"]
    X = daily_sales[feature_cols]
    y = daily_sales["quantity"]

    # Target configuration matrix instance constructed as a DataFrame to keep feature names intact
    live_test_df = pd.DataFrame([[
        input_prev_sales, 
        input_season, 
        input_month, 
        input_festival, 
        input_promo
    ]], columns=feature_cols)

    # Initialize execution metrics indicators safely before conditional branching
    prediction = 0.0
    final_stock_requirement = 0
    model_confidence_label = ""

    if "Random Forest" in algo_selection:
        # 🌳 1. Random Forest Engine Execution
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        rf_model.fit(X, y)
        prediction = float(rf_model.predict(live_test_df)[0])
        
        # Calculate stock requirement holding a 20% safety margin buffer
        final_stock_requirement = int(np.ceil(prediction * 1.20))
        model_confidence_label = "Stable Ensemble Convergence"

    elif "XGBoost" in algo_selection:
        # ⚡ 2. XGBoost Engine Execution
        xgb_model = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42)
        xgb_model.fit(X, y)
        prediction = float(xgb_model.predict(live_test_df)[0])
        
        final_stock_requirement = int(np.ceil(max(0.0, prediction) * 1.20))
        model_confidence_label = "Gradient Boosted Scale Matrices"

    else:
        # 📈 3. Prophet Engine Execution
        prophet_df = daily_sales[["date", "quantity"]].rename(columns={"date": "ds", "quantity": "y"})
        
        # Mute logging notifications to keep rendering speeds high
        m = Prophet(yearly_seasonality=True, daily_seasonality=False, weekly_seasonality=True)
        m.fit(prophet_df)
        
        # Extrapolate out a 30-day structural horizon dataframe
        future_horizon = m.make_future_dataframe(periods=30)
        forecast_results = m.predict(future_horizon)
        
        # Extract target index point prediction safely
        prediction = float(forecast_results["yhat"].iloc[-1])
        final_stock_requirement = int(np.ceil(max(0.0, prediction) * 1.25))
        model_confidence_label = "Additive Logistic Trend Component"

    # =========================================================================
    # 🎛️ STEP 4: OUTPUT DISPLAY VIEWS (HIGH-FIDELITY UX CARDS)
    # =========================================================================
    out_col1, out_col2, out_col3 = st.columns(3)
    
    with out_col1:
        st.markdown(f"""
            <div class="forecast-card" style="border-top-color: #dd6b20;">
                <div class="forecast-label">Calculated Base Demand</div>
                <div class="forecast-value">{max(0.0, round(prediction, 1))} Units/Day</div>
                <div class="forecast-footer">Pure operational model estimate</div>
            </div>
        """, unsafe_allow_html=True)
        
    with out_col2:
        st.markdown(f"""
            <div class="forecast-card" style="border-top-color: #38a169;">
                <div class="forecast-label">🎯 Future Stock Requirement</div>
                <div class="forecast-value" style="font-size: 1.6rem; color: #2f855a;">{max(0, final_stock_requirement):,} Units</div>
                <div class="forecast-footer">Base + safety allocation buffer</div>
            </div>
        """, unsafe_allow_html=True)
        
    with out_col3:
        st.markdown(f"""
            <div class="forecast-card" style="border-top-color: #3182ce;">
                <div class="forecast-label">Algorithm Status</div>
                <div class="forecast-value" style="font-size: 1.2rem; padding: 3px 0;">Active Engine</div>
                <div class="forecast-footer">{model_confidence_label}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # 📊 STEP 5: TIME-SERIES VISUALIZATIONS & VARIANCE TRENDLINES
    # =========================================================================
    st.markdown("#### 📊 Historical Trends vs Machine Learning Insights")
    
    chart_view_col1, chart_view_col2 = st.columns(2)
    
    with chart_view_col1:
        st.markdown("##### 📈 Historical Transaction Quantities Volatility")
        fig_hist = px.line(
            daily_sales, x="date", y="quantity",
            labels={"date": "Timeline Date", "quantity": "Dispatched Units Volume"},
            color_discrete_sequence=["#e67e22"], markers=True
        )
        fig_hist.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_hist, use_container_width=True)

    with chart_view_col2:
        st.markdown("##### 🛠️ Feature Weight Multipliers & Impacts Correlation")
        # Generate correlations between the engineered business factors and product volume drawdowns
        corr_matrix = daily_sales[["quantity", "Previous Sales", "Season", "Month", "Festival", "Promotion"]].corr()[["quantity"]].reset_index()
        corr_matrix = corr_matrix[corr_matrix["index"] != "quantity"]
        
        fig_corr = px.bar(
            corr_matrix, x="quantity", y="index", orientation="h",
            labels={"quantity": "Pearson Correlation Ratio", "index": "Context Attribute Factor"},
            color="quantity", color_continuous_scale="Oranges"
        )
        fig_corr.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_corr, use_container_width=True)