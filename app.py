import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import streamlit as st
import streamlit_authenticator as stauth


REQUIRED_SECRET_KEYS = ["google_sheet_url", "google_form_url", "cookie_key"]
LOCAL_EXPENSES_PATTERN = "expenses_*.csv"


st.set_page_config(
    page_title="আমার স্মার্ট মানি ম্যানেজার",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;500;600;700&display=swap');

        /* ── Base font ── */
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: "Noto Sans Bengali", "Hind Siliguri", "SolaimanLipi", sans-serif;
        }

        /* ── HIDE ALL STREAMLIT/GITHUB BRANDING & FOOTER ── */
        #MainMenu,
        footer,
        header,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="manage-app-button"],
        [data-testid="stAppDeployButton"],
        .stDeployButton,
        [class*="viewerBadge"],
        [class*="styles_viewerBadge"],
        [class*="githubButton"],
        [data-testid="baseButton-headerNoPadding"],
        iframe[title="streamlit_authenticator"],
        a[href*="streamlit.io"],
        a[href*="share.streamlit.io"],
        div[class*="StatusWidget"],
        div[class*="ReportStatus"],
        section[data-testid="stSidebarNavItems"] + div {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
        }

        /* ── Light mode ── */
        @media (prefers-color-scheme: light) {
            .stApp { background: #f7f8fb; }
            [data-testid="stMetric"] { background: #ffffff; border: 1px solid #e6e9f0; }
        }

        /* ── Dark mode ── */
        @media (prefers-color-scheme: dark) {
            .stApp { background: #0f1117 !important; }

            [data-testid="stMetric"] {
                background: #1e2130 !important;
                border: 1px solid #2e3250 !important;
                color: #e8eaf6 !important;
            }

            [data-testid="stMetricLabel"] p,
            [data-testid="stMetricValue"],
            [data-testid="stMetricDelta"] {
                color: #e8eaf6 !important;
            }

            h1, h2, h3, h4, p, label, span, div {
                color: #e8eaf6;
            }

            [data-testid="stDataFrame"] { filter: none; }

            .stProgress > div > div {
                background-color: #3d5afe !important;
            }

            .stProgress {
                background-color: #2e3250 !important;
            }

            [data-testid="stExpander"] {
                background: #1e2130 !important;
                border: 1px solid #2e3250 !important;
            }

            .stButton > button,
            .stFormSubmitButton > button {
                background: #3d5afe !important;
                color: #ffffff !important;
                border: none !important;
            }

            .stButton > button:hover,
            .stFormSubmitButton > button:hover {
                background: #536dfe !important;
            }

            [data-testid="stTextInput"] input,
            [data-testid="stNumberInput"] input {
                background: #1e2130 !important;
                color: #e8eaf6 !important;
                border: 1px solid #3d4265 !important;
            }

            [data-testid="stForm"] {
                background: #1e2130 !important;
                border: 1px solid #2e3250 !important;
                border-radius: 10px !important;
                padding: 1rem !important;
            }

            section[data-testid="stSidebar"] {
                background: #1a1d2e !important;
                border-right: 1px solid #2e3250 !important;
            }

            .stAlert {
                background: #1e2130 !important;
                border: 1px solid #3d4265 !important;
            }

            .stInfo { border-left: 4px solid #3d5afe !important; }
            .stWarning { border-left: 4px solid #ffa000 !important; }
            .stSuccess { border-left: 4px solid #00c853 !important; }
            .stError { border-left: 4px solid #f44336 !important; }

            [data-testid="stMultiSelect"] > div,
            [data-testid="stSelectbox"] > div {
                background: #1e2130 !important;
                color: #e8eaf6 !important;
                border: 1px solid #3d4265 !important;
            }

            [data-baseweb="tag"] {
                background: #3d5afe !important;
                color: #ffffff !important;
            }
        }

        /* ── Streamlit also sets data-theme attribute ── */
        [data-theme="dark"] .stApp { background: #0f1117 !important; }

        [data-theme="dark"] [data-testid="stMetric"] {
            background: #1e2130 !important;
            border: 1px solid #2e3250 !important;
        }

        [data-theme="dark"] .stButton > button,
        [data-theme="dark"] .stFormSubmitButton > button {
            background: #3d5afe !important;
            color: #fff !important;
            border: none !important;
        }

        [data-theme="dark"] [data-testid="stForm"] {
            background: #1e2130 !important;
            border: 1px solid #2e3250 !important;
            border-radius: 10px !important;
            padding: 1rem !important;
        }

        [data-theme="dark"] section[data-testid="stSidebar"] {
            background: #1a1d2e !important;
        }

        /* ── Shared metric style ── */
        [data-testid="stMetric"] {
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }

        [data-testid="stMetricLabel"] p,
        [data-testid="stMetricValue"] {
            font-family: "Noto Sans Bengali", "Hind Siliguri", "SolaimanLipi", sans-serif;
        }

        /* ── Buttons ── */
        .stButton > button,
        .stFormSubmitButton > button {
            width: 100%;
            min-height: 2.8rem;
            border-radius: 8px;
            font-weight: 700;
            font-family: "Noto Sans Bengali", "Hind Siliguri", "SolaimanLipi", sans-serif;
            transition: background 0.2s ease, transform 0.1s ease;
        }

        .stButton > button:active,
        .stFormSubmitButton > button:active {
            transform: scale(0.98);
        }

        /* ── DataFrame ── */
        div[data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
        }

        /* ── Sidebar font ── */
        section[data-testid="stSidebar"] {
            font-family: "Noto Sans Bengali", "Hind Siliguri", "SolaimanLipi", sans-serif;
        }

        /* ── Layout ── */
        .block-container {
            max-width: 1120px;
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 { letter-spacing: 0; }

        /* ── Mobile ── */
        @media (max-width: 720px) {
            .block-container {
                padding: 0.9rem 0.85rem 3rem; /* extra bottom padding so content clears any residual bar */
            }

            h1 {
                font-size: 1.75rem;
                line-height: 1.25;
            }

            h2, h3 { font-size: 1.2rem; }

            [data-testid="stMetric"] { padding: 0.85rem; }

            /* bigger tap targets on mobile */
            .stButton > button,
            .stFormSubmitButton > button {
                min-height: 3.2rem;
                font-size: 1rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

def load_config() -> dict:
    missing_keys = []
    config = {}

    for key in REQUIRED_SECRET_KEYS:
        try:
            config[key] = st.secrets[key]
        except Exception:
            missing_keys.append(key)

    try:
        config["users"] = list(st.secrets["users"])
    except Exception:
        missing_keys.append("users")

    try:
        config["total_budget"] = int(st.secrets.get("total_budget", 10000))
    except Exception:
        config["total_budget"] = 10000

    if missing_keys:
        st.error(
            "অ্যাপ চালাতে Streamlit secrets সেট করা দরকার: "
            + ", ".join(sorted(set(missing_keys)))
        )
        st.stop()

    return config


CONFIG = load_config()
GOOGLE_SHEET_URL = CONFIG["google_sheet_url"]
GOOGLE_FORM_URL = CONFIG["google_form_url"]
TOTAL_BUDGET = CONFIG["total_budget"]
USERS = CONFIG["users"]


def build_credentials() -> dict:
    credentials = {"usernames": {}}
    for user in USERS:
        credentials["usernames"][user["username"]] = {
            "name": user["name"],
            "password": stauth.Hasher.hash(user["password"]),
        }
    return credentials


def get_csv_url() -> str:
    csv_url = GOOGLE_SHEET_URL.replace(
        "/edit?usp=sharing", "/export?format=csv"
    ).replace("/edit#gid=", "/export?format=csv&gid=")
    return f"{csv_url}&timestamp={int(time.time())}"


def normalize_expenses(data: pd.DataFrame, fallback_username: str = "") -> pd.DataFrame:
    rename_map = {
        "User": "username",
        "Username": "username",
        "Timestamp": "Date",
        "timestamp": "Date",
        "Date": "Date",
        "date": "Date",
        "তারিখ": "Date",
        "খাত": "Khath",
        "Category": "Khath",
        "Amount": "Amount",
        "amount": "Amount",
        "টাকা": "Amount",
    }
    data = data.rename(columns=rename_map)

    for column in ["username", "Date", "Khath", "Amount"]:
        if column not in data.columns:
            data[column] = fallback_username if column == "username" else np.nan

    data = data[["username", "Date", "Khath", "Amount"]].copy()
    data["username"] = data["username"].fillna(fallback_username).astype(str).str.strip()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Khath"] = data["Khath"].fillna("অন্যান্য").astype(str).str.strip()
    data["Amount"] = pd.to_numeric(data["Amount"], errors="coerce").fillna(0).astype(int)
    return data[data["Amount"] > 0]


def load_local_expenses() -> pd.DataFrame:
    expenses = []

    for path in Path(".").glob(LOCAL_EXPENSES_PATTERN):
        fallback_username = path.stem.replace("expenses_", "", 1)
        try:
            expenses.append(normalize_expenses(pd.read_csv(path), fallback_username))
        except Exception:
            continue

    if not expenses:
        return pd.DataFrame(columns=["username", "Date", "Khath", "Amount"])
    return pd.concat(expenses, ignore_index=True)


def load_expenses() -> pd.DataFrame:
    try:
        data = normalize_expenses(pd.read_csv(get_csv_url()))
    except Exception:
        data = pd.DataFrame(columns=["username", "Date", "Khath", "Amount"])

    local_data = load_local_expenses()
    if data.empty:
        return local_data
    if local_data.empty:
        return data
    return pd.concat([data, local_data], ignore_index=True)


def save_local_expense(username: str, category: str, amount: int) -> None:
    path = Path(f"expenses_{username}.csv")
    new_row = pd.DataFrame(
        [
            {
                "username": username,
                "Date": pd.Timestamp.now(),
                "Khath": category,
                "Amount": int(amount),
            }
        ]
    )

    if path.exists():
        existing = normalize_expenses(pd.read_csv(path), username)
        data = pd.concat([existing, new_row], ignore_index=True)
    else:
        data = new_row

    data.to_csv(path, index=False, encoding="utf-8")


def save_expense(username: str, category: str, amount: int) -> tuple[bool, str]:
    form_data = {
        "entry.410603098": username,
        "entry.946762292": category,
        "entry.2055736241": amount,
    }

    try:
        response = requests.post(GOOGLE_FORM_URL, data=form_data, timeout=15)
    except requests.RequestException as exc:
        save_local_expense(username, category, amount)
        return (
            True,
            "Google-এ পাঠানো যায়নি, তাই খরচটি লোকাল CSV ফাইলে সেভ হয়েছে। "
            f"কারণ: {exc}",
        )

    if response.status_code in (200, 302):
        return True, "খরচটি সফলভাবে সেভ হয়েছে।"
    save_local_expense(username, category, amount)
    return (
        True,
        "Google Form সাড়া দেয়নি, তাই খরচটি লোকাল CSV ফাইলে সেভ হয়েছে। "
        "Entry ID এবং ফর্ম লিংক পরে চেক করুন।",
    )


def format_taka(amount: int | float) -> str:
    return f"{int(amount):,} টাকা"


def filter_expenses(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    st.subheader("ফিল্টার")

    category_options = sorted(df["Khath"].dropna().unique().tolist())
    amount_min = int(df["Amount"].min())
    amount_max = int(df["Amount"].max())
    dated_df = df.dropna(subset=["Date"])

    filter_col_1, filter_col_2, filter_col_3 = st.columns(3)

    with filter_col_1:
        selected_categories = st.multiselect(
            "খাত নির্বাচন করুন",
            options=category_options,
            default=category_options,
        )

    with filter_col_2:
        if amount_min == amount_max:
            amount_range = (amount_min, amount_max)
            st.number_input(
                "টাকার পরিমাণ",
                value=amount_min,
                disabled=True,
            )
        else:
            amount_range = st.slider(
                "টাকার পরিমাণ",
                min_value=amount_min,
                max_value=amount_max,
                value=(amount_min, amount_max),
            )

    with filter_col_3:
        if dated_df.empty:
            date_range = None
            include_missing_date = True
            st.text_input("তারিখ", value="তারিখ পাওয়া যায়নি", disabled=True)
        else:
            start_date = dated_df["Date"].min().date()
            end_date = dated_df["Date"].max().date()
            date_range = st.date_input(
                "তারিখ",
                value=(start_date, end_date),
                min_value=start_date,
                max_value=end_date,
            )
            include_missing_date = st.checkbox(
                "তারিখ নেই এমন রেকর্ড দেখান",
                value=True,
            )

    filtered_df = df[
        df["Khath"].isin(selected_categories)
        & df["Amount"].between(amount_range[0], amount_range[1])
    ].copy()

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
        missing_date_filter = (
            filtered_df["Date"].isna()
            if include_missing_date
            else pd.Series(False, index=filtered_df.index)
        )
        filtered_df = filtered_df[
            missing_date_filter
            | (
                (filtered_df["Date"].dt.date >= start_date)
                & (filtered_df["Date"].dt.date <= end_date)
            )
        ]

    st.caption(f"মোট {len(df)}টি রেকর্ডের মধ্যে {len(filtered_df)}টি দেখানো হচ্ছে")
    return filtered_df


def show_forecast(df: pd.DataFrame, category_df: pd.DataFrame, remaining_budget: int) -> None:
    spent_amounts = df["Amount"].tolist()

    if len(spent_amounts) > 1:
        days = np.arange(len(spent_amounts))
        slope, intercept = np.polyfit(days, spent_amounts, 1)
        predicted_next = max(100, int(slope * len(spent_amounts) + intercept))
    else:
        predicted_next = spent_amounts[0]

    highest_expense_row = category_df.loc[category_df["Amount"].idxmax()]
    highest_category = highest_expense_row["Khath"]
    highest_amount = int(highest_expense_row["Amount"])

    st.info("আপনার খরচের লোকাল অ্যানালাইসিস রিপোর্ট")
    st.markdown(
        f"""
        **১. খরচের অভ্যাস:** এখন পর্যন্ত সবচেয়ে বেশি খরচ হয়েছে **{highest_category}** খাতে,
        মোট **{format_taka(highest_amount)}**।

        **২. পরবর্তী সম্ভাব্য খরচ:** বর্তমান প্যাটার্ন অনুযায়ী পরবর্তী খরচ হতে পারে প্রায়
        **{format_taka(predicted_next)}**।

        **৩. টাকা বাঁচানোর পরামর্শ:** **{highest_category}** খাতে খরচ একটু কমালে বাজেট ধরে রাখা সহজ হবে।
        """
    )

    if remaining_budget < TOTAL_BUDGET * 0.3:
        st.warning("আপনার বাজেট শেষের দিকে। জরুরি নয় এমন খরচ আপাতত কমিয়ে দিন।")


authenticator = stauth.Authenticate(
    build_credentials(),
    "money_manager_cookie",
    CONFIG["cookie_key"],
    cookie_expiry_days=30,
)

authenticator.login(key="login_form")

authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")
name = st.session_state.get("name")

if authentication_status is False:
    st.error("ইউজারনেম বা পাসওয়ার্ড ভুল হয়েছে। আবার চেষ্টা করুন।")
elif authentication_status is None:
    st.warning("আপনার ইউজারনেম ও পাসওয়ার্ড দিয়ে লগইন করুন।")
elif authentication_status:
    authenticator.logout("লগআউট", "sidebar")
    st.sidebar.title(f"স্বাগতম, {name}!")
    st.sidebar.caption("আপনার ব্যক্তিগত খরচের হিসাব")

    all_data = load_expenses()
    user_df = all_data[all_data["username"] == username].copy()

    st.title("💰 আমার স্মার্ট মানি ম্যানেজার")
    st.caption(f"লগইন করা ইউজার: {name}")

    df = filter_expenses(user_df)

    total_spent = int(df["Amount"].sum()) if not df.empty else 0
    remaining_budget = TOTAL_BUDGET - total_spent
    used_percent = min(100, round((total_spent / TOTAL_BUDGET) * 100))

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("মোট বাজেট", format_taka(TOTAL_BUDGET))
    metric_2.metric("মোট খরচ", format_taka(total_spent), delta=f"-{format_taka(total_spent)}" if total_spent else None)
    metric_3.metric("বাকি বাজেট", format_taka(remaining_budget))

    st.progress(used_percent / 100, text=f"বাজেটের {used_percent}% ব্যবহার হয়েছে")

    st.subheader("নতুন খরচ যোগ করুন")
    with st.form(key="expense_form", clear_on_submit=True):
        category = st.text_input(
            "কোথায় খরচ করেছেন?",
            placeholder="যেমন: খাবার, রিকশা, বাজার",
        )
        amount = st.number_input("কত টাকা খরচ হয়েছে?", min_value=1, step=1)
        submit_button = st.form_submit_button("সেভ করুন")

    if submit_button:
        category = category.strip()
        if not category:
            st.error("খরচের খাত লিখুন।")
        else:
            success, message = save_expense(username, category, int(amount))
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    st.divider()

    if user_df.empty:
        st.info("এখনো কোনো খরচের রেকর্ড নেই। প্রথম খরচটি যোগ করুন।")
    elif df.empty:
        st.info("এই ফিল্টারে কোনো রেকর্ড পাওয়া যায়নি। ফিল্টার বদলে দেখুন।")
    else:
        st.subheader("খরচের বিশ্লেষণ")
        category_df = (
            df.groupby("Khath", as_index=False)["Amount"]
            .sum()
            .sort_values("Amount", ascending=False)
        )

        table_df = category_df.rename(
            columns={"Khath": "খাত", "Amount": "মোট খরচ"}
        )

        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.write("খরচের তালিকা")
            st.dataframe(table_df, use_container_width=True, hide_index=True)

        with right_col:
            st.write("খাত অনুযায়ী পাই চার্ট")
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.pie(
                category_df["Amount"],
                labels=category_df["Khath"],
                autopct="%1.1f%%",
                startangle=90,
                textprops={"fontsize": 10},
            )
            ax.axis("equal")
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

        with st.expander("সব রেকর্ড দেখুন"):
            full_df = df.copy()
            full_df["Date"] = full_df["Date"].dt.strftime("%Y-%m-%d").fillna("তারিখ নেই")
            full_df = full_df.rename(
                columns={
                    "username": "ইউজার",
                    "Date": "তারিখ",
                    "Khath": "খাত",
                    "Amount": "টাকা",
                }
            )
            st.dataframe(full_df[["তারিখ", "খাত", "টাকা"]], use_container_width=True, hide_index=True)

        st.subheader("স্মার্ট বাজেট ফোরকাস্ট")
        if st.button("ফোরকাস্ট ও পরামর্শ তৈরি করুন"):
            show_forecast(df, category_df, remaining_budget)
