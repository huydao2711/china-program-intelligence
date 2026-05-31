"""
crawl/extractor.py — Use Gemini to extract program info from raw webpage text.
"""
import os, json, re, time
import requests

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

EXTRACT_PROMPT_TEMPLATE = (
    "You are extracting China summer camp / exchange program data from a webpage.\n\n"
    "From the text below, extract ALL distinct programs/camps/exchanges you can find.\n"
    "For each program return a JSON object with these exact fields (use null if unknown):\n\n"
    "program_name_en, chinese_name, organization, program_type, country_eligibility,\n"
    "online_offline (Online/Offline/Hybrid), city, province, duration, start_date, end_date,\n"
    "last_active_year, recurring (Yes/No/Unknown), target_group (Student/Teacher/Researcher/Youth/Public),\n"
    "age_requirement, language_req, hsk_requirement, degree_requirement,\n"
    "fully_funded (Yes/Partial/No/Unknown), scholarship_amount,\n"
    "tuition_covered, accommodation_covered, flight_covered, stipend,\n"
    "deadline, application_link, official_website, contact_email, wechat_account, contact_person,\n"
    "description, activities, exchange_type, internship (Yes/No), certificate (Yes/No),\n"
    "credits_transfer (Yes/No/Unknown), still_active (Yes/No/Unknown),\n"
    "confidence (float 0.0-1.0 how confident this is a real program)\n\n"
    "Return ONLY a valid JSON array of objects. If no programs found, return [].\n"
    "Omit any program with confidence < 0.3.\n\n"
    "WEBPAGE TEXT:\n"
)


def _parse_json_robust(content: str):
    """Try multiple strategies to parse possibly-truncated JSON."""
    # Strategy 1: direct parse
    try:
        return json.loads(content)
    except Exception:
        pass
    # Strategy 2: find array boundaries
    start = content.find('[')
    if start == -1:
        # Try single object
        start = content.find('{')
        if start == -1:
            return None
        end = content.rfind('}')
        if end == -1:
            return None
        try:
            return [json.loads(content[start:end + 1])]
        except Exception:
            return None
    end = content.rfind(']')
    if end != -1:
        try:
            return json.loads(content[start:end + 1])
        except Exception:
            pass
    # Strategy 3: extract complete objects one by one (handles truncated array)
    programs = []
    depth = 0
    obj_start = None
    i = start + 1  # skip opening [
    while i < len(content):
        c = content[i]
        if c == '{':
            if depth == 0:
                obj_start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and obj_start is not None:
                try:
                    programs.append(json.loads(content[obj_start:i + 1]))
                except Exception:
                    pass
                obj_start = None
        i += 1
    return programs if programs else None


def extract_programs(text: str, source_url: str, source_name: str) -> list:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("[Extractor] No GEMINI_API_KEY set")
        return []

    text_snippet = text[:5000]
    prompt = EXTRACT_PROMPT_TEMPLATE + text_snippet

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
        },
    }

    for attempt in range(5):
        try:
            resp = requests.post(
                f"{GEMINI_URL}?key={api_key}",
                json=payload,
                timeout=60,
            )
            if resp.status_code == 400:
                print(f"[Extractor] Gemini 400: {resp.text[:300]}")
                return []  # bad request — don't retry
            if resp.status_code in (429, 503):
                wait = 15 * (2 ** attempt)
                print(f"[Extractor] Gemini {resp.status_code} — retry {attempt+1}/5 in {wait}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        except requests.exceptions.Timeout:
            wait = 15 * (2 ** attempt)
            print(f"[Extractor] Timeout — retry {attempt+1}/5 in {wait}s")
            time.sleep(wait)
        except Exception as e:
            print(f"[Extractor] Error: {e}")
            return []
    else:
        print("[Extractor] Gemini unavailable after 5 retries")
        return []

    try:
        raw = resp.json()
        content = raw["candidates"][0]["content"]["parts"][0]["text"]

        # Strip markdown code fences
        content = re.sub(r'```(?:json)?', '', content).strip()

        programs = _parse_json_robust(content)
        if programs is None:
            print(f"[Extractor] No JSON in response: {content[:150]}")
            return []

        from datetime import date
        today = date.today().isoformat()

        for p in programs:
            p["source_url"]       = source_url
            p["platform_source"]  = source_name
            p["scraped_date"]     = today
            p["duplicate_check"]  = ""
            p["notes"]            = ""
            p["applied"]          = ""
            p["followed"]         = ""
            p["contacted"]        = ""
            p["response_status"]  = ""
            p["interview_status"] = ""
            p["priority_level"]   = ""
            p["personal_notes"]   = ""

        return [p for p in programs if float(p.get("confidence") or 0) >= 0.3]

    except Exception as e:
        print(f"[Extractor] Error: {e}")
        return []


def programs_to_rows(programs: list) -> list:
    """Convert extracted program dicts to sheet rows matching COLUMNS order."""
    FIELD_ORDER = [
        "program_name_en", "chinese_name", "organization", "program_type",
        "country_eligibility", "online_offline", "city", "province",
        "duration", "start_date", "end_date", "last_active_year", "recurring",
        "target_group", "age_requirement", "language_req", "hsk_requirement", "degree_requirement",
        "fully_funded", "scholarship_amount", "tuition_covered", "accommodation_covered",
        "flight_covered", "stipend",
        "deadline", "application_link", "official_website", "contact_email",
        "wechat_account", "contact_person",
        "description", "activities", "exchange_type", "internship",
        "certificate", "credits_transfer",
        "source_url", "platform_source", "scraped_date", "confidence",
        "duplicate_check", "still_active", "notes",
        "applied", "followed", "contacted", "response_status",
        "interview_status", "priority_level", "personal_notes",
    ]
    rows = []
    for p in programs:
        row = [str(p.get(f, "") or "") for f in FIELD_ORDER]
        rows.append(row)
    return rows
