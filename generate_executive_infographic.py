import os
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions
WIDTH = 1600
HEIGHT = 2100

img = Image.new("RGB", (WIDTH, HEIGHT), "#0F172A") # Modern Slate 900 background
draw = ImageDraw.Draw(img)

# Helper for loading fonts
def get_font(name, size):
    try:
        return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
    except Exception:
        return ImageFont.load_default()

font_title   = get_font("segoeuib.ttf", 44)
font_subtitle= get_font("segoeui.ttf", 22)
font_sec_hdr = get_font("segoeuib.ttf", 28)
font_card_hdr= get_font("segoeuib.ttf", 22)
font_bold    = get_font("segoeuib.ttf", 18)
font_body    = get_font("segoeui.ttf", 17)
font_mono    = get_font("consola.ttf", 16)
font_small   = get_font("segoeui.ttf", 15)

# Color Palette
DARK_BG   = "#0F172A" # Slate 900
CARD_BG   = "#1E293B" # Slate 800
CARD_BORDER = "#334155" # Slate 700
WHITE     = "#FFFFFF"
TEXT_MUTED= "#94A3B8" # Slate 400
GREEN_BG  = "#064E3B"
GREEN_TXT = "#34D399"
GREEN_BORDER = "#059669"
AMBER_BG  = "#451A03"
AMBER_TXT = "#FBBF24"
AMBER_BORDER = "#D97706"
BLUE_BG   = "#1E3A8A"
BLUE_TXT  = "#60A5FA"
BLUE_BORDER = "#3B82F6"
PURPLE_BG = "#3B0764"
PURPLE_TXT= "#C084FC"

# Helper for drawing rounded cards
def draw_card(xy, fill=CARD_BG, outline=CARD_BORDER, radius=16, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

# Helper for drawing badges
def draw_badge(x, y, text, bg, fg, font=font_small):
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0] + 20
    h = bbox[3] - bbox[1] + 10
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=bg)
    draw.text((x + 10, y + 4), text, font=font, fill=fg)
    return w

# ─────────────────────────────────────────────────────────────
# 1. HEADER SECTION
# ─────────────────────────────────────────────────────────────
draw.rectangle([(0, 0), (WIDTH, 170)], fill="#0B132B")
draw.line([(0, 170), (WIDTH, 170)], fill="#1E293B", width=3)

# Top Bar Accent
draw.rectangle([(0, 0), (WIDTH, 8)], fill="#3B82F6")

draw.text((60, 30), "CFF BALANCING MACHINE AUTOMATION & QR SYSTEM", font=font_title, fill=WHITE)
draw.text((60, 90), "Executive Technical Investigation & Architecture Status Report | MIDC Supa Plant", font=font_subtitle, fill="#38BDF8")

# Meta Info Chips
cx = 60
cx += draw_badge(cx, 125, "MACHINE: Shanghai Jianping PHGS-5D (S/N 26010050)", "#1E293B", "#94A3B8") + 15
cx += draw_badge(cx, 125, "CONTROLLER: Kunlun Tongtai MCGS Linux", "#1E293B", "#94A3B8") + 15
cx += draw_badge(cx, 125, "PRINTER: Zebra ZD421 (22.4 x 15mm)", "#1E293B", "#34D399")

# ─────────────────────────────────────────────────────────────
# 2. STATUS OVERVIEW (3 KPI METRIC CARDS)
# ─────────────────────────────────────────────────────────────
kpi_y = 195
kpi_w = 460
kpi_h = 130

# KPI 1: Software & Printing Engine
draw_card([(60, kpi_y), (60 + kpi_w, kpi_y + kpi_h)], fill="#064E3B", outline=GREEN_BORDER)
draw.text((85, kpi_y + 18), "SOFTWARE & PRINTER PIPELINE", font=font_small, fill="#A7F3D0")
draw.text((85, kpi_y + 42), "100% READY & TESTED", font=font_card_hdr, fill="#34D399")
draw.text((85, kpi_y + 78), "- Zebra ZD421 direct 300 DPI ZPL streaming\n- SQLite DB normalized, Latest record at Top (Row #1)", font=font_small, fill="#D1FAE5")

