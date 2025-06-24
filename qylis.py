import streamlit as st
import requests
import plotly.graph_objects as go

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Resume Screener", page_icon=":mag:", layout="wide")
st.title("📝 Resume Screener")

# --- Upload Job Description ---
st.header("Step 1: Upload Job Description")
jd_file = st.file_uploader(
    "Upload Job Description (PDF, DOCX, or TXT)", 
    type=["pdf", "docx", "txt"]
)

jd_uploaded = False
if jd_file:
    with st.spinner("Uploading job description..."):
        files = {"file": (jd_file.name, jd_file, jd_file.type)}
        try:
            response = requests.post(f"{API_URL}/upload-jd", files=files)
            if response.status_code == 200:
                st.success("✅ Job description uploaded successfully.")
                jd_uploaded = True
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")

# --- Upload Resumes ---
st.header("Step 2: Upload Resumes")
resume_files = st.file_uploader(
    "Upload one or more resumes (PDF, DOCX, or TXT)", 
    type=["pdf", "docx", "txt"], 
    accept_multiple_files=True
)

if st.button("Screen Resumes") and resume_files and (jd_uploaded or jd_file):
    with st.spinner("Screening resumes..."):
        files = [("files", (f.name, f, f.type)) for f in resume_files]
        try:
            response = requests.post(f"{API_URL}/upload-resumes", files=files)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    st.markdown("### <span style='color:green'>Screening Results (Ranked)</span>", unsafe_allow_html=True)
                    # Prepare data for table and bar chart
                    table_data = []
                    bar_labels = []
                    bar_values = []
                    bar_colors = []
                    for idx, r in enumerate(results, 1):
                        match_pct = r.get("match_percentage", 0)
                        table_data.append([
                            idx,
                            r.get("resume_filename", ""),
                            r.get("email", ""),
                            r.get("location", ""),
                            match_pct,
                            ", ".join(r.get("matched_skills", [])),
                            ", ".join(r.get("missing_skills", [])),
                            ", ".join(r.get("additional_skills", [])),
                        ])
                        bar_labels.append(r.get("resume_filename", ""))
                        bar_values.append(match_pct)
                        # Color logic
                        if match_pct >= 80:
                            bar_colors.append("green")
                        elif match_pct >= 50:
                            bar_colors.append("orange")
                        else:
                            bar_colors.append("red")

                    # Display table with colored text for match %
                    st.write("#### Resume Table")
                    for row in table_data:
                        color = "green" if row[4] >= 80 else "orange" if row[4] >= 50 else "red"
                        st.markdown(
                            f"<div style='background-color:#f9f9f9;padding:8px;border-radius:6px;margin-bottom:4px;'>"
                            f"<b>Rank:</b> {row[0]} | <b>Resume:</b> {row[1]} | <b>Email:</b> {row[2]} | <b>Location:</b> {row[3]} | "
                            f"<b>Match %:</b> <span style='color:{color}'>{row[4]}</span><br>"
                            f"<b>Matched Skills:</b> {row[5]}<br>"
                            f"<b>Missing Skills:</b> {row[6]}<br>"
                            f"<b>Additional Skills:</b> {row[7]}"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                    # --- Colored Bar Diagram ---
                    st.write("#### Match Percentage Bar Diagram")
                    fig = go.Figure(
                        go.Bar(
                            x=bar_labels,
                            y=bar_values,
                            marker_color=bar_colors
                        )
                    )
                    fig.update_layout(
                        xaxis_title="Resume",
                        yaxis_title="Match %",
                        yaxis=dict(range=[0, 100]),
                        plot_bgcolor="#f9f9f9"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ No valid results returned. Check 'all_results' for errors.")
                    st.json(data.get("all_results", {}))
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")

# Footer
st.markdown(
    "<hr><center><span style='color:gray'>Powered by Streamlit & OpenAI | "
    "Status: <span style='color:green'>Ready</span></span></center>",
    unsafe_allow_html=True
)