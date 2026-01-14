from PIL import Image, ImageDraw, ImageFont
import os
from shared.config import DATA_DIR

FONTS_DIR = os.path.join(DATA_DIR, "fonts")
FONT_REGULAR = os.path.join(FONTS_DIR, "arial.ttf")
FONT_BOLD = os.path.join(FONTS_DIR, "G_ari_bd.ttf")


def get_font(size: int, bold: bool = False):
    try:
        font_path = FONT_BOLD if bold else FONT_REGULAR
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"⚠ Font fallback used ({e})")
        return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    words = str(text).split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if draw.textbbox((0, 0), test_line, font=font)[2] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def calculate_table_height(draw, items, font, row_height, desc_x, desc_right):
    total = 0
    line_height = font.getbbox("Ag")[3] + 4
    desc_width = desc_right - desc_x

    for item in items:
        lines = wrap_text(draw, item.get("item_name", "-"), font, desc_width)
        total += max(row_height, len(lines) * line_height)

    return total


def render_delivery_image(delivery: dict) -> str:
    images_dir = os.path.join(DATA_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)

    width = 1000
    row_height = 45
    header_height = 280
    footer_height = 140

    font_title = get_font(42)
    font_header = get_font(28, bold=True)
    font_normal = get_font(24)
    font_bold = get_font(26, bold=True)
    font_small = get_font(20)

    items = delivery.get("items", [])

    # ─── PASS 1: CALCULATE HEIGHT ─────────
    tmp_img = Image.new("RGB", (width, 100), "white")
    tmp_draw = ImageDraw.Draw(tmp_img)

    table_height = calculate_table_height(
        tmp_draw, items, font_normal, row_height, 260, 600
    )

    height = header_height + row_height + table_height + footer_height
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # ─── HEADER ───────────────────────────
    y = 30
    draw.text((40, y), "DELIVERY NOTE", font=font_title, fill="black")
    y += 70

    draw.text((40, y), f"No: {delivery.get('document_number', '-')}", font=font_header, fill="black")
    draw.text((620, y), f"Date: {delivery.get('date', '-')[:10]}", font=font_header, fill="black")
    y += 50

    draw.text((40, y), f"Customer: {delivery.get('card_name') or '-'}", font=font_normal, fill="black")
    y += 40
    draw.text((40, y), f"CardCode: {delivery.get('card_code', '-')}", font=font_normal, fill="black")
    y += 40
    draw.text((40, y), f"Sales Manager: {delivery.get('sales_manager', '-')}", font=font_normal, fill="black")
    y += 60

    # ─── TABLE HEADER ─────────────────────
    TABLE_LEFT = 40
    TABLE_RIGHT = width - 40

    COLS = {
        "idx": 40,
        "code": 100,
        "desc": 260,
        "qty": 600,
        "price": 700,
        "total": 820,
    }

    HEADERS = [
        ("#", COLS["idx"]),
        ("Item Code", COLS["code"]),
        ("Description", COLS["desc"]),
        ("Qty", COLS["qty"]),
        ("Price", COLS["price"]),
        ("Line Total", COLS["total"]),
    ]

    table_top = y

    for text, x in HEADERS:
        draw.text((x, y), text, font=font_bold, fill="black")

    y += row_height
    draw.line((TABLE_LEFT, y, TABLE_RIGHT, y), fill="black", width=2)

    # ─── TABLE ROWS ───────────────────────
    QTY_RIGHT = COLS["price"]
    PRICE_RIGHT = COLS["total"]
    TOTAL_RIGHT = TABLE_RIGHT

    for i, item in enumerate(items, 1):
        start_y = y

        desc_lines = wrap_text(
            draw, item.get("item_name", "-"), font_normal, COLS["qty"] - COLS["desc"]
        )

        line_height = font_normal.getbbox("Ag")[3] + 4
        row_h = max(row_height, len(desc_lines) * line_height)

        draw.text((COLS["idx"], start_y + 8), str(i), font=font_normal, fill="black")
        draw.text((COLS["code"], start_y + 8), str(item.get("item_code", "-")), font=font_normal, fill="black")

        for j, line in enumerate(desc_lines):
            draw.text((COLS["desc"], start_y + 8 + j * line_height), line, font=font_normal, fill="black")

        qty = str(item.get("quantity", 0))
        w = draw.textbbox((0, 0), qty, font=font_normal)[2]
        draw.text((QTY_RIGHT - w, start_y + 8), qty, font=font_normal, fill="black")

        price = f"{float(item.get('price', 0)):,.2f}"
        w = draw.textbbox((0, 0), price, font=font_normal)[2]
        draw.text((PRICE_RIGHT - w, start_y + 8), price, font=font_normal, fill="black")

        total = f"{float(item.get('line_total', 0)):,.2f}"
        w = draw.textbbox((0, 0), total, font=font_normal)[2]
        draw.text((TOTAL_RIGHT - w, start_y + 8), total, font=font_normal, fill="black")

        y += row_h
        draw.line((TABLE_LEFT, y, TABLE_RIGHT, y), fill="#cccccc", width=1)

    table_bottom = y

    # ─── VERTICAL GRID LINES ──────────────
    for x in [COLS["idx"], COLS["code"], COLS["desc"], COLS["qty"], COLS["price"], COLS["total"], TABLE_RIGHT]:
        draw.line((x, table_top, x, table_bottom), fill="#999999", width=1)

    # ─── FOOTER ───────────────────────────
    y += 40
    total_text = f"Total amount: {delivery.get('total_amount', 0):,.2f} {delivery.get('currency', 'UZS')}"
    w = draw.textbbox((0, 0), total_text, font=font_bold)[2]
    draw.text((TABLE_RIGHT - w, y), total_text, font=font_bold, fill="black")

    y += 50
    draw.text((40, y), f"Remarks: {delivery.get('remarks') or '-'}", font=font_small, fill="black")

    doc_num = delivery.get("document_number", "unknown")
    path = os.path.join(images_dir, f"delivery_{doc_num}.png")

    img.save(path, quality=95)
    return path
