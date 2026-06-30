import time
import re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import streamlit as st
import streamlit_authenticator as stauth
import streamlit.components.v1 as components

try:
    import gspread
except ImportError:
    gspread = None

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
        [data-testid="stFooter"],
        [data-testid="stFooterIcon"],
        [data-testid="stFooterLink"],
        [data-testid="stStatusWidget"],
        [data-testid="manage-app-button"],
        [data-testid="stAppDeployButton"],
        .stDeployButton,
        [class*="viewerBadge"],
        [class*="styles_viewerBadge"],
        [class*="githubButton"],
        [class*="streamlit-footer"],
        [class*="footer"],
        [data-testid="baseButton-headerNoPadding"],
        iframe[title="streamlit_authenticator"],
        a[href*="github.com/streamlit"],
        a[href*="streamlit.io"],
        a[href*="share.streamlit.io"],
        button[title*="GitHub"],
        button[title*="Streamlit"],
        button[aria-label*="GitHub"],
        button[aria-label*="Streamlit"],
        div[class*="StatusWidget"],
        div[class*="ReportStatus"],
        section[data-testid="stSidebarNavItems"] + div {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
        }

        footer:has(a[href*="github.com/streamlit"]),
        footer:has(a[href*="streamlit.io"]) {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
        }

        /* ── Light mode ── */
        @media (prefers-color-scheme: light) {
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(16, 185, 129, 0.12), transparent 28rem),
                    linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
            }
            [data-testid="stMetric"] { background: rgba(255,255,255,0.92); border: 1px solid #e2e8f0; }
        }

        /* ── Dark mode ── */
        @media (prefers-color-scheme: dark) {
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(20, 184, 166, 0.16), transparent 28rem),
                    linear-gradient(180deg, #0f172a 0%, #111827 100%) !important;
            }

            [data-testid="stMetric"] {
                background: rgba(15, 23, 42, 0.84) !important;
                border: 1px solid rgba(148, 163, 184, 0.22) !important;
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

            .stProgress > div > div { background: linear-gradient(90deg, #14b8a6, #f59e0b) !important; }

            .stProgress {
                background-color: #273449 !important;
            }

            [data-testid="stExpander"] {
                background: rgba(15, 23, 42, 0.82) !important;
                border: 1px solid rgba(148, 163, 184, 0.2) !important;
            }

            .stButton > button,
            .stFormSubmitButton > button {
                background: linear-gradient(135deg, #0f766e, #15803d) !important;
                color: #ffffff !important;
                border: none !important;
            }

            .stButton > button:hover,
            .stFormSubmitButton > button:hover {
                background: linear-gradient(135deg, #0d9488, #16a34a) !important;
            }

            [data-testid="stTextInput"] input,
            [data-testid="stNumberInput"] input {
                background: #111827 !important;
                color: #e8eaf6 !important;
                border: 1px solid rgba(148, 163, 184, 0.28) !important;
            }

            [data-testid="stForm"] {
                background: rgba(15, 23, 42, 0.82) !important;
                border: 1px solid rgba(148, 163, 184, 0.2) !important;
                border-radius: 8px !important;
                padding: 1.1rem !important;
            }

            section[data-testid="stSidebar"] {
                background: #0f172a !important;
                border-right: 1px solid rgba(148, 163, 184, 0.18) !important;
            }

            .stAlert {
                background: #1e2130 !important;
                border: 1px solid #3d4265 !important;
            }

            .stInfo { border-left: 4px solid #14b8a6 !important; }
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
                background: #0f766e !important;
                color: #ffffff !important;
            }
        }

        /* ── Streamlit also sets data-theme attribute ── */
        [data-theme="dark"] .stApp { background: #0f1117 !important; }

        [data-theme="dark"] [data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.84) !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
        }

        [data-theme="dark"] .stButton > button,
        [data-theme="dark"] .stFormSubmitButton > button {
            background: linear-gradient(135deg, #0f766e, #15803d) !important;
            color: #fff !important;
            border: none !important;
        }

        [data-theme="dark"] [data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.82) !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }

        [data-theme="dark"] section[data-testid="stSidebar"] {
            background: #0f172a !important;
        }

        /* ── Shared metric style ── */
        [data-testid="stMetric"] {
            border-radius: 8px;
            padding: 1.05rem 1.1rem;
            box-shadow: 0 14px 30px rgba(15,23,42,0.08);
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
            border: 0;
            background: linear-gradient(135deg, #0f766e, #15803d);
            color: #ffffff;
            box-shadow: 0 12px 22px rgba(15, 118, 110, 0.22);
            transition: background 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background: linear-gradient(135deg, #0d9488, #16a34a);
            color: #ffffff;
            box-shadow: 0 14px 26px rgba(15, 118, 110, 0.28);
        }

        .stButton > button:active,
        .stFormSubmitButton > button:active {
            transform: scale(0.98);
        }

        /* ── DataFrame ── */
        div[data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.22);
        }

        /* ── Sidebar font ── */
        section[data-testid="stSidebar"] {
            font-family: "Noto Sans Bengali", "Hind Siliguri", "SolaimanLipi", sans-serif;
        }

        /* ── Layout ── */
        .block-container {
            max-width: 1180px;
            padding-top: 1.1rem;
            padding-bottom: 2.4rem;
        }

        h1, h2, h3 { letter-spacing: 0; }
        h1 { font-weight: 800; }
        h2, h3 { font-weight: 700; }

        div[data-testid="stVerticalBlock"] { gap: 1rem; }

        .app-hero {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 8px;
            padding: 1.35rem 1.45rem;
            margin: 0.35rem 0 1rem;
            background:
                linear-gradient(135deg, rgba(15, 118, 110, 0.96), rgba(17, 24, 39, 0.94)),
                radial-gradient(circle at 92% 10%, rgba(245, 158, 11, 0.35), transparent 18rem);
            color: #ffffff;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.16);
        }

        .app-hero h1 {
            margin: 0.25rem 0 0.35rem;
            color: #ffffff;
            font-size: clamp(2rem, 3vw, 3.1rem);
            line-height: 1.12;
        }

        .app-hero p, .app-hero span, .app-hero strong { color: rgba(255,255,255,0.9); }

        .hero-topline {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }

        .hero-pill {
            display: inline-flex;
            align-items: center;
            min-height: 2rem;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.18);
            font-size: 0.92rem;
            font-weight: 700;
        }

        .hero-stats {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 1.15rem;
        }

        .hero-stat {
            min-height: 5.3rem;
            padding: 0.8rem 0.9rem;
            border-radius: 8px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.16);
        }

        .hero-stat span {
            display: block;
            font-size: 0.82rem;
            opacity: 0.82;
            margin-bottom: 0.25rem;
        }

        .hero-stat strong {
            display: block;
            font-size: 1.2rem;
            line-height: 1.25;
        }

        .section-title {
            margin: 1rem 0 0.15rem;
        }

        .section-title h2 {
            margin: 0;
            font-size: 1.35rem;
        }

        .section-title p {
            margin: 0.2rem 0 0;
            color: #64748b;
        }

        [data-testid="stForm"],
        [data-testid="stExpander"] {
            border-radius: 8px !important;
            box-shadow: 0 12px 28px rgba(15,23,42,0.07);
        }

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input {
            border-radius: 8px !important;
            min-height: 2.7rem;
        }

        .stProgress > div {
            height: 0.85rem;
            border-radius: 999px;
        }

        .stProgress > div > div {
            border-radius: 999px;
            background: linear-gradient(90deg, #14b8a6, #f59e0b);
        }

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

            .app-hero { padding: 1rem; }
            .hero-stats { grid-template-columns: 1fr; }

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


def get_user_expense_path(username: str) -> Path:
    return Path(f"expenses_{username}.csv")


def get_spreadsheet_id() -> str:
    match = re.search(r"/spreadsheets/d/([^/]+)", GOOGLE_SHEET_URL)
    return match.group(1) if match else ""


def get_google_service_account_info() -> dict | None:
    for key in ("google_service_account", "gcp_service_account"):
        try:
            info = st.secrets.get(key)
        except Exception:
            info = None

        if info:
            info = dict(info)
            if "private_key" in info:
                info["private_key"] = info["private_key"].replace("\\n", "\n")
            return info

    return None


def get_google_worksheet():
    if gspread is None:
        return None, "Google Sheet এডিট করতে gspread package install করতে হবে।"

    service_account_info = get_google_service_account_info()
    if not service_account_info:
        return None, "Google Sheet এডিট করতে secrets.toml-এ google_service_account সেট করুন।"

    spreadsheet_id = get_spreadsheet_id()
    if not spreadsheet_id:
        return None, "google_sheet_url থেকে Spreadsheet ID পাওয়া যায়নি।"

    try:
        client = gspread.service_account_from_dict(service_account_info)
        workbook = client.open_by_key(spreadsheet_id)
        worksheet_name = st.secrets.get("google_sheet_worksheet", "")
        worksheet = workbook.worksheet(worksheet_name) if worksheet_name else workbook.sheet1
        return worksheet, ""
    except Exception as exc:
        return None, f"Google Sheet খুলতে সমস্যা হয়েছে: {exc}"


def find_header(headers: list[str], candidates: list[str]) -> str | None:
    normalized = {str(header).strip().lower(): header for header in headers}
    for candidate in candidates:
        header = normalized.get(candidate.lower())
        if header is not None:
            return header
    return None


def get_sheet_column_map(headers: list[str]) -> dict:
    return {
        "username": find_header(headers, ["username", "user", "name", "নাম", "ইউজার"]),
        "date": find_header(headers, ["timestamp", "date", "তারিখ"]),
        "category": find_header(headers, ["khath", "category", "খাত"]),
        "amount": find_header(headers, ["amount", "টাকা"]),
    }


def load_google_sheet_editable_expenses(username: str) -> tuple[pd.DataFrame, str]:
    worksheet, error = get_google_worksheet()
    if error:
        return pd.DataFrame(columns=["Source", "Row", "Date", "Category", "Amount"]), error

    rows = worksheet.get_all_records()
    headers = worksheet.row_values(1)
    column_map = get_sheet_column_map(headers)
    missing_columns = [column for column in ["username", "date", "category", "amount"] if not column_map[column]]
    if missing_columns:
        return (
            pd.DataFrame(columns=["Source", "Row", "Date", "Category", "Amount"]),
            f"Google Sheet header পাওয়া যায়নি: {', '.join(missing_columns)}",
        )

    editable_rows = []
    for row_number, row in enumerate(rows, start=2):
        row_username = str(row.get(column_map["username"], "")).strip()
        if row_username != username:
            continue

        amount = pd.to_numeric(row.get(column_map["amount"], 0), errors="coerce")
        editable_rows.append(
            {
                "Source": "Google Sheet",
                "Row": row_number,
                "Date": pd.to_datetime(row.get(column_map["date"], ""), errors="coerce").date(),
                "Category": str(row.get(column_map["category"], "")).strip(),
                "Amount": int(0 if pd.isna(amount) else amount),
            }
        )

    return pd.DataFrame(editable_rows, columns=["Source", "Row", "Date", "Category", "Amount"]), ""


def load_editable_expenses(username: str) -> pd.DataFrame:
    path = get_user_expense_path(username)
    google_df, _ = load_google_sheet_editable_expenses(username)

    if not path.exists():
        return google_df

    data = normalize_expenses(pd.read_csv(path), username)
    data = data.rename(columns={"Khath": "Category"})
    data["Date"] = data["Date"].dt.date
    data["Source"] = "লোকাল CSV"
    data["Row"] = range(1, len(data) + 1)
    local_df = data[["Source", "Row", "Date", "Category", "Amount"]]
    return pd.concat([google_df, local_df], ignore_index=True)


def save_editable_expenses(username: str, data: pd.DataFrame) -> tuple[bool, str]:
    path = get_user_expense_path(username)
    cleaned = data.copy()

    for column in ["Date", "Category", "Amount"]:
        if column not in cleaned.columns:
            return False, f"কলাম পাওয়া যায়নি: {column}"

    cleaned = cleaned[["Date", "Category", "Amount"]].copy()
    cleaned["Category"] = cleaned["Category"].fillna("").astype(str).str.strip()
    cleaned["Amount"] = pd.to_numeric(cleaned["Amount"], errors="coerce").fillna(0).astype(int)
    cleaned["Date"] = pd.to_datetime(cleaned["Date"], errors="coerce")
    cleaned = cleaned[(cleaned["Category"] != "") & (cleaned["Amount"] > 0)]

    output = pd.DataFrame(
        {
            "username": username,
            "Date": cleaned["Date"],
            "Khath": cleaned["Category"],
            "Amount": cleaned["Amount"],
        }
    )
    output.to_csv(path, index=False, encoding="utf-8")
    return True, "রেকর্ড সফলভাবে আপডেট হয়েছে।"


def save_google_sheet_editable_expenses(data: pd.DataFrame) -> tuple[bool, str]:
    worksheet, error = get_google_worksheet()
    if error:
        return False, error

    headers = worksheet.row_values(1)
    column_map = get_sheet_column_map(headers)
    missing_columns = [column for column in ["date", "category", "amount"] if not column_map[column]]
    if missing_columns:
        return False, f"Google Sheet header পাওয়া যায়নি: {', '.join(missing_columns)}"

    header_positions = {header: index + 1 for index, header in enumerate(headers)}
    try:
        for _, row in data.iterrows():
            row_number = int(row["Row"])
            worksheet.update_cell(row_number, header_positions[column_map["date"]], str(row["Date"]))
            worksheet.update_cell(row_number, header_positions[column_map["category"]], str(row["Category"]).strip())
            worksheet.update_cell(row_number, header_positions[column_map["amount"]], int(row["Amount"]))
    except Exception as exc:
        return False, f"Google Sheet update করতে সমস্যা হয়েছে: {exc}"

    return True, "Google Sheet রেকর্ড সফলভাবে আপডেট হয়েছে।"


def save_editable_expenses(username: str, data: pd.DataFrame) -> tuple[bool, str]:
    cleaned = data.copy()
    for column in ["Source", "Row", "Date", "Category", "Amount"]:
        if column not in cleaned.columns:
            return False, f"কলাম পাওয়া যায়নি: {column}"

    cleaned["Category"] = cleaned["Category"].fillna("").astype(str).str.strip()
    cleaned["Amount"] = pd.to_numeric(cleaned["Amount"], errors="coerce").fillna(0).astype(int)
    cleaned["Date"] = pd.to_datetime(cleaned["Date"], errors="coerce").dt.date
    cleaned = cleaned[(cleaned["Category"] != "") & (cleaned["Amount"] > 0)]

    google_rows = cleaned[cleaned["Source"] == "Google Sheet"].copy()
    local_rows = cleaned[cleaned["Source"] != "Google Sheet"].copy()

    output = pd.DataFrame(
        {
            "username": username,
            "Date": pd.to_datetime(local_rows["Date"], errors="coerce"),
            "Khath": local_rows["Category"],
            "Amount": local_rows["Amount"],
        }
    )
    output.to_csv(get_user_expense_path(username), index=False, encoding="utf-8")

    if not google_rows.empty:
        success, message = save_google_sheet_editable_expenses(google_rows)
        if not success:
            return success, message

    return True, "সব রেকর্ড সফলভাবে আপডেট হয়েছে।"


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


def section_title(title: str, subtitle: str = "") -> None:
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="section-title">
            <h2>{title}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(name: str, total_records: int, total_spent: int, remaining_budget: int) -> None:
    st.markdown(
        f"""
        <section class="app-hero">
            <div class="hero-topline">
                <span class="hero-pill">ব্যক্তিগত ড্যাশবোর্ড</span>
                <span class="hero-pill">লগইন: {name}</span>
            </div>
            <h1>আমার স্মার্ট মানি ম্যানেজার</h1>
            <p>দৈনন্দিন খরচ, বাজেট এবং সেভিংস এক জায়গায় পরিষ্কারভাবে দেখুন।</p>
            <div class="hero-stats">
                <div class="hero-stat">
                    <span>মোট রেকর্ড</span>
                    <strong>{total_records}টি</strong>
                </div>
                <div class="hero-stat">
                    <span>এখন পর্যন্ত খরচ</span>
                    <strong>{format_taka(total_spent)}</strong>
                </div>
                <div class="hero-stat">
                    <span>বাকি বাজেট</span>
                    <strong>{format_taka(remaining_budget)}</strong>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def filter_expenses(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    section_title("ফিল্টার", "খাত, টাকা ও তারিখ অনুযায়ী রিপোর্ট সাজিয়ে নিন।")

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


def render_hamburger_menu_button() -> None:
    components.html(
        """
        <script>
            const parentDoc = window.parent.document;
            const buttonId = "custom-sidebar-toggle";
            let toggleButton = parentDoc.getElementById(buttonId);

            if (!toggleButton) {
                toggleButton = parentDoc.createElement("button");
                toggleButton.id = buttonId;
                toggleButton.type = "button";
                toggleButton.setAttribute("aria-label", "মেনু খুলুন");
                toggleButton.innerHTML = "<span></span><span></span><span></span>";
                parentDoc.body.appendChild(toggleButton);
            }

            toggleButton.onclick = () => {
                const streamlitToggle =
                    parentDoc.querySelector('[data-testid="collapsedControl"] button') ||
                    parentDoc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                    parentDoc.querySelector('button[aria-label="Open sidebar"]') ||
                    parentDoc.querySelector('button[aria-label="Close sidebar"]') ||
                    parentDoc.querySelector('button[data-testid="baseButton-headerNoPadding"]');

                if (streamlitToggle) {
                    streamlitToggle.click();
                }
            };

            const styleId = "custom-sidebar-toggle-style";
            if (!parentDoc.getElementById(styleId)) {
                const style = parentDoc.createElement("style");
                style.id = styleId;
                style.textContent = `
                    #custom-sidebar-toggle {
                        position: fixed;
                        top: 0.9rem;
                        left: 0.9rem;
                        z-index: 999999;
                        width: 2.7rem;
                        height: 2.7rem;
                        display: inline-flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        gap: 0.28rem;
                        border: 1px solid rgba(148, 163, 184, 0.28);
                        border-radius: 8px;
                        background: rgba(15, 118, 110, 0.96);
                        box-shadow: 0 12px 26px rgba(15, 23, 42, 0.2);
                        cursor: pointer;
                    }

                    #custom-sidebar-toggle span {
                        width: 1.25rem;
                        height: 0.14rem;
                        border-radius: 999px;
                        background: #ffffff;
                        display: block;
                    }

                    #custom-sidebar-toggle:hover {
                        background: #0d9488;
                    }

                    @media (max-width: 720px) {
                        #custom-sidebar-toggle {
                            top: 0.7rem;
                            left: 0.7rem;
                        }
                    }
                `;
                parentDoc.head.appendChild(style);
            }
        </script>
        """,
        height=0,
        width=0,
    )


def render_sidebar_navigation() -> str:
    return st.sidebar.radio(
        "মেনু",
        [
            "ব্যক্তিগত ড্যাশবোর্ড",
            "বাজেট সারাংশ",
            "খরচ বিশ্লেষণ",
            "ফোরকাস্টিং",
            "রেকর্ড এডিট",
        ],
        key="selected_dashboard_section",
    )


def render_add_expense_form(username: str) -> None:
    section_title("নতুন খরচ যোগ করুন", "খরচ লিখে সেভ করলে রিপোর্ট আপডেট হবে।")
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


def render_edit_records(username: str) -> None:
    section_title("রেকর্ড এডিট", "ভুল ইনপুট হলে তারিখ, খাত বা টাকার পরিমাণ ঠিক করে নিন।")
    st.caption("গুগল শিটের রেকর্ড এখানে সরাসরি এডিট করা যাবে না। লোকাল CSV রেকর্ড এডিট, যোগ বা মুছে ফেলা যাবে।")

    editable_df = load_editable_expenses(username)
    edited_df = st.data_editor(
        editable_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Date": st.column_config.DateColumn("তারিখ"),
            "Category": st.column_config.TextColumn("খাত", required=True),
            "Amount": st.column_config.NumberColumn("টাকা", min_value=1, step=1, required=True),
        },
        key="expense_edit_table",
    )

    if st.button("পরিবর্তন সেভ করুন", key="save_edited_expenses"):
        success, message = save_editable_expenses(username, edited_df)
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


def render_budget_summary(df: pd.DataFrame) -> None:
    total_spent = int(df["Amount"].sum()) if not df.empty else 0
    remaining_budget = TOTAL_BUDGET - total_spent
    used_percent = min(100, round((total_spent / TOTAL_BUDGET) * 100))

    section_title("বাজেট সারাংশ", "ফিল্টার করা ডেটার ওপর ভিত্তি করে বর্তমান হিসাব।")
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("মোট বাজেট", format_taka(TOTAL_BUDGET))
    metric_2.metric("মোট খরচ", format_taka(total_spent), delta=f"-{format_taka(total_spent)}" if total_spent else None)
    metric_3.metric("বাকি বাজেট", format_taka(remaining_budget))
    st.progress(used_percent / 100, text=f"বাজেটের {used_percent}% ব্যবহার হয়েছে")


def build_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Khath", "Amount"])
    return (
        df.groupby("Khath", as_index=False)["Amount"]
        .sum()
        .sort_values("Amount", ascending=False)
    )


def render_cost_analysis(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("এই ফিল্টারে কোনো রেকর্ড পাওয়া যায়নি। ফিল্টার বদলে দেখুন।")
        return

    section_title("খরচের বিশ্লেষণ", "কোন খাতে কত টাকা যাচ্ছে তা দ্রুত বোঝার জন্য।")
    category_df = build_category_summary(df)
    table_df = category_df.rename(
        columns={"Khath": "খাত", "Amount": "মোট খরচ"}
    )

    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.markdown("**খরচের তালিকা**")
        st.dataframe(table_df, use_container_width=True, hide_index=True)

    with right_col:
        st.markdown("**খাত অনুযায়ী চার্ট**")
        chart_colors = [
            "#0f766e",
            "#f59e0b",
            "#2563eb",
            "#db2777",
            "#16a34a",
            "#7c3aed",
            "#ea580c",
            "#0891b2",
        ]
        fig, ax = plt.subplots(figsize=(5.4, 5.4), facecolor="none")
        ax.pie(
            category_df["Amount"],
            labels=category_df["Khath"],
            autopct="%1.1f%%",
            startangle=90,
            colors=chart_colors[: len(category_df)],
            pctdistance=0.78,
            wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
            textprops={"fontsize": 10, "fontfamily": "sans-serif"},
        )
        ax.axis("equal")
        ax.set_facecolor("none")
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


def render_forecasting(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("ফোরকাস্ট তৈরি করার জন্য খরচের রেকর্ড দরকার।")
        return

    total_spent = int(df["Amount"].sum())
    remaining_budget = TOTAL_BUDGET - total_spent
    section_title("স্মার্ট বাজেট ফোরকাস্ট", "আপনার বর্তমান খরচের প্যাটার্ন থেকে ছোট্ট পরামর্শ।")
    if st.button("ফোরকাস্ট ও পরামর্শ তৈরি করুন"):
        show_forecast(df, build_category_summary(df), remaining_budget)


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

elif authentication_status:
    render_hamburger_menu_button()
    authenticator.logout("লগআউট", "sidebar")
    st.sidebar.title(f"স্বাগতম, {name}!")
    selected_section = render_sidebar_navigation()

    all_data = load_expenses()
    user_df = all_data[all_data["username"] == username].copy()

    total_records = len(user_df)
    all_total_spent = int(user_df["Amount"].sum()) if not user_df.empty else 0
    all_remaining_budget = TOTAL_BUDGET - all_total_spent

    if selected_section == "ব্যক্তিগত ড্যাশবোর্ড":
        render_hero(name, total_records, all_total_spent, all_remaining_budget)
        render_add_expense_form(username)
        if user_df.empty:
            st.info("এখনো কোনো খরচের রেকর্ড নেই। এই ড্যাশবোর্ড থেকে প্রথম খরচ যোগ করুন।")
        else:
            recent_df = user_df.sort_values("Date", ascending=False).head(8).copy()
            recent_df["Date"] = recent_df["Date"].dt.strftime("%Y-%m-%d").fillna("তারিখ নেই")
            recent_df = recent_df.rename(
                columns={
                    "Date": "তারিখ",
                    "Khath": "খাত",
                    "Amount": "টাকা",
                }
            )
            section_title("সাম্প্রতিক রেকর্ড")
            st.dataframe(recent_df[["তারিখ", "খাত", "টাকা"]], use_container_width=True, hide_index=True)
    elif selected_section == "রেকর্ড এডিট":
        render_edit_records(username)
    else:
        filtered_df = filter_expenses(user_df)
        if selected_section == "বাজেট সারাংশ":
            render_budget_summary(filtered_df)
        elif selected_section == "খরচ বিশ্লেষণ":
            render_cost_analysis(filtered_df)
        elif selected_section == "ফোরকাস্টিং":
            render_forecasting(filtered_df)

    st.stop()
    authenticator.logout("লগআউট", "sidebar")
    st.sidebar.title(f"স্বাগতম, {name}!")
    st.sidebar.caption("আপনার ব্যক্তিগত খরচের হিসাব")

    all_data = load_expenses()
    user_df = all_data[all_data["username"] == username].copy()

    total_records = len(user_df)
    all_total_spent = int(user_df["Amount"].sum()) if not user_df.empty else 0
    all_remaining_budget = TOTAL_BUDGET - all_total_spent
    render_hero(name, total_records, all_total_spent, all_remaining_budget)

    df = filter_expenses(user_df)

    total_spent = int(df["Amount"].sum()) if not df.empty else 0
    remaining_budget = TOTAL_BUDGET - total_spent
    used_percent = min(100, round((total_spent / TOTAL_BUDGET) * 100))

    section_title("বাজেট সারাংশ", "ফিল্টার করা ডেটার ওপর ভিত্তি করে বর্তমান হিসাব।")
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("মোট বাজেট", format_taka(TOTAL_BUDGET))
    metric_2.metric("মোট খরচ", format_taka(total_spent), delta=f"-{format_taka(total_spent)}" if total_spent else None)
    metric_3.metric("বাকি বাজেট", format_taka(remaining_budget))

    st.progress(used_percent / 100, text=f"বাজেটের {used_percent}% ব্যবহার হয়েছে")

    section_title("নতুন খরচ যোগ করুন", "খরচ লিখে সেভ করলে রিপোর্ট আপডেট হবে।")
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
        section_title("খরচের বিশ্লেষণ", "কোন খাতে কত টাকা যাচ্ছে তা দ্রুত বোঝার জন্য।")
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
            st.markdown("**খরচের তালিকা**")
            st.dataframe(table_df, use_container_width=True, hide_index=True)

        with right_col:
            st.markdown("**খাত অনুযায়ী চার্ট**")
            chart_colors = [
                "#0f766e",
                "#f59e0b",
                "#2563eb",
                "#db2777",
                "#16a34a",
                "#7c3aed",
                "#ea580c",
                "#0891b2",
            ]
            fig, ax = plt.subplots(figsize=(5.4, 5.4), facecolor="none")
            ax.pie(
                category_df["Amount"],
                labels=category_df["Khath"],
                autopct="%1.1f%%",
                startangle=90,
                colors=chart_colors[: len(category_df)],
                pctdistance=0.78,
                wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
                textprops={"fontsize": 10, "fontfamily": "sans-serif"},
            )
            ax.axis("equal")
            ax.set_facecolor("none")
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

        section_title("স্মার্ট বাজেট ফোরকাস্ট", "আপনার বর্তমান খরচের প্যাটার্ন থেকে ছোট্ট পরামর্শ।")
        if st.button("ফোরকাস্ট ও পরামর্শ তৈরি করুন"):
            show_forecast(df, category_df, remaining_budget)
