from pathlib import Path
import runpy

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "hicks_landscaping.duckdb"
BUILD_SCRIPT = ROOT / "scripts" / "build_duckdb.py"

st.set_page_config(
    page_title="Hicks Analytics | Landscaping Performance Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            max-width: 1450px;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(120, 120, 120, 0.18);
        }
        .brand-kicker {
            font-size: 0.78rem;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            opacity: 0.65;
            margin-bottom: 0.25rem;
        }
        .brand-title {
            font-size: 2rem;
            font-weight: 760;
            line-height: 1.1;
            margin-bottom: 0.2rem;
        }
        .brand-subtitle {
            font-size: 1rem;
            opacity: 0.68;
            margin-bottom: 1.25rem;
        }
        .insight-card {
            border: 1px solid rgba(120,120,120,.22);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin-bottom: .7rem;
        }
        .insight-card strong {
            font-size: 1.02rem;
        }
        .story-hero {
            background: linear-gradient(135deg, rgba(20, 83, 45, .96), rgba(22, 101, 52, .82));
            color: white;
            border-radius: 20px;
            padding: 1.6rem 1.8rem;
            margin: .4rem 0 1.2rem 0;
            box-shadow: 0 12px 34px rgba(20, 83, 45, .16);
        }
        .story-hero h2 {
            color: white;
            margin: 0 0 .45rem 0;
        }
        .story-hero p {
            color: rgba(255, 255, 255, .88);
            margin: 0;
            max-width: 820px;
        }
        .story-callout {
            border-left: 5px solid #f59e0b;
            background: rgba(245, 158, 11, .09);
            border-radius: 0 14px 14px 0;
            padding: 1rem 1.15rem;
            margin: .8rem 0 1.1rem 0;
        }
        .story-step {
            text-transform: uppercase;
            letter-spacing: .1em;
            font-size: .74rem;
            font-weight: 700;
            opacity: .62;
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(120,120,120,.18);
            padding: 0.8rem 0.9rem;
            border-radius: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Data access
# -----------------------------
def require_database():
    if not DB_PATH.exists():
        with st.spinner("Preparing the synthetic portfolio data..."):
            try:
                runpy.run_path(str(BUILD_SCRIPT), run_name="__main__")
            except Exception as exc:
                st.error("The portfolio data could not be prepared. Please try again shortly.")
                st.exception(exc)
                st.stop()


@st.cache_data
def query(sql: str) -> pd.DataFrame:
    require_database()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


@st.cache_data
def load_base_data():
    jobs = query("select * from analytics.fct_job_profitability")
    estimates = query("select * from analytics.mart_estimate_performance")
    return jobs, estimates


jobs, estimates = load_base_data()
jobs["completed_date"] = pd.to_datetime(jobs["completed_date"])
jobs["completed_month"] = pd.to_datetime(jobs["completed_month"])

min_date = jobs["completed_date"].min().date()
max_date = jobs["completed_date"].max().date()


# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.markdown("## Hicks Analytics")
st.sidebar.caption("Landscaping Performance Hub")
st.sidebar.divider()

experience = st.sidebar.radio(
    "Experience",
    ["Guided Demo", "Explore Dashboard"],
    help="Follow a business story or explore the complete dashboard.",
)

all_cities = sorted(jobs["city"].dropna().unique().tolist())
all_services = sorted(jobs["service_name"].dropna().unique().tolist())
all_crews = sorted(jobs["crew_name"].dropna().unique().tolist())

if experience == "Guided Demo":
    page = "Guided Demo"
    date_range = (min_date, max_date)
    selected_cities = all_cities
    selected_services = all_services
    selected_crews = all_crews
    st.sidebar.info(
        "You are in the guided owner story. Switch to Explore Dashboard for filters and detailed views."
    )
else:
    page = st.sidebar.radio(
        "View",
        [
            "Executive Overview",
            "Job Profitability",
            "Crew Performance",
            "Sales & Estimates",
        ],
    )

    date_range = st.sidebar.date_input(
        "Completed date",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    selected_cities = st.sidebar.multiselect("City", all_cities, default=all_cities)
    selected_services = st.sidebar.multiselect("Service", all_services, default=all_services)
    selected_crews = st.sidebar.multiselect("Crew", all_crews, default=all_crews)

st.sidebar.divider()
st.sidebar.caption("Portfolio demo • Synthetic Middle Tennessee data")


# -----------------------------
# Apply filters
# -----------------------------
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date = end_date = pd.Timestamp(date_range)

filtered = jobs[
    (jobs["completed_date"] >= start_date)
    & (jobs["completed_date"] <= end_date)
    & (jobs["city"].isin(selected_cities))
    & (jobs["service_name"].isin(selected_services))
    & (jobs["crew_name"].isin(selected_crews))
].copy()

if filtered.empty:
    st.warning("No jobs match the current filters.")
    st.stop()


# -----------------------------
# Helpers
# -----------------------------
def money(value):
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"${value/1_000:,.0f}K"
    return f"${value:,.0f}"


def pct(value):
    return f"{float(value):.1%}"


def style_chart(fig, height=355):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=48, b=10),
        legend_title_text="",
        hovermode="x unified",
    )
    return fig


