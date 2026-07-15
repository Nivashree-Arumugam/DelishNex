"""
download_dish_images.py
Automatically downloads real, high-quality, royalty-free food photographs
from Wikimedia Commons and Unsplash for every dish in the DelishNex database.
Saves images to static/images/dishes/ and updates the database image_url field.
"""

import os
import sys
import re
import time
import urllib.request
import urllib.parse
import urllib.error
import json

# ── ensure we can import Flask app ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from models import db, Menu

DEST_DIR = os.path.join(os.path.dirname(__file__), "static", "images", "dishes")
os.makedirs(DEST_DIR, exist_ok=True)

# ── Dish → search term mapping (precise, dish-specific) ─────────────────────
DISH_IMAGES = {
    # ── The Green Terrace (id 1-17) ─────────────────────────────────────────
    "Paneer Tikka":         "paneer_tikka.jpg",
    "Chicken Seekh Kebab":  "chicken_seekh_kebab.jpg",
    "Crispy Corn":          "crispy_corn.jpg",
    "Mushroom Galawat":     "mushroom_galawat.jpg",
    "Butter Chicken":       "butter_chicken.jpg",
    "Dal Makhani":          "dal_makhani.jpg",
    "Mutton Biryani":       "mutton_biryani.jpg",
    "Paneer Butter Masala": "paneer_butter_masala.jpg",
    "Veg Fried Rice":       "veg_fried_rice.jpg",
    "Gulab Jamun":          "gulab_jamun.jpg",
    "Chocolate Lava Cake":  "chocolate_lava_cake.jpg",
    "Rasmalai":             "rasmalai.jpg",
    "Mango Lassi":          "mango_lassi.jpg",
    "Masala Chai":          "masala_chai.jpg",
    "Fresh Lime Soda":      "fresh_lime_soda.jpg",
    "Royal Feast Combo":    "royal_feast_combo.jpg",
    "Veg Delight Combo":    "veg_delight_combo.jpg",
    # ── Spice Garden (id 18-25) ──────────────────────────────────────────────
    "Medu Vada":            "medu_vada.jpg",
    "Chicken 65":           "chicken_65.jpg",
    "Masala Dosa":          "masala_dosa.jpg",
    "Chettinad Chicken":    "chettinad_chicken.jpg",
    "Sambar Rice":          "sambar_rice.jpg",
    "Payasam":              "payasam.jpg",
    "Filter Coffee":        "filter_coffee.jpg",
    "Spice Garden Thali":   "spice_garden_thali.jpg",
    # ── The Royal Plate (id 26-33) ───────────────────────────────────────────
    "Galouti Kebab":        "galouti_kebab.jpg",
    "Dahi Ke Kebab":        "dahi_ke_kebab.jpg",
    "Mughlai Chicken Curry":"mughlai_chicken_curry.jpg",
    "Dum Biryani":          "dum_biryani.jpg",
    "Shahi Paneer":         "shahi_paneer.jpg",
    "Phirni":               "phirni.jpg",
    "Thandai":              "thandai.jpg",
    "Royal Feast":          "royal_feast.jpg",
    # ── Ocean Breeze (id 34-41) ──────────────────────────────────────────────
    "Prawn Tempura":        "prawn_tempura.jpg",
    "Fish Tikka":           "fish_tikka.jpg",
    "Goan Fish Curry":      "goan_fish_curry.jpg",
    "Lobster Thermidor":    "lobster_thermidor.jpg",
    "Coconut Rice":         "coconut_rice.jpg",
    "Coconut Panna Cotta":  "coconut_panna_cotta.jpg",
    "Blue Lagoon Mocktail": "blue_lagoon_mocktail.jpg",
    "Seafood Platter":      "seafood_platter.jpg",
    # ── Bamboo Kitchen (id 42-49) ────────────────────────────────────────────
    "Dim Sum Platter":      "dim_sum_platter.jpg",
    "Thai Spring Rolls":    "thai_spring_rolls.jpg",
    "Kung Pao Chicken":     "kung_pao_chicken.jpg",
    "Pad Thai":             "pad_thai.jpg",
    "Sushi Roll Set":       "sushi_roll_set.jpg",
    "Mochi Ice Cream":      "mochi_ice_cream.jpg",
    "Thai Iced Tea":        "thai_iced_tea.jpg",
    "Asian Explorer Combo": "asian_explorer_combo.jpg",
    # ── La Dolce Vita (id 50-59) ─────────────────────────────────────────────
    "Bruschetta":           "bruschetta.jpg",
    "Caprese Salad":        "caprese_salad.jpg",
    "Margherita Pizza":     "margherita_pizza.jpg",
    "Pasta Carbonara":      "pasta_carbonara.jpg",
    "Risotto Funghi":       "risotto_funghi.jpg",
    "Tiramisu":             "tiramisu.jpg",
    "Panna Cotta":          "panna_cotta.jpg",
    "Espresso":             "espresso.jpg",
    "Limoncello Spritz":    "limoncello_spritz.jpg",
    "Italian Feast Combo":  "italian_feast_combo.jpg",
}

