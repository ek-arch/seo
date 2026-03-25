"""
sheets_client.py — Google Sheets integration for Kolo SEO Agent
================================================================
Pushes comment queue and audit results to a shared Google Sheet.
Uses service account JSON key for authentication.
"""

import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Sheet ID extracted from URL
SHEET_ID = "1EoXaNgpF9Rg4Q-KksFL9d5k5ScDtAF0m7qbg4JxHW4k"


def _get_client(creds_json: str) -> gspread.Client:
    """Authenticate with Google Sheets using service account JSON."""
    if isinstance(creds_json, str):
        creds_info = json.loads(creds_json)
    else:
        creds_info = creds_json
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)


def push_comments(creds_json: str, comments: list[dict], sheet_name: str = "Comments") -> int:
    """
    Push NEW comments to Google Sheet (append-only, never erases old rows).
    Creates the sheet tab if it doesn't exist.
    Skips comments whose URL is already in the sheet.
    Returns number of NEW rows added.
    """
    gc = _get_client(creds_json)
    spreadsheet = gc.open_by_key(SHEET_ID)

    # Get or create sheet
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
        ws.update("A1:G1", [["Date", "Post URL", "Post Title", "Platform", "Community", "Comment", "Status"]])
        ws.format("A1:G1", {"textFormat": {"bold": True}})

    # Read existing URLs to avoid duplicates
    existing_urls = set()
    try:
        url_col = ws.col_values(2)  # Column B = Post URL
        existing_urls = set(url_col[1:])  # Skip header
    except Exception:
        pass

    # Only append new comments
    import datetime
    today = datetime.date.today().isoformat()
    new_rows = []
    for c in comments:
        url = c.get("url", "")
        if url in existing_urls:
            continue  # Already in sheet
        new_rows.append([
            today,
            url,
            c.get("title", "")[:100],
            c.get("platform", "Reddit"),
            c.get("subreddit", ""),
            c.get("comment", ""),
            c.get("status", "draft"),
        ])

    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")

    return len(new_rows)


def push_audit_results(creds_json: str, results: list[dict], sheet_name: str = "GEO Audit") -> int:
    """
    Push GEO visibility audit results to Google Sheet.
    Creates the sheet tab if it doesn't exist.
    Appends new rows per audit run.
    Returns number of rows added.
    """
    gc = _get_client(creds_json)
    spreadsheet = gc.open_by_key(SHEET_ID)

    try:
        ws = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
        ws.update("A1:H1", [["Date", "Query", "Kolo Visible", "Kolo Position", "Top Result", "Competitors", "AI Overview", "Total Results"]])
        ws.format("A1:H1", {"textFormat": {"bold": True}})

    import datetime
    today = datetime.date.today().isoformat()
    new_rows = []
    for r in results:
        if r.get("error"):
            continue
        ai_mention = ""
        if r.get("ai_overview"):
            ai_mention = "Kolo mentioned" if r["ai_overview"].get("kolo_mentioned") else "No Kolo"
        new_rows.append([
            today,
            r.get("query", ""),
            "Yes" if r.get("kolo_visible") else "No",
            r.get("kolo_position") or "",
            r.get("top_result_domain", ""),
            ", ".join(r.get("competitors_found", [])),
            ai_mention,
            r.get("total_results", 0),
        ])

    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")

    return len(new_rows)


def push_publications(creds_json: str, publications: list[dict], sheet_name: str = "Publications") -> int:
    """Push content plan or publication data to Google Sheet. Handles both formats."""
    gc = _get_client(creds_json)
    spreadsheet = gc.open_by_key(SHEET_ID)

    # Detect format: new content plan vs old publication tracker
    if publications and "Task" in publications[0]:
        # New unified content plan format
        headers = ["Task", "Type", "Market", "Outlet Options", "Price", "GEO", "Week", "Status", "Publication URL", "Reddit/Quora URL"]
        try:
            ws = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=sheet_name, rows=500, cols=len(headers))
        ws.update(f"A1:{chr(64+len(headers))}1", [headers])
        ws.format(f"A1:{chr(64+len(headers))}1", {"textFormat": {"bold": True}})
        ws.batch_clear([f"A2:{chr(64+len(headers))}1000"])
        rows = []
        for p in publications:
            rows.append([p.get(h, "") for h in headers])
        if rows:
            ws.update(f"A2:{chr(64+len(headers))}{len(rows)+1}", rows, value_input_option="USER_ENTERED")
        return len(rows)
    else:
        # Legacy publication tracker format
        headers = ["Outlet", "Lang", "Price ($)", "Status", "Publication URL", "Post to X"]
        try:
            ws = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=sheet_name, rows=500, cols=8)
        ws.update("A1:F1", [headers])
        ws.format("A1:F1", {"textFormat": {"bold": True}})
        ws.batch_clear(["A2:F1000"])
        rows = []
        for p in publications:
            rows.append([p.get(h, "") for h in headers])
        if rows:
            ws.update(f"A2:F{len(rows)+1}", rows, value_input_option="USER_ENTERED")
        return len(rows)
