"""Sorting transactions into categories, in three layers:

1. Rules the user taught us (they corrected a category once, so we remember the merchant).
2. Built-in keyword rules for common merchants.
3. Optionally, an LLM for anything left. Its answer must be one of our fixed categories,
   or we ignore it and mark the transaction Uncategorized. A model can't invent a category."""
import os
import re

from app.models import CATEGORIES

_PREFIX = re.compile(r"^(sq \*|tst\* ?|sp \*|pp\*|paypal \*|pos |debit card purchase |ach |checkcard \d+ )", re.I)
_DROP_WORDS = {"store", "payments", "payment", "usa", "inc", "llc", "direct", "dep", "bill", "help", "trip",
               "mktpl", "paygo", "nyct", "subscription", "of", "the", "new", "york", "san", "francisco", "supermarket"}
_PLACES = {"ny", "nj", "ca", "wa", "tx", "ma", "il"}
_ACRONYMS = {"cvs", "nyu", "mta", "amc", "atm", "h&m", "omny"}


def _word(w):
    low = w.lower()
    return low.upper() if low in _ACRONYMS else low[:1].upper() + low[1:]


KEYWORDS = {
    "Income": ["payroll", "direct dep", "salary", "stipend"],
    "Rent & Utilities": ["rent", "con ed", "coned", "national grid", "verizon", "spectrum", "t-mobile", "electric"],
    "Groceries": ["trader joe", "whole foods", "wegmans", "key food", "c-town", "instacart", "aldi"],
    "Dining": ["starbucks", "chipotle", "sweetgreen", "doordash", "uber eats", "grubhub", "cafe", "coffee", "pizza", "dunkin"],
    "Transport": ["mta", "omny", "uber", "lyft", "citi bike", "amtrak", "nj transit", "shell", "exxon"],
    "Shopping": ["amazon", "amzn", "target", "uniqlo", "h&m", "ikea", "best buy"],
    "Subscriptions": ["netflix", "spotify", "hulu", "icloud", "apple.com/bill", "youtube premium", "chatgpt", "notion"],
    "Health": ["cvs", "walgreens", "pharmacy", "dental", "medical", "planet fitness", "equinox"],
    "Travel": ["airbnb", "delta", "united", "jetblue", "marriott", "hilton", "expedia"],
    "Entertainment": ["amc", "ticketmaster", "seatgeek", "steam", "regal"],
    "Transfers": ["zelle", "venmo", "transfer"],
    "Fees": ["fee", "interest charge", "overdraft"],
}


def clean_merchant(description):
    """Turn a bank descriptor like 'SQ *BLUE BOTTLE COFFEE 8823 NY' into 'Blue Bottle Coffee'."""
    text = _PREFIX.sub("", description.strip())
    text = re.split(r"\s+-\s+", text)[0]  # 'RENT PAYMENT - 512 W 112TH ST' -> 'RENT PAYMENT'
    if "*" in text:  # 'DOORDASH*CHIPOTLE', 'UBER *TRIP' -> keep the brand before the star
        before, after = text.split("*", 1)
        text = before if len(before.strip()) >= 2 else after
    text = re.sub(r"\.com\b.*$", "", text, flags=re.I)  # 'NETFLIX.COM 866...' -> 'NETFLIX'
    words = []
    for w in re.split(r"[\s/]+", text):
        bare = w.strip("#,.").lower()
        if not bare or any(ch.isdigit() for ch in bare) or bare in _DROP_WORDS:
            continue
        words.append(w.strip("#,."))
    while words and words[-1].lower() in _PLACES:
        words.pop()
    name = " ".join(_word(w) for w in words[:4])
    return name or description.strip().title()


def by_keyword(text):
    low = text.lower()
    for category, words in KEYWORDS.items():
        if any(re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low) for w in words):
            return category
    return None


def validate_llm_category(raw):
    """Accept a model's answer only if it names exactly one of our categories."""
    if not raw:
        return None
    answer = raw.strip().strip(".\"'").lower()
    for c in CATEGORIES:
        if answer == c.lower():
            return c
    return None


def llm_categorizer():
    """Returns a function description -> raw model answer, or None when no API key is set.
    Works with OpenAI or any OpenAI-compatible endpoint, such as NVIDIA NIM (set LLM_BASE_URL)."""
    key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    from openai import OpenAI

    client = OpenAI(api_key=key, base_url=os.environ.get("LLM_BASE_URL") or None)
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    allowed = ", ".join(CATEGORIES)

    def ask(description, amount):
        msg = (f"Categorize this bank transaction. Answer with exactly one of: {allowed}.\n"
               f"Description: {description}\nAmount: {amount}")
        resp = client.chat.completions.create(model=model, temperature=0,
                                              messages=[{"role": "user", "content": msg}])
        return resp.choices[0].message.content

    return ask


def categorize(description, amount, learned_rules, ask_llm=None):
    """Returns (merchant, category, source)."""
    merchant = clean_merchant(description)
    if merchant.lower() in learned_rules:
        return merchant, learned_rules[merchant.lower()], "user"
    if amount > 0 and by_keyword(description) in (None, "Income"):
        return merchant, "Income", "rule"
    hit = by_keyword(description)
    if hit:
        return merchant, hit, "rule"
    if ask_llm:
        try:
            category = validate_llm_category(ask_llm(description, amount))
        except Exception:
            category = None
        if category:
            return merchant, category, "ai"
    return merchant, "Uncategorized", "none"
