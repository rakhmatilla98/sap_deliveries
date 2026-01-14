# shared/render_delivery_image.py
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

    # temporary image for measurement only
    tmp_img = Image.new("RGB", (width, 100), "white")
    tmp_draw = ImageDraw.Draw(tmp_img)

    table_height = calculate_table_height(
        tmp_draw,
        items,
        font_normal,
        row_height,
        desc_x=260,
        desc_right=600
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
    columns = [40, 100, 260, 600, 700, 820, 920]
    headers = ["#", "Item Code", "Description", "Qty", "Price", "Line Total", ""]

    for x, h in zip(columns, headers):
        draw.text((x, y), h, font=font_bold, fill="black")

    y += row_height
    draw.line((40, y, width - 40, y), fill="black", width=2)

    # ─── TABLE ROWS ───────────────────────
    QTY_RIGHT = 700
    PRICE_RIGHT = 820
    TOTAL_RIGHT = 920

    for i, item in enumerate(items, 1):
        start_y = y

        # --- Description wrapping ---
        desc_x = 260
        desc_width = 600 - desc_x
        desc_lines = wrap_text(
            draw,
            item.get("item_name", "-"),
            font_normal,
            desc_width
        )

        line_height = font_normal.getbbox("Ag")[3] + 4
        row_h = max(row_height, len(desc_lines) * line_height)

        # --- Static columns ---
        draw.text((40, start_y + 8), str(i), font=font_normal, fill="black")
        draw.text((100, start_y + 8), str(item.get("item_code", "-")), font=font_normal, fill="black")
        qty_text = str(item.get("quantity", 0))
        qty_bbox = draw.textbbox((0, 0), qty_text, font=font_normal)
        draw.text(
            (QTY_RIGHT - (qty_bbox[2] - qty_bbox[0]), start_y + 8),
            qty_text,
            font=font_normal,
            fill="black"
        )

        # --- Description multiline ---
        for idx, line in enumerate(desc_lines):
            draw.text(
                (desc_x, start_y + 8 + idx * 26),
                line,
                font=font_normal,
                fill="black"
            )

        # --- Price ---
        price = float(item.get("price", 0))
        price_text = f"{price:,.2f}"
        price_bbox = draw.textbbox((0, 0), price_text, font=font_normal)
        draw.text(
            (PRICE_RIGHT - (price_bbox[2] - price_bbox[0]), start_y + 8),
            price_text,
            font=font_normal,
            fill="black"
        )

        # --- Line total ---
        line_total = float(item.get("line_total", 0))
        total_text = f"{line_total:,.2f}"
        total_bbox = draw.textbbox((0, 0), total_text, font=font_normal)
        draw.text(
            (TOTAL_RIGHT - (total_bbox[2] - total_bbox[0]), start_y + 8),
            total_text,
            font=font_normal,
            fill="black"
        )

        y += row_h
        draw.line((40, y, width - 40, y), fill="#dddddd", width=1)

    # ─── FOOTER ───────────────────────────
    y += 40
    total_text = f"Total amount: {delivery.get('total_amount', 0):,.2f} {delivery.get('currency', 'UZS')}"
    bbox = draw.textbbox((0, 0), total_text, font=font_bold)
    draw.text((width - 40 - (bbox[2] - bbox[0]), y), total_text, font=font_bold, fill="black")

    y += 50
    draw.text((40, y), f"Remarks: {delivery.get('remarks') or '-'}", font=font_small, fill="black")

    doc_num = delivery.get("document_number", "unknown")
    path = os.path.join(images_dir, f"delivery_{doc_num}.png")

    final_height = max(y + 40, header_height + footer_height)
    img = img.crop((0, 0, width, final_height))

    img.save(path, quality=95)

    return path


def wrap_text(draw, text, font, max_width):
    """
    Splits text into multiple lines so that each line
    fits within max_width.
    """
    words = str(text).split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)

        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
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
        row_h = max(row_height, len(lines) * line_height)
        total += row_h

    return total
