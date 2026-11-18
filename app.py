import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import date
from io import BytesIO

st.set_page_config(page_title="IPMAT PALUGA", page_icon="📊", layout="wide")

st.markdown("""
<style>
.main {background-color:#f7f8fc;}
[data-testid="stMetric"] {background:white;padding:16px;border-radius:12px;border:1px solid #e8eaf2;}
.block-container {padding-top:1.5rem;}
</style>
""", unsafe_allow_html=True)

st.title("📊 IPMAT PALUGA")
st.caption("Mock Test Performance & Learning Analytics")

def get_client():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
        return create_client(url, key)
    except Exception:
        return None

if "client" not in st.session_state:
    st.session_state.client = get_client()
if "user" not in st.session_state:
    st.session_state.user = None
if "mock_cache" not in st.session_state:
    st.session_state.mock_cache = []

client = st.session_state.client

def auth_screen():
    st.subheader("Welcome")
    st.info("Create an account or sign in to access your private mock-test records.")
    if client is None:
        st.error("Database is not configured yet. Follow SETUP.md to connect Supabase before using student accounts.")
        st.stop()
    mode = st.radio("Choose", ["Sign in", "Create account"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button(mode, type="primary", use_container_width=True):
        try:
            if mode == "Create account":
                result = client.auth.sign_up({"email": email, "password": password})
                if result.user:
                    st.success("Account created. If email confirmation is enabled, verify your email, then sign in.")
            else:
                result = client.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = result.user
                st.rerun()
        except Exception as e:
            st.error(f"Could not complete authentication: {e}")

if client is None or st.session_state.user is None:
    auth_screen()
    st.stop()

user_id = st.session_state.user.id

with st.sidebar:
    st.success(f"Signed in: {st.session_state.user.email}")
    page = st.radio("Navigation", ["Dashboard", "Add Mock Test", "Question-level Analysis", "Mock History", "CSV Upload", "Help"])
    if st.button("Sign out"):
        try:
            client.auth.sign_out()
        finally:
            st.session_state.user = None
            st.rerun()

def fetch_mocks():
    try:
        return client.table("mock_tests").select("*").eq("user_id", user_id).order("test_date", desc=True).execute().data or []
    except Exception as e:
        st.error(f"Unable to load mock tests: {e}")
        return []

def fetch_questions():
    try:
        return client.table("question_results").select("*").eq("user_id", user_id).execute().data or []
    except Exception as e:
        st.error(f"Unable to load question records: {e}")
        return []

mocks = fetch_mocks()
questions = fetch_questions()
mock_df = pd.DataFrame(mocks)
q_df = pd.DataFrame(questions)

def num(row, key, default=0):
    try: return float(row.get(key, default) or default)
    except: return default

if page == "Dashboard":
    st.header("Your performance dashboard")
    if mock_df.empty:
        st.info("You haven't added a mock test yet. Open **Add Mock Test** to enter your first result.")
    else:
        mock_df["total_score"] = pd.to_numeric(mock_df["total_score"], errors="coerce").fillna(0)
        mock_df["test_date"] = pd.to_datetime(mock_df["test_date"], errors="coerce")
        latest = mock_df.sort_values("test_date").iloc[-1]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Mocks completed", len(mock_df))
        c2.metric("Latest score", f'{latest["total_score"]:.1f}')
        c3.metric("Best score", f'{mock_df["total_score"].max():.1f}')
        c4.metric("Average score", f'{mock_df["total_score"].mean():.1f}')
        st.subheader("Score trend")
        trend = mock_df.sort_values("test_date")
        st.plotly_chart(px.line(trend, x="test_date", y="total_score", markers=True, title="Total score across mocks"), use_container_width=True)
        st.subheader("Latest section scores")
        cols = st.columns(3)
        for col, section in zip(cols, ["QA", "VA", "LR"]):
            score = num(latest, f"{section.lower()}_score")
            maximum = num(latest, f"{section.lower()}_max")
            col.metric(section, f"{score:g} / {maximum:g}" if maximum else f"{score:g}")
        if not q_df.empty:
            st.subheader("Topic accuracy (question records)")
            q_df["is_correct"] = q_df["is_correct"].astype(bool)
            topic = q_df.groupby("topic", dropna=False)["is_correct"].mean().mul(100).reset_index(name="accuracy")
            topic["topic"] = topic["topic"].fillna("Unspecified")
            st.plotly_chart(px.bar(topic, x="topic", y="accuracy", range_y=[0,100], title="Accuracy by topic"), use_container_width=True)
    st.caption("Scores and estimates are based only on the data you enter. They are not admission predictions.")

elif page == "Add Mock Test":
    st.header("Add a mock test")
    with st.form("mock_form"):
        exam = st.selectbox("Examination", ["IPMAT Indore", "IPMAT Rohtak", "JIPMAT", "Other"])
        test_name = st.text_input("Mock name", placeholder="e.g. Mock Test 01")
        test_date = st.date_input("Test date", value=date.today())
        st.subheader("Section scores")
        a,b,c = st.columns(3)
        qa = a.number_input("QA score", min_value=0.0, value=0.0)
        qa_max = a.number_input("QA maximum marks", min_value=0.0, value=60.0)
        va = b.number_input("VA score", min_value=0.0, value=0.0)
        va_max = b.number_input("VA maximum marks", min_value=0.0, value=60.0)
        lr = c.number_input("LR score (if applicable)", min_value=0.0, value=0.0)
        lr_max = c.number_input("LR maximum marks", min_value=0.0, value=0.0)
        total_override = st.number_input("Total score (optional; enter 0 to calculate from sections)", min_value=0.0, value=0.0)
        attempted = st.number_input("Total attempted questions", min_value=0, value=0, step=1)
        correct = st.number_input("Total correct answers", min_value=0, value=0, step=1)
        submitted = st.form_submit_button("Save mock test", type="primary")
    if submitted:
        if not test_name.strip():
            st.error("Please enter a mock name.")
        elif qa > qa_max or va > va_max or lr > lr_max or correct > attempted:
            st.error("Please check scores, maximum marks and correct/attempted counts.")
        else:
            total = total_override if total_override > 0 else qa + va + lr
            payload = {"user_id": user_id, "exam": exam, "test_name": test_name.strip(),
                       "test_date": str(test_date), "qa_score": qa, "qa_max": qa_max,
                       "va_score": va, "va_max": va_max, "lr_score": lr, "lr_max": lr_max,
                       "total_score": total, "attempted": attempted, "correct": correct}
            try:
                client.table("mock_tests").insert(payload).execute()
                st.success("Mock test saved successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not save this mock: {e}")

elif page == "Question-level Analysis":
    st.header("Add question-level records")
    st.write("Record one row per question to analyse topic accuracy and time. You can also upload a CSV from the CSV Upload page.")
    with st.form("question_form"):
        exam = st.selectbox("Examination", ["IPMAT Indore", "IPMAT Rohtak", "JIPMAT"], key="qexam")
        mock_name = st.text_input("Mock name", key="qmock")
        question_no = st.text_input("Question number", "1")
        section = st.selectbox("Section", ["QA", "VA", "LR"])
        topic = st.text_input("Topic", placeholder="e.g. Percentages")
        status = st.selectbox("Result", ["Correct", "Incorrect", "Unattempted"])
        time_seconds = st.number_input("Time taken (seconds)", min_value=0, value=60)
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Difficult", "Unknown"])
        add = st.form_submit_button("Save question")
    if add:
        if not mock_name.strip() or not topic.strip():
            st.error("Please enter the mock name and topic.")
        else:
            try:
                client.table("question_results").insert({
                    "user_id": user_id, "exam": exam, "mock_name": mock_name.strip(),
                    "question_no": str(question_no), "section": section, "topic": topic.strip(),
                    "result": status, "is_correct": status == "Correct",
                    "time_seconds": int(time_seconds), "difficulty": difficulty
                }).execute()
                st.success("Question record saved.")
                st.rerun()
            except Exception as e: st.error(f"Could not save question: {e}")
    if not q_df.empty:
        st.subheader("Your recorded questions")
        st.dataframe(q_df.drop(columns=["user_id"], errors="ignore"), use_container_width=True)

elif page == "Mock History":
    st.header("Mock test history")
    if mock_df.empty:
        st.info("No mock tests yet.")
    else:
        show = mock_df.drop(columns=["user_id"], errors="ignore").sort_values("test_date", ascending=False)
        st.dataframe(show, use_container_width=True)
        st.download_button("Download my mock history (CSV)", show.to_csv(index=False), "my_mock_history.csv", "text/csv")

elif page == "CSV Upload":
    st.header("Upload question-level CSV")
    st.write("Upload a CSV with these columns: exam, mock_name, question_no, section, topic, result, time_seconds, difficulty.")
    template = pd.DataFrame([{"exam":"IPMAT Indore","mock_name":"Mock 01","question_no":"1","section":"QA","topic":"Percentages","result":"Correct","time_seconds":75,"difficulty":"Easy"}])
    st.download_button("Download CSV template", template.to_csv(index=False), "ipmat_question_template.csv", "text/csv")
    file = st.file_uploader("Choose CSV file", type=["csv"])
    if file:
        try:
            data = pd.read_csv(file)
            required = ["exam","mock_name","question_no","section","topic","result","time_seconds","difficulty"]
            missing = [x for x in required if x not in data.columns]
            if missing:
                st.error("Missing columns: " + ", ".join(missing))
            else:
                st.dataframe(data.head(10), use_container_width=True)
                if st.button("Import these records", type="primary"):
                    rows=[]
                    for _,r in data.iterrows():
                        result=str(r["result"]).strip().title()
                        if result not in ["Correct","Incorrect","Unattempted"]: continue
                        rows.append({"user_id":user_id,"exam":str(r["exam"]),"mock_name":str(r["mock_name"]),
                            "question_no":str(r["question_no"]),"section":str(r["section"]).upper(),
                            "topic":str(r["topic"]),"result":result,"is_correct":result=="Correct",
                            "time_seconds":int(r["time_seconds"]),"difficulty":str(r["difficulty"])})
                    if rows:
                        client.table("question_results").insert(rows).execute()
                        st.success(f"Imported {len(rows)} question records.")
                        st.rerun()
                    else: st.warning("No valid rows found.")
        except Exception as e: st.error(f"Could not read CSV: {e}")

elif page == "Help":
    st.header("How to use IPMAT PALUGA")
    st.markdown("""
    1. Add each mock under **Add Mock Test**.
    2. Enter question-level details under **Question-level Analysis**, or import them using **CSV Upload**.
    3. Visit **Dashboard** to view score trends and topic accuracy.
    4. Download your mock history from **Mock History**.

    **Important:** Section structures, marking schemes and maximum marks differ across exam providers and mock series. Enter the maximum marks shown by your own mock provider. The app does not assume one universal marking scheme.
    """)
    st.warning("This is an early version. Do not upload sensitive identity documents or share your password. Use a unique password.")
