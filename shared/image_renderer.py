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

    items = delivery.get("items", [])
    table_height = (len(items) + 1) * row_height
    height = header_height + table_height + footer_height

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    font_title = get_font(42)
    font_header = get_font(28, bold=True)
    font_normal = get_font(24)
    font_bold = get_font(26, bold=True)
    font_small = get_font(20)

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
    columns = [40, 100, 260, 620, 780, 900]
    headers = ["#", "Item Code", "Description", "Qty", "Line Total", ""]

    for x, h in zip(columns, headers):
        draw.text((x, y), h, font=font_bold, fill="black")

    y += row_height
    draw.line((40, y, width - 40, y), fill="black", width=2)

    # ─── TABLE ROWS ───────────────────────
    for i, item in enumerate(items, 1):
        draw.text((40, y + 8), str(i), font=font_normal, fill="black")
        draw.text((100, y + 8), str(item.get("item_code", "-")), font=font_normal, fill="black")
        draw.text((260, y + 8), str(item.get("item_name", "-")), font=font_normal, fill="black")
        draw.text((620, y + 8), str(item.get("quantity", 0)), font=font_normal, fill="black")

        line_total = item.get("line_total", item.get("line_total ", 0))
        total_text = f"{float(line_total):,.2f}"

        bbox = draw.textbbox((0, 0), total_text, font=font_normal)
        draw.text((880 - (bbox[2] - bbox[0]), y + 8), total_text, font=font_normal, fill="black")

        y += row_height
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
    img.save(path, quality=95)

    return path
