def normalize_phone(phone: str) -> str:
    return phone.replace(" ", "").replace("-", "").replace("+", "")


def find_bp_by_phone(phone: str):
    """
    Return:
      (card_code, card_name) or None
    """
    # TEMP MOCK
    demo = {
        "998901234567": ("C20000", "Demo Partner"),
    }

    phone = normalize_phone(phone)
    return demo.get(phone)
