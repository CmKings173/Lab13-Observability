"""Tests for PII scrubbing in app/pii.py"""
from app.pii import hash_user_id, scrub_text, summarize_text


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_email_preserves_surrounding_text() -> None:
    out = scrub_text("Contact: user@example.com, thanks")
    assert "Contact:" in out
    assert "thanks" in out
    assert "@" not in out


# ---------------------------------------------------------------------------
# Vietnamese phone
# ---------------------------------------------------------------------------

def test_scrub_phone_vn_local() -> None:
    out = scrub_text("Call me at 0987654321")
    assert "0987654321" not in out
    assert "REDACTED_PHONE_VN" in out


def test_scrub_phone_vn_plus84() -> None:
    out = scrub_text("Phone: +84 987 654 321")
    assert "+84" not in out
    assert "REDACTED_PHONE_VN" in out


def test_scrub_phone_vn_dotted() -> None:
    out = scrub_text("090.123.4567 is my number")
    assert "090.123.4567" not in out
    assert "REDACTED_PHONE_VN" in out


# ---------------------------------------------------------------------------
# CCCD (12 digits)
# ---------------------------------------------------------------------------

def test_scrub_cccd() -> None:
    out = scrub_text("My CCCD is 001234567890")
    assert "001234567890" not in out
    assert "REDACTED_CCCD" in out


# ---------------------------------------------------------------------------
# Credit card
# ---------------------------------------------------------------------------

def test_scrub_credit_card_spaces() -> None:
    out = scrub_text("Card: 4111 1111 1111 1111")
    assert "4111" not in out
    assert "REDACTED_CREDIT_CARD" in out


def test_scrub_credit_card_dashes() -> None:
    out = scrub_text("Pay with 4111-1111-1111-1111")
    assert "4111" not in out
    assert "REDACTED_CREDIT_CARD" in out


def test_scrub_credit_card_no_separator() -> None:
    out = scrub_text("Card number 4111111111111111")
    assert "4111111111111111" not in out
    assert "REDACTED_CREDIT_CARD" in out


# ---------------------------------------------------------------------------
# Passport
# ---------------------------------------------------------------------------

def test_scrub_passport() -> None:
    out = scrub_text("Passport B1234567 issued in Hanoi")
    assert "B1234567" not in out
    assert "REDACTED_PASSPORT" in out


def test_scrub_passport_8digit() -> None:
    out = scrub_text("My passport is B12345678")
    assert "B12345678" not in out
    assert "REDACTED_PASSPORT" in out


# ---------------------------------------------------------------------------
# No false positives on clean text
# ---------------------------------------------------------------------------

def test_no_redaction_clean_text() -> None:
    text = "The monitoring system is running fine."
    assert scrub_text(text) == text


# ---------------------------------------------------------------------------
# summarize_text
# ---------------------------------------------------------------------------

def test_summarize_truncates() -> None:
    long_text = "a" * 200
    result = summarize_text(long_text)
    assert result.endswith("...")
    assert len(result) <= 83  # 80 chars + "..."


def test_summarize_scrubs_pii() -> None:
    result = summarize_text("Send invoice to user@test.com please")
    assert "@" not in result
    assert "REDACTED_EMAIL" in result


def test_summarize_short_text_no_ellipsis() -> None:
    result = summarize_text("Hello world")
    assert not result.endswith("...")


# ---------------------------------------------------------------------------
# hash_user_id
# ---------------------------------------------------------------------------

def test_hash_user_id_length() -> None:
    h = hash_user_id("u_team_01")
    assert len(h) == 12


def test_hash_user_id_deterministic() -> None:
    assert hash_user_id("u_team_01") == hash_user_id("u_team_01")


def test_hash_user_id_different_inputs() -> None:
    assert hash_user_id("user_a") != hash_user_id("user_b")
