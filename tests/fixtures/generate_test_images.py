import os
from PIL import Image, ImageDraw

upload_dir = r"C:\Users\Tanmay Kishore\Chemical-Tor\tests\fixtures\uploads"
os.makedirs(upload_dir, exist_ok=True)

images = [
    ("pfd_reaction_scheme.png", "Process Flow Diagram & Reaction Scheme", "Synthetic Route: Raw Materials -> Reaction -> Separation -> Distillation -> ZLD"),
    ("master_layout_plan.png", "Master Plant Site Layout Plan", "Plot Area: 40,468 sqm | Greenbelt: 33.1% | Production, Utilities, ETP/ZLD, Tank Farm"),
    ("topographical_10km_map.png", "Topographical Study Area Map (10 km Radius)", "Survey of India Toposheet | Siting Buffer & Environmental Sensitivity"),
    ("satellite_location_map.png", "Google Earth Satellite Location Map", "Site Coordinates: 17 deg 31 min N, 78 deg 10 min E | Immediate Road Access"),
    ("proponent_letterhead_undertaking.png", "Proponent Undertaking on Letterhead", "Signed & Notarized Statutory Undertaking | Form 1 & ToR Compliance"),
    ("land_allotment_deed.png", "Industrial Land Allotment Order & Possession Deed", "State Industrial Development Corporation (TSIIC) Allotment Order")
]

for filename, title, subtitle in images:
    filepath = os.path.join(upload_dir, filename)
    img = Image.new("RGB", (1600, 900), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)
    
    # Outer border
    draw.rectangle([20, 20, 1580, 880], outline=(31, 56, 100), width=4)
    # Header bar
    draw.rectangle([24, 24, 1576, 120], fill=(31, 56, 100))
    
    # Text
    draw.text((60, 50), title, fill=(255, 255, 255))
    draw.text((60, 200), subtitle, fill=(50, 50, 50))
    draw.text((60, 450), f"[Technical Drawing Asset: {filename}]", fill=(100, 100, 100))
    draw.text((60, 500), "Scale: 1:1000 | Verified for Terms of Reference Presentation (Sector 5f)", fill=(120, 120, 120))
    
    img.save(filepath)
    print(f"Generated: {filepath}")