def headline():
    st.markdown('<div class="brand-kicker">Hicks Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-title">Landscaping Performance Hub</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-subtitle">'
        'Profitability, estimating, crew efficiency, and service-area performance.'
        '</div>',
        unsafe_allow_html=True,
    )


def metric_values(df):
    revenue = df["billed_revenue"].sum()
    gross_profit = df["gross_profit"].sum()
    margin = gross_profit / revenue if revenue else 0
    jobs_completed = len(df)
    avg_job = revenue / jobs_completed if jobs_completed else 0
    rev_per_hour = revenue / df["actual_labor_hours"].sum()
    return revenue, gross_profit, margin, jobs_completed, avg_job, rev_per_hour


def crew_summary(df):
    return (
        df.groupby("crew_name")
        .agg(
            Jobs=("job_id", "count"),
            Revenue=("billed_revenue", "sum"),
            Gross_Profit=("gross_profit", "sum"),
            Labor_Hours=("actual_labor_hours", "sum"),
            Labor_Variance_Hours=("labor_variance_hours", "sum"),
            Avg_Labor_Variance=("labor_variance_pct", "mean"),
            Rework_Rate=("rework_flag", "mean"),
            Rework_Jobs=("rework_flag", "sum"),
        )
        .assign(
            Gross_Margin=lambda x: x["Gross_Profit"] / x["Revenue"],
            Revenue_Per_Labor_Hour=lambda x: x["Revenue"] / x["Labor_Hours"],
        )
        .reset_index()
    )


def change_story_step(delta):
    st.session_state.story_step = min(4, max(0, st.session_state.story_step + delta))


def story_navigation(step):
    st.write("")
    left, middle, right = st.columns([1, 2.4, 1])
    with left:
        if step > 0:
            st.button(
                "← Previous",
                width="stretch",
                on_click=change_story_step,
                args=(-1,),
            )
    with middle:
        st.progress(step / 4, text=f"Guided story · Step {step + 1} of 5")
    with right:
        if step < 4:
            st.button(
                "Next →",
                type="primary",
                width="stretch",
                on_click=change_story_step,
                args=(1,),
            )