# KPI 2: Physical Network Link
draw_card([(570, kpi_y), (570 + kpi_w, kpi_y + kpi_h)], fill="#1E3A8A", outline=BLUE_BORDER)
draw.text((595, kpi_y + 18), "PHYSICAL ETHERNET LINK", font=font_small, fill="#BFDBFE")
draw.text((595, kpi_y + 42), "100% CONNECTED & VERIFIED", font=font_card_hdr, fill="#60A5FA")
draw.text((595, kpi_y + 78), f"- IP: 192.168.0.2 (SWITCH LAN1/LAN2)\n- Hardware MAC: 0C:75:12:2E:EA:2E (Layer-2 Live)", font=font_small, fill="#DBEAFE")

# KPI 3: Live Data Streaming Bottleneck
draw_card([(1080, kpi_y), (1080 + kpi_w, kpi_y + kpi_h)], fill="#451A03", outline=AMBER_BORDER)
draw.text((1105, kpi_y + 18), "AUTOMATIC LAN EXTRACTION", font=font_small, fill="#FDE68A")
draw.text((1105, kpi_y + 42), "BLOCKED BY FIRMWARE", font=font_card_hdr, fill="#FBBF24")
draw.text((1105, kpi_y + 78), "- Machine firmware lacks native LAN push daemon\n- FTP sandboxed (/var/ftp/ empty), SSH root locked", font=font_small, fill="#FEF3C7")

# ─────────────────────────────────────────────────────────────
# 3. SECTION 1: WHAT IS 100% COMPLETED (DETAILED)
# ─────────────────────────────────────────────────────────────
sec1_y = 350
draw.text((60, sec1_y), "1. Work Accomplished & Production-Ready Modules", font=font_sec_hdr, fill=WHITE)
draw.line([(60, sec1_y + 40), (1540, sec1_y + 40)], fill=CARD_BORDER, width=2)

s1_box_y = sec1_y + 55
s1_box_h = 320
draw_card([(60, s1_box_y), (1540, s1_box_y + s1_box_h)])

achievements = [
    ("Instant ZPL Direct Printing Engine", 
     "Configured Zebra ZD421-300dpi printer for exact 22.4mm x 15.0mm (265x177 dots) label stock. Generates chunkier bold QR Code Version 1 + readable condensed serial. Silent print in <0.3s without Windows print dialogs."),
    ("Database Standardized & Chronological UI Sorting", 
     "Converted all 604 historical balancing records to standard ISO timestamps (YYYY-MM-DD HH:MM:SS). Updated SQLite sorting query (ORDER BY test_timestamp DESC) so the newest balanced fan ALWAYS displays at Row #1 (Top)."),
    ("One-Click Production Launcher Deployed", 
     "Created '1_START_CFF_AUTO_APP.bat' on desktop. Runs continuous background watcher on all USB ports (D: to Z:) and local drop folders for zero-touch file parsing, QR generation, and sticker printing."),
    ("Forensic Resolution of Nov 14 Mystery", 
     "Audited records #7-#10 (Tests 11577-11580). Confirmed they originated from drop folder test files dropped during pipeline verification on Nov 14, proving the physical machine never had LAN auto-streaming enabled out of the factory.")
]

ay = s1_box_y + 20
for title, desc in achievements:
    draw.ellipse([(85, ay + 6), (97, ay + 18)], fill="#10B981")
    draw.text((110, ay), title, font=font_bold, fill="#34D399")
    draw.text((110, ay + 26), desc, font=font_body, fill=TEXT_MUTED)
    ay += 72

# ─────────────────────────────────────────────────────────────
# 4. SECTION 2: THE CORE TECHNICAL BOTTLENECK (THE PROBLEM)
# ─────────────────────────────────────────────────────────────
sec2_y = 750
draw.text((60, sec2_y), "2. The Exact Technical Bottleneck (Why LAN Doesn't Stream)", font=font_sec_hdr, fill="#F87171")
draw.line([(60, sec2_y + 40), (1540, sec2_y + 40)], fill=CARD_BORDER, width=2)