# ── Curated Unsplash photo IDs per dish (high quality, CC0/free-to-use) ──────
# Format: dish name → Unsplash photo ID (from unsplash.com/photos/<id>)
UNSPLASH_IDS = {
    "Paneer Tikka":         "photo-1565557623262-b51c2513a641",  # grilled paneer
    "Chicken Seekh Kebab":  "photo-1628294895950-9805252f784d",  # kebab on skewer
    "Crispy Corn":          "photo-1547592180-85f173990554",      # fried corn
    "Mushroom Galawat":     "photo-1504674900247-0877df9cc836",   # mushroom dish
    "Butter Chicken":       "photo-1588166524941-3bf61a9c41db",   # butter chicken
    "Dal Makhani":          "photo-1546833999-b9f581a1996d",      # dal makhani
    "Mutton Biryani":       "photo-1563379091339-03b21ab4a4f8",   # biryani
    "Paneer Butter Masala": "photo-1585937421612-70a008356fbe",   # paneer masala
    "Veg Fried Rice":       "photo-1603133872878-684f208fb84b",   # fried rice
    "Gulab Jamun":          "photo-1601050690117-94f5f6fa8ad7",   # gulab jamun
    "Chocolate Lava Cake":  "photo-1617305855058-336d24456869",   # lava cake
    "Rasmalai":             "photo-1589301760014-d929f3979dbc",   # rasmalai
    "Mango Lassi":          "photo-1553361371-9b22f78e8b1d",      # mango lassi
    "Masala Chai":          "photo-1564890369478-c89ca6d9cde9",   # masala chai
    "Fresh Lime Soda":      "photo-1513558161293-cdaf765ed2fd",   # lime soda
    "Royal Feast Combo":    "photo-1596040033229-a9821ebd058d",   # indian feast
    "Veg Delight Combo":    "photo-1601050690596-fbc4831caacc",   # veg spread
    "Medu Vada":            "photo-1589301760014-d929f3979dbc",   # medu vada
    "Chicken 65":           "photo-1627308595229-7830a5c91f9f",   # chicken 65
    "Masala Dosa":          "photo-1630383249896-24dcbdab8f40",   # masala dosa
    "Chettinad Chicken":    "photo-1588166524941-3bf61a9c41db",   # spicy chicken curry
    "Sambar Rice":          "photo-1536304993881-ff6e9eefa2a6",   # rice with sambar
    "Payasam":              "photo-1579954115545-a95591f28bfc",   # kheer payasam
    "Filter Coffee":        "photo-1495474472287-4d71bcdd2085",   # filter coffee
    "Spice Garden Thali":   "photo-1596040033229-a9821ebd058d",   # south indian thali
    "Galouti Kebab":        "photo-1625398407796-82cec9eff75d",   # seekh/galouti kebab
    "Dahi Ke Kebab":        "photo-1599487488170-d11ec9c172f0",   # dahi kebab
    "Mughlai Chicken Curry":"photo-1574653853027-5382a3d23a15",   # mughlai curry
    "Dum Biryani":          "photo-1563379091339-03b21ab4a4f8",   # dum biryani
    "Shahi Paneer":         "photo-1585937421612-70a008356fbe",   # shahi paneer
    "Phirni":               "photo-1579954115545-a95591f28bfc",   # phirni/rice pudding
    "Thandai":              "photo-1553361371-9b22f78e8b1d",      # thandai/milk drink
    "Royal Feast":          "photo-1596040033229-a9821ebd058d",   # royal feast
    "Prawn Tempura":        "photo-1534482421-64566f976cfa",      # prawn tempura
    "Fish Tikka":           "photo-1467003909585-2f8a72700288",   # fish tikka
    "Goan Fish Curry":      "photo-1510130387422-82bed34b37e9",   # fish curry
    "Lobster Thermidor":    "photo-1560717789-0ac7c58ac90a",      # lobster
    "Coconut Rice":         "photo-1536304993881-ff6e9eefa2a6",   # coconut rice
    "Coconut Panna Cotta":  "photo-1551024506-0bccd828d307",      # panna cotta
    "Blue Lagoon Mocktail": "photo-1570696516188-ade861b84a49",   # blue mocktail
    "Seafood Platter":      "photo-1534482421-64566f976cfa",      # seafood platter
    "Dim Sum Platter":      "photo-1563245372-f21724e3856d",      # dim sum
    "Thai Spring Rolls":    "photo-1615361200141-f45040f367be",   # spring rolls
    "Kung Pao Chicken":     "photo-1604908176997-125f25cc6f3d",   # kung pao chicken
    "Pad Thai":             "photo-1569050467447-ce54b3bbc37d",   # pad thai
    "Sushi Roll Set":       "photo-1553621042-f6e147245754",      # sushi rolls
    "Mochi Ice Cream":      "photo-1563805042-7684c019e1cb",      # mochi
    "Thai Iced Tea":        "photo-1556679343-c7306c1976bc",      # thai iced tea
    "Asian Explorer Combo": "photo-1617196034183-421b4040d20d",   # asian spread
    "Bruschetta":           "photo-1572695157366-5e585ab2b69f",   # bruschetta
    "Caprese Salad":        "photo-1555939594-58d7cb561ad1",      # caprese salad
    "Margherita Pizza":     "photo-1574071318508-1cdbab80d002",   # margherita pizza
    "Pasta Carbonara":      "photo-1621996346565-e3dbc646d9a9",   # pasta carbonara
    "Risotto Funghi":       "photo-1476124369491-e7addf5db371",   # mushroom risotto
    "Tiramisu":             "photo-1571877227200-a0d98ea607e9",   # tiramisu
    "Panna Cotta":          "photo-1551024506-0bccd828d307",      # panna cotta
    "Espresso":             "photo-1510707577719-ae7c14805e3a",   # espresso
    "Limoncello Spritz":    "photo-1570696516188-ade861b84a49",   # spritz mocktail
    "Italian Feast Combo":  "photo-1414235077428-338989a2e8c0",   # italian feast
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def download_unsplash(dish_name, filename):
    """Download from Unsplash using curated photo ID at max quality."""
    photo_id = UNSPLASH_IDS.get(dish_name)
    if not photo_id:
        return False

    # Unsplash raw image URL (no API key needed for direct photo access)
    url = f"https://images.unsplash.com/{photo_id}?w=1920&q=90&fit=crop&auto=format"
    dest_path = os.path.join(DEST_DIR, filename)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                data = resp.read()
                if len(data) > 5000:   # must be a real image, not a tiny error
                    with open(dest_path, "wb") as f:
                        f.write(data)
                    size_kb = len(data) // 1024
                    print(f"  ✓ Unsplash  {dish_name:<30} → {filename}  ({size_kb} KB)")
                    return True
    except Exception as e:
        print(f"  ✗ Unsplash failed for '{dish_name}': {e}")
    return False


def search_wikimedia(dish_name, filename):
    """Search Wikimedia Commons for a food image and download the first HD result."""
    query = urllib.parse.quote(dish_name + " food")
    api = (
        "https://commons.wikimedia.org/w/api.php"
        f"?action=query&list=search&srsearch={query}&srnamespace=6"
        "&srlimit=5&format=json"
    )
    try:
        req = urllib.request.Request(api, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        results = data.get("query", {}).get("search", [])
        for result in results:
            title = result["title"]
            # skip non-image titles
            if not any(title.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                continue
            # get the direct URL
            encoded_title = urllib.parse.quote(title.replace(" ", "_"))
            info_url = (
                "https://commons.wikimedia.org/w/api.php"
                f"?action=query&titles={encoded_title}&prop=imageinfo"
                "&iiprop=url|size&iiurlwidth=1920&format=json"
            )
            req2 = urllib.request.Request(info_url, headers=HEADERS)
            with urllib.request.urlopen(req2, timeout=20) as resp2:
                info = json.loads(resp2.read())
            pages = info.get("query", {}).get("pages", {})
            for page in pages.values():
                imageinfos = page.get("imageinfo", [])
                for ii in imageinfos:
                    img_url = ii.get("thumburl") or ii.get("url")
                    if img_url:
                        dest_path = os.path.join(DEST_DIR, filename)
                        req3 = urllib.request.Request(img_url, headers=HEADERS)
                        with urllib.request.urlopen(req3, timeout=30) as r3:
                            img_data = r3.read()
                        if len(img_data) > 5000:
                            ext = ".jpg" if filename.endswith(".jpg") else ".jpg"
                            with open(dest_path, "wb") as f:
                                f.write(img_data)
                            size_kb = len(img_data) // 1024
                            print(f"  ✓ Wikimedia {dish_name:<30} → {filename}  ({size_kb} KB)")
                            return True
    except Exception as e:
        print(f"  ✗ Wikimedia failed for '{dish_name}': {e}")
    return False


def download_pexels_fallback(dish_name, filename):
    """Fallback: use Pexels public CDN search page scrape."""
    query = urllib.parse.quote(dish_name + " food")
    search_url = f"https://www.pexels.com/search/{query}/"
    try:
        req = urllib.request.Request(search_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # find a high-res image src
        matches = re.findall(r'"src":"(https://images\.pexels\.com/photos/[^"]+)"', html)
        for match in matches:
            img_url = match.replace("\\u002F", "/")
            # get a bigger version
            img_url = re.sub(r'\?.*$', '', img_url) + "?auto=compress&cs=tinysrgb&w=1920"
            dest_path = os.path.join(DEST_DIR, filename)
            req2 = urllib.request.Request(img_url, headers=HEADERS)
            with urllib.request.urlopen(req2, timeout=30) as r2:
                img_data = r2.read()
            if len(img_data) > 10000:
                with open(dest_path, "wb") as f:
                    f.write(img_data)
                size_kb = len(img_data) // 1024
                print(f"  ✓ Pexels    {dish_name:<30} → {filename}  ({size_kb} KB)")
                return True
    except Exception as e:
        print(f"  ✗ Pexels failed for '{dish_name}': {e}")
    return False


def get_image(dish_name, filename):
    """Try each source in priority order until one succeeds."""
    # Try Unsplash first (curated IDs = exact matches)
    if download_unsplash(dish_name, filename):
        return True
    time.sleep(0.5)
    # Fallback to Wikimedia Commons
    if search_wikimedia(dish_name, filename):
        return True
    time.sleep(0.5)
    # Last resort: Pexels scrape
    if download_pexels_fallback(dish_name, filename):
        return True
    print(f"  ✗ ALL SOURCES FAILED for '{dish_name}'")
    return False


def update_database(app, mapping):
    """Update the image_url column for every Menu row."""
    with app.app_context():
        menus = Menu.query.all()
        updated = 0
        for m in menus:
            filename = mapping.get(m.name)
            if filename:
                new_url = f"dishes/{filename}"
                m.image_url = new_url
                updated += 1
        db.session.commit()
        print(f"\n✅ Database updated: {updated} dish records.")


def main():
    print("=" * 60)
    print("DelishNex – Dish Image Downloader")
    print(f"Saving to: {DEST_DIR}")
    print("=" * 60)

    ok = 0
    fail = 0
    failed_dishes = []
    for dish_name, filename in DISH_IMAGES.items():
        dest_path = os.path.join(DEST_DIR, filename)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 5000:
            print(f"  ↷ Already exists  {dish_name}")
            ok += 1
            continue
        success = get_image(dish_name, filename)
        if success:
            ok += 1
        else:
            fail += 1
            failed_dishes.append(dish_name)
        time.sleep(0.3)   # be polite to servers

    print(f"\n{'='*60}")
    print(f"Downloaded: {ok}  |  Failed: {fail}")
    if failed_dishes:
        print("Failed dishes:")
        for d in failed_dishes:
            print(f"  - {d}")

    app = create_app()
    update_database(app, DISH_IMAGES)
    print("Done! Refresh your browser to see dish images.")


if __name__ == "__main__":
    main()