def render_guided_demo(df):
    if "story_step" not in st.session_state:
        st.session_state.story_step = 0

    # The final month is intentionally excluded because the synthetic data only
    # contains a partial month. This keeps the story's comparisons honest.
    story_df = df[df["completed_month"] < df["completed_month"].max()].copy()
    crew = crew_summary(story_df)
    focus = crew.sort_values("Avg_Labor_Variance", ascending=False).iloc[0]
    focus_jobs = story_df[story_df["crew_name"] == focus["crew_name"]].copy()
    portfolio_margin = story_df["gross_profit"].sum() / story_df["billed_revenue"].sum()
    best_margin = crew.sort_values("Gross_Margin", ascending=False).iloc[0]
    step = st.session_state.story_step

    headline()
    st.markdown(
        """
        <div class="story-hero">
            <div class="story-step">Interactive owner story</div>
            <h2>We're busy—but where is the profit going?</h2>
            <p>Step into the owner's seat, follow the warning signs, find the operational leak, and test a decision before taking action.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if step == 0:
        st.subheader("Your Monday-morning question")
        st.markdown(
            """
            The schedule is full and crews are working hard. But activity alone does not tell you
            whether the company is becoming healthier. Your goal is to find the part of the operation
            where labor hours are quietly eroding profit.
            """
        )

        revenue, gross_profit, margin, jobs_completed, _, _ = metric_values(story_df)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue reviewed", money(revenue), border=True)
        c2.metric("Gross profit", money(gross_profit), border=True)
        c3.metric("Portfolio margin", pct(margin), border=True)
        c4.metric("Completed jobs", f"{jobs_completed:,}", border=True)

        st.markdown(
            """
            <div class="story-callout">
                <strong>Your mission:</strong> identify which crew needs attention, understand why,
                and estimate the value of correcting the problem.
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif step == 1:
        st.subheader("The warning sign")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Crew needing attention", focus["crew_name"], border=True)
        c2.metric("Labor variance", pct(focus["Avg_Labor_Variance"]), border=True)
        c3.metric("Crew margin", pct(focus["Gross_Margin"]), border=True)
        c4.metric(
            "Gap vs portfolio",
            f"{(focus['Gross_Margin'] - portfolio_margin) * 100:+.1f} pts",
            border=True,
        )

        chart_data = crew.sort_values("Gross_Margin").copy()
        chart_data["Status"] = chart_data["crew_name"].apply(
            lambda name: "Investigate" if name == focus["crew_name"] else "Other crews"
        )
        fig = px.bar(
            chart_data,
            x="Gross_Margin",
            y="crew_name",
            color="Status",
            orientation="h",
            title="Gross Margin by Crew",
            color_discrete_map={"Investigate": "#f59e0b", "Other crews": "#166534"},
        )
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(style_chart(fig, 390), width="stretch")
        st.markdown(
            f"""
            <div class="story-callout">
                <strong>What the owner should notice:</strong> {focus['crew_name']} produces meaningful
                revenue, but its margin trails {best_margin['crew_name']} by
                <strong>{(best_margin['Gross_Margin'] - focus['Gross_Margin']) * 100:.1f} points</strong>.
                The next question is whether pricing, materials, or labor is responsible.
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif step == 2:
        st.subheader("Follow the evidence")
        c1, c2 = st.columns([1.25, 1])
        with c1:
            fig = px.scatter(
                crew,
                x="Avg_Labor_Variance",
                y="Gross_Margin",
                size="Revenue",
                color="Rework_Rate",
                text="crew_name",
                title="Labor Overruns vs Gross Margin",
                color_continuous_scale="YlOrRd",
            )
            fig.update_xaxes(tickformat=".0%", title="Average labor variance")
            fig.update_yaxes(tickformat=".0%", title="Gross margin")
            fig.update_traces(textposition="top center")
            st.plotly_chart(style_chart(fig, 420), width="stretch")
        with c2:
            positive_overrun = focus_jobs["labor_variance_hours"].clip(lower=0).sum()
            st.metric("Excess labor hours", f"{positive_overrun:,.0f}", border=True)
            st.metric("Rework rate", pct(focus["Rework_Rate"]), border=True)
            st.metric(
                "Revenue / labor hour",
                money(focus["Revenue_Per_Labor_Hour"]),
                border=True,
            )
            st.markdown(
                f"""
                <div class="story-callout">
                    <strong>Diagnosis:</strong> {focus['crew_name']} is the clear operational outlier.
                    Its jobs run over estimated labor by {focus['Avg_Labor_Variance']:.1%} on average,
                    and its rework rate is {focus['Rework_Rate']:.1%}. This points to estimating,
                    crew execution, or job-scoping—not a lack of demand.
                </div>
                """,
                unsafe_allow_html=True,
            )

    elif step == 3:
        st.subheader("Test a decision before making it")
        st.caption(
            f"Model the effect of coaching and tighter job scoping for {focus['crew_name']}. "
            "The estimate uses the crew's observed labor cost and positive labor overruns."
        )
        recovery_rate = st.slider(
            "Share of excess labor hours recovered",
            min_value=10,
            max_value=75,
            value=40,
            step=5,
            format="%d%%",
        )
        rework_reduction = st.slider(
            "Reduction in rework jobs",
            min_value=0,
            max_value=50,
            value=25,
            step=5,
            format="%d%%",
        )

        excess_hours = focus_jobs["labor_variance_hours"].clip(lower=0).sum()
        labor_rate = focus_jobs["labor_cost"].sum() / focus_jobs["actual_labor_hours"].sum()
        recovered_hours = excess_hours * recovery_rate / 100
        period_savings = recovered_hours * labor_rate
        months = max(1, story_df["completed_month"].nunique())
        annual_savings = period_savings / months * 12
        avoided_rework = round(focus["Rework_Jobs"] * rework_reduction / 100)
        improved_margin = (
            focus["Gross_Profit"] + period_savings
        ) / focus["Revenue"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Hours recovered", f"{recovered_hours:,.0f}", border=True)
        c2.metric("Annualized profit impact", money(annual_savings), border=True)
        c3.metric(
            "Modeled crew margin",
            pct(improved_margin),
            delta=f"{(improved_margin - focus['Gross_Margin']) * 100:.1f} pts",
            border=True,
        )
        c4.metric("Rework jobs avoided", f"{avoided_rework:,}", border=True)

        comparison = pd.DataFrame(
            {
                "Scenario": ["Current", "Modeled"],
                "Gross Margin": [focus["Gross_Margin"], improved_margin],
            }
        )
        fig = px.bar(
            comparison,
            x="Scenario",
            y="Gross Margin",
            color="Scenario",
            title="Current vs Modeled Crew Margin",
            color_discrete_map={"Current": "#94a3b8", "Modeled": "#166534"},
        )
        fig.update_yaxes(tickformat=".0%")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_chart(fig, 340), width="stretch")
        st.caption(
            "Illustrative scenario based on synthetic portfolio data. It is a decision aid, not a guaranteed forecast."
        )

    else:
        st.subheader("Turn the insight into an operating plan")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                <div class="insight-card">
                    <strong>1 · Diagnose</strong><br><br>
                    Review the highest-variance jobs by service, estimator, and crew. Confirm whether the issue begins in the estimate or in field execution.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                <div class="insight-card">
                    <strong>2 · Act</strong><br><br>
                    Tighten job scopes, coach the crew on repeat problem services, and add a weekly exception review for jobs running over plan.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                """
                <div class="insight-card">
                    <strong>3 · Measure</strong><br><br>
                    Track labor variance, rework, margin, and revenue per labor hour to verify that the change creates durable improvement.
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.success(
            "This is the Hicks Analytics approach: connect operating data, surface the decision, "
            "quantify the opportunity, and build a repeatable management rhythm."
        )
        action1, action2, _ = st.columns([1.2, 1.25, 2])
        with action1:
            st.link_button(
                "Build this for my business",
                "https://hicksanalytics.com/#contact",
                type="primary",
                width="stretch",
            )
        with action2:
            if st.button("Restart the story", width="stretch"):
                st.session_state.story_step = 0
                st.rerun()

    story_navigation(step)


# -----------------------------
# Guided Demo / Executive Overview
# -----------------------------
if page == "Guided Demo":
    render_guided_demo(filtered)

elif page == "Executive Overview":
    headline()

    revenue, gross_profit, margin, jobs_completed, avg_job, rev_per_hour = metric_values(filtered)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Revenue", money(revenue), border=True)
    m2.metric("Gross Profit", money(gross_profit), border=True)
    m3.metric("Gross Margin", pct(margin), border=True)
    m4.metric("Jobs Completed", f"{jobs_completed:,}", border=True)
    m5.metric("Avg Job Value", money(avg_job), border=True)
    m6.metric("Revenue / Labor Hr", money(rev_per_hour), border=True)

    st.write("")

    monthly = (
        filtered.groupby(pd.Grouper(key="completed_date", freq="MS"))
        .agg(
            Revenue=("billed_revenue", "sum"),
            Gross_Profit=("gross_profit", "sum"),
        )
        .reset_index()
    )

    c1, c2 = st.columns([1.35, 1])

    with c1:
        trend_long = monthly.melt(
            id_vars="completed_date",
            value_vars=["Revenue", "Gross_Profit"],
            var_name="Metric",
            value_name="Amount",
        )
        trend_long["Metric"] = trend_long["Metric"].str.replace("_", " ")
        fig = px.line(
            trend_long,
            x="completed_date",
            y="Amount",
            color="Metric",
            markers=True,
            title="Revenue & Gross Profit Trend",
        )
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_chart(fig), width="stretch")

    with c2:
        service = (
            filtered.groupby("service_name", as_index=False)["billed_revenue"]
            .sum()
            .sort_values("billed_revenue", ascending=True)
        )
        fig = px.bar(
            service,
            x="billed_revenue",
            y="service_name",
            orientation="h",
            title="Revenue by Service",
        )
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_chart(fig), width="stretch")

    c3, c4 = st.columns(2)

    with c3:
        svc_margin = (
            filtered.groupby("service_name")
            .agg(Revenue=("billed_revenue", "sum"), Gross_Profit=("gross_profit", "sum"))
            .assign(Gross_Margin=lambda x: x["Gross_Profit"] / x["Revenue"])
            .reset_index()
            .sort_values("Gross_Margin")
        )
        fig = px.bar(
            svc_margin,
            x="Gross_Margin",
            y="service_name",
            orientation="h",
            title="Gross Margin by Service",
        )
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(style_chart(fig), width="stretch")

    with c4:
        city = (
            filtered.groupby("city", as_index=False)["billed_revenue"]
            .sum()
            .sort_values("billed_revenue", ascending=True)
        )
        fig = px.bar(
            city,
            x="billed_revenue",
            y="city",
            orientation="h",
            title="Revenue by Service Area",
        )
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_chart(fig), width="stretch")

    st.subheader("Operational Insights")

    crew_perf = (
        filtered.groupby("crew_name")
        .agg(
            Revenue=("billed_revenue", "sum"),
            Labor_Hours=("actual_labor_hours", "sum"),
            Avg_Labor_Variance=("labor_variance_pct", "mean"),
            Rework_Rate=("rework_flag", "mean"),
        )
        .assign(Revenue_Per_Labor_Hour=lambda x: x["Revenue"] / x["Labor_Hours"])
        .reset_index()
    )

    worst_labor = crew_perf.sort_values("Avg_Labor_Variance", ascending=False).iloc[0]
    lowest_productivity = crew_perf.sort_values("Revenue_Per_Labor_Hour").iloc[0]
    lowest_margin = svc_margin.sort_values("Gross_Margin").iloc[0]

    i1, i2, i3 = st.columns(3)
    with i1:
        st.markdown(
            f"""
            <div class="insight-card">
                <strong>Labor variance</strong><br>
                {worst_labor['crew_name']} averages
                <b>{worst_labor['Avg_Labor_Variance']:.1%}</b> above estimated labor.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with i2:
        st.markdown(
            f"""
            <div class="insight-card">
                <strong>Crew productivity</strong><br>
                {lowest_productivity['crew_name']} has the lowest revenue per labor hour at
                <b>{money(lowest_productivity['Revenue_Per_Labor_Hour'])}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with i3:
        st.markdown(
            f"""
            <div class="insight-card">
                <strong>Service margin</strong><br>
                {lowest_margin['service_name']} has the lowest gross margin at
                <b>{lowest_margin['Gross_Margin']:.1%}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------
# Job Profitability
# -----------------------------
elif page == "Job Profitability":
    headline()
    st.subheader("Job Profitability")

    c1, c2, c3, c4 = st.columns(4)
    loss_jobs = (filtered["gross_profit"] < 0).sum()
    labor_over = (filtered["labor_variance_pct"] > 0.10).sum()

    c1.metric("Jobs", f"{len(filtered):,}", border=True)
    c2.metric("Gross Margin", pct(filtered["gross_profit"].sum() / filtered["billed_revenue"].sum()), border=True)
    c3.metric("Jobs Losing Money", f"{loss_jobs:,}", border=True)
    c4.metric("Jobs >10% Labor Over", f"{labor_over:,}", border=True)

    c5, c6 = st.columns(2)

    with c5:
        scatter = px.scatter(
            filtered,
            x="billed_revenue",
            y="gross_margin_pct",
            color="service_name",
            hover_data=["customer_name", "crew_name", "city"],
            title="Job Value vs Gross Margin",
        )
        scatter.update_xaxes(tickprefix="$", tickformat=",.0f")
        scatter.update_yaxes(tickformat=".0%")
        st.plotly_chart(style_chart(scatter, 420), width="stretch")

    with c6:
        labor = (
            filtered.groupby("crew_name", as_index=False)["labor_variance_pct"]
            .mean()
            .sort_values("labor_variance_pct")
        )
        fig = px.bar(
            labor,
            x="labor_variance_pct",
            y="crew_name",
            orientation="h",
            title="Average Labor Variance by Crew",
        )
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(style_chart(fig, 420), width="stretch")

    display_cols = [
        "completed_date",
        "customer_name",
        "service_name",
        "crew_name",
        "city",
        "billed_revenue",
        "gross_profit",
        "gross_margin_pct",
        "estimated_labor_hours",
        "actual_labor_hours",
        "labor_variance_pct",
        "rework_flag",
    ]

    detail = filtered[display_cols].sort_values("gross_profit")
    st.dataframe(
        detail,
        width="stretch",
        hide_index=True,
        column_config={
            "completed_date": st.column_config.DateColumn("Completed"),
            "customer_name": "Customer",
            "service_name": "Service",
            "crew_name": "Crew",
            "city": "City",
            "billed_revenue": st.column_config.NumberColumn("Revenue", format="$%,.0f"),
            "gross_profit": st.column_config.NumberColumn("Gross Profit", format="$%,.0f"),
            "gross_margin_pct": st.column_config.NumberColumn("Margin", format="percent"),
            "estimated_labor_hours": st.column_config.NumberColumn("Est Hrs", format="%.1f"),
            "actual_labor_hours": st.column_config.NumberColumn("Actual Hrs", format="%.1f"),
            "labor_variance_pct": st.column_config.NumberColumn("Labor Var", format="percent"),
            "rework_flag": st.column_config.CheckboxColumn("Rework"),
        },
    )


# -----------------------------
# Crew Performance
# -----------------------------
elif page == "Crew Performance":
    headline()
    st.subheader("Crew Performance")

    crew = (
        filtered.groupby("crew_name")
        .agg(
            Jobs=("job_id", "count"),
            Revenue=("billed_revenue", "sum"),
            Gross_Profit=("gross_profit", "sum"),
            Labor_Hours=("actual_labor_hours", "sum"),
            Avg_Labor_Variance=("labor_variance_pct", "mean"),
            Rework_Rate=("rework_flag", "mean"),
            Avg_Travel=("travel_minutes", "mean"),
            Avg_Rating=("customer_rating", "mean"),
        )
        .assign(
            Gross_Margin=lambda x: x["Gross_Profit"] / x["Revenue"],
            Revenue_Per_Labor_Hour=lambda x: x["Revenue"] / x["Labor_Hours"],
        )
        .reset_index()
    )

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            crew.sort_values("Revenue_Per_Labor_Hour"),
            x="Revenue_Per_Labor_Hour",
            y="crew_name",
            orientation="h",
            title="Revenue per Labor Hour",
        )
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_chart(fig), width="stretch")

    with c2:
        fig = px.bar(
            crew.sort_values("Gross_Margin"),
            x="Gross_Margin",
            y="crew_name",
            orientation="h",
            title="Gross Margin by Crew",
        )
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(style_chart(fig), width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        fig = px.scatter(
            crew,
            x="Avg_Labor_Variance",
            y="Rework_Rate",
            size="Revenue",
            text="crew_name",
            title="Labor Overruns vs Rework",
        )
        fig.update_xaxes(tickformat=".0%")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(style_chart(fig), width="stretch")

    with c4:
        fig = px.scatter(
            crew,
            x="Avg_Travel",
            y="Avg_Rating",
            size="Jobs",
            text="crew_name",
            title="Travel Burden vs Customer Rating",
        )
        st.plotly_chart(style_chart(fig), width="stretch")

    st.dataframe(
        crew.sort_values("Revenue", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "crew_name": "Crew",
            "Jobs": st.column_config.NumberColumn("Jobs", format="%d"),
            "Revenue": st.column_config.NumberColumn("Revenue", format="$%,.0f"),
            "Gross_Profit": st.column_config.NumberColumn("Gross Profit", format="$%,.0f"),
            "Gross_Margin": st.column_config.NumberColumn("Gross Margin", format="percent"),
            "Revenue_Per_Labor_Hour": st.column_config.NumberColumn("Rev/Labor Hr", format="$%.0f"),
            "Avg_Labor_Variance": st.column_config.NumberColumn("Labor Var", format="percent"),
            "Rework_Rate": st.column_config.NumberColumn("Rework", format="percent"),
            "Avg_Travel": st.column_config.NumberColumn("Avg Travel Min", format="%.1f"),
            "Avg_Rating": st.column_config.NumberColumn("Rating", format="%.2f"),
        },
    )


# -----------------------------
# Sales & Estimates
# -----------------------------
elif page == "Sales & Estimates":
    headline()
    st.subheader("Sales & Estimates")
    st.caption(
        "Estimate data is shown across the complete synthetic portfolio dataset. "
        "We will connect these metrics to the dashboard filters in the next iteration."
    )

    total_estimates = estimates["estimates_sent"].sum()
    total_won = estimates["estimates_won"].sum()
    overall_win = total_won / total_estimates
    quoted_value = estimates["quoted_value"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estimates Sent", f"{int(total_estimates):,}", border=True)
    c2.metric("Estimates Won", f"{int(total_won):,}", border=True)
    c3.metric("Win Rate", pct(overall_win), border=True)
    c4.metric("Quoted Value", money(quoted_value), border=True)

    c5, c6 = st.columns(2)

    with c5:
        win = estimates.sort_values("win_rate")
        fig = px.bar(
            win,
            x="win_rate",
            y="service_name",
            orientation="h",
            title="Estimate Win Rate by Service",
        )
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(style_chart(fig, 430), width="stretch")

    with c6:
        value = estimates.sort_values("quoted_value")
        fig = px.bar(
            value,
            x="quoted_value",
            y="service_name",
            orientation="h",
            title="Quoted Pipeline Value by Service",
        )
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_chart(fig, 430), width="stretch")

    st.dataframe(
        estimates.sort_values("quoted_value", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "service_id": None,
            "service_name": "Service",
            "estimates_sent": st.column_config.NumberColumn("Sent", format="%d"),
            "estimates_won": st.column_config.NumberColumn("Won", format="%d"),
            "win_rate": st.column_config.NumberColumn("Win Rate", format="percent"),
            "quoted_value": st.column_config.NumberColumn("Quoted Value", format="$%,.0f"),
            "avg_estimate_value": st.column_config.NumberColumn("Avg Estimate", format="$%,.0f"),
        },
    )