s2_box_y = sec2_y + 55
s2_box_h = 420
draw_card([(60, s2_box_y), (1540, s2_box_y + s2_box_h)], fill="#18181B", outline="#7F1D1D")

# Diagram Box inside Problem
diag_x = 90
diag_y = s2_box_y + 25
draw_card([(diag_x, diag_y), (1510, diag_y + 110)], fill="#09090B", outline="#27272A")

draw.text((diag_x + 30, diag_y + 18), "PHYSICAL CABLE LINK", font=font_bold, fill="#38BDF8")
draw.text((diag_x + 30, diag_y + 45), "PC (192.168.0.100) <========== LAN CABLE ==========> CFF Machine (192.168.0.2)", font=font_mono, fill="#E2E8F0")
draw.text((diag_x + 30, diag_y + 72), "[STATUS: 100% CONNECTED & TALKING (MAC: 0C:75:12:2E:EA:2E) - Wire is completely healthy]", font=font_mono, fill="#4ADE80")

# Explanation points
py = diag_y + 130
problems = [
    ("Firmware Architecture Limitation:", 
     "Shanghai Jianping software (MicroDoubleplane) is built to commit balancing test data directly to internal NAND Flash memory (/mcgs/data/). The firmware has NO native background service to broadcast or push records over Ethernet upon test completion."),
    ("FTP Server is Sandboxed (Chroot Jail):", 
     "Port 21 (vsFTPd 3.0.3) allows anonymous login, but Linux security locks it inside an empty dummy folder (/var/ftp/ with 0 files). It cannot access the actual balancing database located inside /mcgs/data/."),
    ("Factory Encrypted Root Password:", 
     "Port 22 (SSH) is active and running OpenSSH 7.6, but requires the Linux 'root' master password set by the Chinese manufacturer. Without this password, we cannot reconfigure /etc/vsftpd.conf to unjail the data directory."),
    ("Closed Standard Protocols:", 
     "Port 80 (HTTP Web API) = CLOSED (Refused), Port 502 (Modbus TCP) = CLOSED, Port 445 (Windows SMB Share) = CLOSED. Zero network data ports are exposed out-of-the-box.")
]

for title, desc in problems:
    draw.ellipse([(90, py + 6), (102, py + 18)], fill="#EF4444")
    draw.text((115, py), title, font=font_bold, fill="#FCA5A5")
    draw.text((115, py + 26), desc, font=font_body, fill="#CBD5E1")
    py += 68

# ─────────────────────────────────────────────────────────────
# 5. SECTION 3: THE TWO ROADS FORWARD FOR MANAGEMENT DECISION
# ─────────────────────────────────────────────────────────────
sec3_y = 1250
draw.text((60, sec3_y), "3. Strategic Roadmap for Management Decision", font=font_sec_hdr, fill=WHITE)
draw.line([(60, sec3_y + 40), (1540, sec3_y + 40)], fill=CARD_BORDER, width=2)

col_w = 460
col_h = 480
y_col = sec3_y + 55

# Option A: Vendor Collaboration
draw_card([(60, y_col), (60 + col_w, y_col + col_h)], fill="#0F172A", outline="#0284C7")
draw.rectangle([(60, y_col), (60 + col_w, y_col + 50)], fill="#0369A1")
draw.text((80, y_col + 14), "OPTION A: Vendor Credentials", font=font_card_hdr, fill=WHITE)

draw.text((80, y_col + 70), "DIRECT LAN STREAMING (Rs 0)", font=font_bold, fill="#38BDF8")
draw.text((80, y_col + 105), 
          "We sent a formal technical inquiry\nto Shanghai Jianping requesting:\n"
          "1. SSH root password (Port 22)\n"
          "2. Authorized FTP login credentials\n"
          "3. TPC touchscreen engineer password\n\n"
          "HOW IT WORKS:\n"
          "Once password is provided, we SSH into\n"
          "machine in 5 mins, un-sandbox FTP or\n"
          "install a 5-line daemon that pushes\n"
          "records over the existing LAN cable.\n\n"
          "PROS: Zero extra hardware cost.\n"
          "RISK: Depends on vendor willingness\n"
          "to share factory passwords.", 
          font=font_body, fill="#E2E8F0")

