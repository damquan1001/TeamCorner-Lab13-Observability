from app.pii import scrub_text, summarize_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_vietnamese_phone() -> None:
    out = scrub_text("Call me at 0987654321")
    assert "0987654321" not in out
    assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd() -> None:
    out = scrub_text("My CCCD is 012345678901")
    assert "012345678901" not in out
    assert "REDACTED_CCCD" in out


def test_scrub_credit_card() -> None:
    out = scrub_text("Card 4111 1111 1111 1111")
    assert "4111" not in out
    assert "REDACTED_CREDIT_CARD" in out


def test_scrub_passport_like_id() -> None:
    out = scrub_text("Passport P1234567 should not be logged")
    assert "P1234567" not in out
    assert "REDACTED_PASSPORT" in out


def test_scrub_vietnamese_address_keywords() -> None:
    out = scrub_text("dia chi: 123 Nguyen Trai, Quan 1")
    assert "123 Nguyen Trai" not in out
    assert "REDACTED_ADDRESS" in out


def test_summarize_text_does_not_leak_pii() -> None:
    out = summarize_text("Email student@vinuni.edu.vn and card 4111 1111 1111 1111")
    assert "student@" not in out
    assert "4111" not in out
