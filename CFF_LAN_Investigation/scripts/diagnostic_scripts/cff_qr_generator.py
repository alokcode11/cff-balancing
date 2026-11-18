import os
import json
import qrcode
from PIL import Image, ImageDraw, ImageFont

def generate_cff_sticker(
    rotor="122x992mm",
    timestamp="2026-11-07 20:08:25",
    machine="PHGS-5D (S/N: 26010050)",
    status="OK",
    plane1_amount="0.186 g",
    plane1_angle="104.0°",
    plane2_amount="0.070 g",
    plane2_angle="115.7°",
    test_run="7",
    out_dir=r"C:\Users\alokp\Desktop\CFF\CFF_LAN_Investigation\samples\raw_balancing_records"
):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Structured Industrial QR Payload
    unique_id = f"CFF-{timestamp.replace(' ', '-').replace(':', '')}-{status}"
    payload_data = {
        "id": unique_id,
        "machine": "PHGS-5D",
        "sn": "26010050",
        "part": rotor,
        "date": timestamp,
        "status": status,
        "plane1": {"amt_g": 0.186, "deg": 104.0},
        "plane2": {"amt_g": 0.070, "deg": 115.7},
        "run": test_run
    }
    payload_str = json.dumps(payload_data, separators=(',', ':'))
    
    # 2. Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(payload_str)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    
    # 3. Create Thermal Sticker Canvas (e.g. 600 x 320 px - standard 50x30mm or 60x40mm sticker)
    canvas_w = 600
    canvas_h = 320
    sticker = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(sticker)
    
    # Draw border
    draw.rectangle([(4, 4), (canvas_w - 5, canvas_h - 5)], outline="black", width=3)
    
    # Header bar
    draw.rectangle([(4, 4), (canvas_w - 5, 45)], fill="#1E3A8A") # Navy header
    
    # Try default or standard fonts
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 20)
        font_main = ImageFont.truetype("arialbd.ttf", 16)
        font_sm = ImageFont.truetype("arial.ttf", 14)
        font_lg = ImageFont.truetype("arialbd.ttf", 26)
    except:
        font_title = ImageFont.load_default()
        font_main = ImageFont.load_default()
        font_sm = ImageFont.load_default()
        font_lg = ImageFont.load_default()
        
    draw.text((15, 12), "CFF DYNAMIC BALANCING CERTIFICATE", fill="white", font=font_title)
    
    # Paste QR Code on the left
    qr_w, qr_h = qr_img.size
    qr_x = 15
    qr_y = 60
    sticker.paste(qr_img, (qr_x, qr_y))
    
    # Text details on the right
    col_x = 240
    curr_y = 60
    
    draw.text((col_x, curr_y), f"Part Model: {rotor}", fill="black", font=font_main)
    curr_y += 24
    draw.text((col_x, curr_y), f"Test Date: {timestamp}", fill="black", font=font_sm)
    curr_y += 20
    draw.text((col_x, curr_y), f"Machine: {machine}", fill="black", font=font_sm)
    curr_y += 26
    
    # Plane 1
    draw.text((col_x, curr_y), f"Plane 1 (Left):", fill="#1E3A8A", font=font_main)
    draw.text((col_x + 130, curr_y), f"{plane1_amount}  @  {plane1_angle}", fill="black", font=font_main)
    curr_y += 24
    
    # Plane 2
    draw.text((col_x, curr_y), f"Plane 2 (Right):", fill="#1E3A8A", font=font_main)
    draw.text((col_x + 130, curr_y), f"{plane2_amount}  @  {plane2_angle}", fill="black", font=font_main)
    curr_y += 32
    
    # Status Banner (Green OK Box)
    draw.rectangle([(col_x, curr_y), (col_x + 160, curr_y + 45)], fill="#16A34A") # Green
    draw.text((col_x + 35, curr_y + 8), f"STATUS: {status}", fill="white", font=font_main)
    
    # Unique ID label
    draw.text((col_x + 175, curr_y + 12), f"ID: #{test_run}", fill="#6B7280", font=font_sm)
    
    # Bottom sub-text
    draw.text((15, canvas_h - 25), f"Verification Payload: {unique_id}", fill="#4B5563", font=font_sm)
    
    out_path = os.path.join(out_dir, "cff_sample_qr_sticker.png")
    sticker.save(out_path)
    print(f"Sticker generated: {out_path}", flush=True)
    return out_path, payload_str

if __name__ == '__main__':
    p, payload = generate_cff_sticker()
    print("Payload:", payload)