# Option B: Autonomous Hardware Bridge
draw_card([(540, y_col), (540 + col_w, y_col + col_h)], fill="#0F172A", outline="#10B981")
draw.rectangle([(540, y_col), (540 + col_w, y_col + 50)], fill="#059669")
draw.text((560, y_col + 14), "OPTION B: Smart Hardware Bridge", font=font_card_hdr, fill=WHITE)

draw.text((560, y_col + 70), "RASPBERRY PI ZERO 2W (~Rs 2,500)", font=font_bold, fill="#34D399")
draw.text((560, y_col + 105), 
          "Automotive & MES Industry Standard\nfor closed legacy industrial machines.\n\n"
          "HOW IT WORKS:\n"
          "- Pi Zero 2W plugged into machine USB.\n"
          "- Appears to machine as FAT32 U-Disk.\n"
          "- Internal daemon detects new test CSV\n"
          "  in <100ms via Linux kernel inotify.\n"
          "- Instantly pushes record via Wi-Fi/LAN\n"
          "  to laptop; Zebra prints sticker.\n\n"
          "PROS: 100% Zero-Touch, Zero vendor\n"
          "dependency, 24/7 reliability.\n"
          "SCRIPTS: Already coded in repo!", 
          font=font_body, fill="#E2E8F0")

# Option C: Immediate Factory Operation
draw_card([(1020, y_col), (1020 + col_w, y_col + col_h)], fill="#0F172A", outline="#F59E0B")
draw.rectangle([(1020, y_col), (1020 + col_w, y_col + 50)], fill="#D97706")
draw.text((1040, y_col + 14), "OPTION C: Immediate Operation", font=font_card_hdr, fill=WHITE)

draw.text((1040, y_col + 70), "READY TO USE TODAY (Rs 0)", font=font_bold, fill="#FBBF24")
draw.text((1040, y_col + 105), 
          "While Option A or B is implemented,\nfactory production runs smoothly now.\n\n"
          "WORKFLOW:\n"
          "1. Operator balances fan on CFF.\n"
          "2. Taps 'Export' to USB pendrive.\n"
          "3. Plugs pendrive into laptop.\n"
          "4. 1_START_CFF_AUTO_APP detects it\n"
          "   in 1 sec, shows record at Top Row #1,\n"
          "   and silently prints QR sticker.\n\n"
          "PROS: 100% operational right now,\n"
          "no downtime on the production line.\n"
          "CONS: Requires physical pendrive swap.", 
          font=font_body, fill="#E2E8F0")

# ─────────────────────────────────────────────────────────────
# 6. FOOTER
# ─────────────────────────────────────────────────────────────
foot_y = 1970
draw.rectangle([(0, foot_y), (WIDTH, HEIGHT)], fill="#0B132B")
draw.line([(0, foot_y), (WIDTH, foot_y)], fill="#1E293B", width=2)

draw.text((60, foot_y + 35), "SUMMARY RECOMMENDATION FOR MANAGEMENT:", font=font_bold, fill=WHITE)
draw.text((60, foot_y + 65), "Proceed with Option C immediately on the floor. Await vendor password reply (Option A). If vendor delays or declines, deploy Option B (Pi Zero 2W, Rs 2,500) for 100% zero-touch automated production.", font=font_body, fill="#38BDF8")

# Save file
out_path_desktop = r"c:\Users\alokp\Desktop\CFF\CFF_Automation_Executive_Summary.png"
out_path_brain = r"C:\Users\alokp\.gemini\antigravity\brain\9f2bc130-9cc6-4426-b94f-d2e7b0f05be1\CFF_Automation_Executive_Summary.png"

img.save(out_path_desktop, "PNG", quality=95)
img.save(out_path_brain, "PNG", quality=95)
print("Infographic image successfully generated at:")
print("1.", out_path_desktop)
print("2.", out_path_brain)
