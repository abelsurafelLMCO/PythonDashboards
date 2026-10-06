import streamlit as st
import pandas as pd
import altair as alt
from datetime import date
import os

EXCEL_FILE = "tasks_new.xlsx"

# 1. Load or Initialize Data
def load_data():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    else:
        # Default starter template if file doesn't exist
        df = pd.DataFrame({
            "Task_ID": ["T-101", "T-102", "T-103", "T-104"],
            "Analyst": ["Sarah Jenkins", "Alex Rivera", "David Kim", "Taylor Johnson"],
            "Task_Name": ["Financial Audit", "Data Reconciliation", "Report Generation", "Data Analysis"],
            "Status": ["In Progress", "Completed", "In Progress", "Pending"],
            "Priority": ["High", "Medium", "Low", "Medium"],
            "Due_Date": [str(date.today()), str(date.today()), str(date.today()), str(date.today())]
        })
        df.to_excel(EXCEL_FILE, index=False)
        return df

def save_data(df):
    try:
        df.to_excel(EXCEL_FILE, index=False)
        return True
    except PermissionError:
        st.error(f"⚠️ Cannot save to '{EXCEL_FILE}' because the file is open in Microsoft Excel or another program. Please close Excel and try saving again.")
        return False
    except Exception as e:
        st.error(f"⚠️ Error saving data: {e}")
        return False

st.set_page_config(page_title="Analyst Task Tracker", layout="wide")
st.title("📋 Analyst Task & Assignment Dashboard")

df = load_data()

# 2. Key Metrics & Analyst Availability
st.subheader("📊 Analyst Workload & Availability")

total_tasks = len(df)
completed_tasks = len(df[df["Status"] == "Completed"])
active_df = df[df["Status"].isin(["Pending", "In Progress"])]
active_tasks = len(active_df)

all_analysts = sorted(df["Analyst"].dropna().unique().tolist())
analyst_active_counts = active_df.groupby("Analyst").size().to_dict()

# Availability classification
available_analysts = [a for a in all_analysts if analyst_active_counts.get(a, 0) == 0]
active_analysts = [a for a in all_analysts if 0 < analyst_active_counts.get(a, 0) <= 2]
busy_analysts = [a for a in all_analysts if analyst_active_counts.get(a, 0) > 2]

# Summary metric cards
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Tasks", total_tasks)
m2.metric("Active Tasks", active_tasks)
m3.metric("Available Analysts", f"{len(available_analysts)} / {len(all_analysts)}")
m4.metric("Completed Tasks", completed_tasks)

# Visual layout: 2 columns
vcol1, vcol2 = st.columns([1, 1])

with vcol1:
    st.markdown("#### 🟢 Availability Roster")
    if available_analysts:
        available_list = "\n".join([f"- 🟢 **{a}** (Ready for work)" for a in available_analysts])
        st.success(f"**Available Analysts (0 active tasks):**\n\n{available_list}")
    else:
        st.info("🟡 All analysts currently have at least one active task.")

    if active_analysts:
        with st.expander(f"🟡 Active Analysts ({len(active_analysts)}) - Moderate Load", expanded=True):
            for a in active_analysts:
                count = analyst_active_counts[a]
                st.write(f"• **{a}**: {count} active task{'s' if count > 1 else ''}")

    if busy_analysts:
        with st.expander(f"🔴 Busy Analysts ({len(busy_analysts)}) - High Load", expanded=False):
            for a in busy_analysts:
                count = analyst_active_counts[a]
                st.write(f"• **{a}**: {count} active tasks")

with vcol2:
    st.markdown("#### 📈 Active Tasks per Analyst")
    chart_rows = []
    for a in all_analysts:
        c = analyst_active_counts.get(a, 0)
        status_category = "🟢 Available (0)" if c == 0 else ("🟡 Active (1-2)" if c <= 2 else "🔴 High Load (3+)")
        chart_rows.append({"Analyst": a, "Active Tasks": c, "Status": status_category})

    chart_df = pd.DataFrame(chart_rows)

    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
        .encode(
            y=alt.Y("Analyst:N", sort="-x", title="Analyst"),
            x=alt.X("Active Tasks:Q", title="Active Tasks (Pending & In Progress)", axis=alt.Axis(tickMinStep=1)),
            color=alt.Color(
                "Status:N",
                scale=alt.Scale(
                    domain=["🟢 Available (0)", "🟡 Active (1-2)", "🔴 High Load (3+)"],
                    range=["#2ecc71", "#f39c12", "#e74c3c"]
                ),
                legend=alt.Legend(title="Availability")
            ),
            tooltip=["Analyst", "Active Tasks", "Status"]
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)

st.divider()

# 3. Interactive Task Table (Update Status / Mark Done)
st.subheader("📝 Update Task Status")
st.caption("Change status in the table below and click 'Save Changes' to update Excel.")

status_options = ["Pending", "In Progress", "Completed", "On Hold"]
priority_options = ["Low", "Medium", "High", "Critical"]

edited_df = st.data_editor(
    df,
    column_config={
        "Status": st.column_config.SelectboxColumn("Status", options=status_options, required=True),
        "Priority": st.column_config.SelectboxColumn("Priority", options=priority_options),
        "Task_ID": st.column_config.TextColumn("Task ID", disabled=True),
    },
    use_container_width=True,
    num_rows="dynamic"
)

if st.button("💾 Save Table Changes"):
    if save_data(edited_df):
        st.success("Excel sheet updated successfully!")
        st.rerun()

st.divider()

# 4. Form to Assign a New Task
st.subheader("➕ Assign a New Task")
with st.form("assign_task_form"):
    col_a, col_b = st.columns(2)
    with col_a:
        # Preselect available analysts first in list
        sorted_analysts = available_analysts + [a for a in all_analysts if a not in available_analysts]
        analyst_choice = st.selectbox(
            "Assign To",
            options=sorted_analysts,
            format_func=lambda x: f"🟢 {x} (Available)" if x in available_analysts else f"🟡 {x} ({analyst_active_counts.get(x, 0)} active)"
        )
        task_name = st.text_input("Task Description / Name")
    with col_b:
        priority = st.selectbox("Priority", options=priority_options, index=1)
        due_date = st.date_input("Due Date", min_value=date.today())

    submitted = st.form_submit_button("Assign Task")
    if submitted:
        if not task_name.strip():
            st.error("Please provide a task name.")
        else:
            new_id = f"T-{100 + len(df) + 1}"
            new_row = pd.DataFrame([{
                "Task_ID": new_id,
                "Analyst": analyst_choice,
                "Task_Name": task_name.strip(),
                "Status": "Pending",
                "Priority": priority,
                "Due_Date": str(due_date)
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            if save_data(updated_df):
                st.success(f"Assigned task {new_id} to {analyst_choice}!")
                st.rerun()