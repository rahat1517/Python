import time
from pathlib import Path

import numpy as np
import pandas as pd
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
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;500;600;700&display=swap');

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: "Noto Sans Bengali", "Hind Siliguri", "SolaimanLipi", sans-serif;
        }

        .stApp {
            background: #f7f8fb;
        }

        .block-container {
            max-width: 1120px;
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            letter-spacing: 0;
        }

        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e6e9f0;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }

        [data-testid="stMetricLabel"] p,
        [data-testid="stMetricValue"] {
            font-family: "Noto Sans Bengali", "Hind Siliguri", "SolaimanLipi", sans-serif;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            width: 100%;
            min-height: 2.8rem;
            border-radius: 8px;
            font-weight: 700;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
        }

        section[data-testid="stSidebar"] {
            font-family: "Noto Sans Bengali", "Hind Siliguri", "SolaimanLipi", sans-serif;
        }

        @media (max-width: 720px) {
            .block-container {
                padding: 0.9rem 0.85rem 1.5rem;
            }

            h1 {
                font-size: 1.75rem;
                line-height: 1.25;
            }

            h2, h3 {
                font-size: 1.2rem;
            }

            [data-testid="stMetric"] {
                padding: 0.85rem;
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
        "খাত": "Khath",
        "Category": "Khath",
        "Amount": "Amount",
        "amount": "Amount",
        "টাকা": "Amount",
    }
    data = data.rename(columns=rename_map)

    for column in ["username", "Khath", "Amount"]:
        if column not in data.columns:
            data[column] = fallback_username if column == "username" else np.nan

    data = data[["username", "Khath", "Amount"]].copy()
    data["username"] = data["username"].fillna(fallback_username).astype(str).str.strip()
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
        return pd.DataFrame(columns=["username", "Khath", "Amount"])
    return pd.concat(expenses, ignore_index=True)


def load_expenses() -> pd.DataFrame:
    try:
        data = normalize_expenses(pd.read_csv(get_csv_url()))
    except Exception:
        data = pd.DataFrame(columns=["username", "Khath", "Amount"])

    local_data = load_local_expenses()
    if data.empty:
        return local_data
    if local_data.empty:
        return data
    return pd.concat([data, local_data], ignore_index=True)


def save_local_expense(username: str, category: str, amount: int) -> None:
    path = Path(f"expenses_{username}.csv")
    new_row = pd.DataFrame(
        [{"username": username, "Khath": category, "Amount": int(amount)}]
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
    df = all_data[all_data["username"] == username].copy()

    total_spent = int(df["Amount"].sum()) if not df.empty else 0
    remaining_budget = TOTAL_BUDGET - total_spent
    used_percent = min(100, round((total_spent / TOTAL_BUDGET) * 100))

    st.title("💰 আমার স্মার্ট মানি ম্যানেজার")
    st.caption(f"লগইন করা ইউজার: {name}")

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

    if df.empty:
        st.info("এখনো কোনো খরচের রেকর্ড নেই। প্রথম খরচটি যোগ করুন।")
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

        chart_df = table_df.set_index("খাত")
        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.write("খরচের তালিকা")
            st.dataframe(table_df, use_container_width=True, hide_index=True)

        with right_col:
            st.write("খাত অনুযায়ী খরচ")
            st.bar_chart(chart_df, use_container_width=True)

        with st.expander("সব রেকর্ড দেখুন"):
            full_df = df.rename(
                columns={"username": "ইউজার", "Khath": "খাত", "Amount": "টাকা"}
            )
            st.dataframe(full_df[["খাত", "টাকা"]], use_container_width=True, hide_index=True)

        st.subheader("স্মার্ট বাজেট ফোরকাস্ট")
        if st.button("ফোরকাস্ট ও পরামর্শ তৈরি করুন"):
            show_forecast(df, category_df, remaining_budget)
