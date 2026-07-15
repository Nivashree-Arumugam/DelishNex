"""
fix_failed_dishes.py – Retry the 19 dishes that failed due to rate limiting.
Uses 3-second pauses between Wikimedia requests + Unsplash fallbacks.
"""

import os, sys, time, urllib.request, urllib.parse, json

DEST_DIR = os.path.join(os.path.dirname(__file__), "static", "images", "dishes")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Wikimedia Commons file titles (verified) ──────────────────────────────
WMC = {
    "Dal Makhani":       "File:Dal Makhani.jpg",
    "Mutton Biryani":    "File:Mutton Dum biryani.jpg",
    "Gulab Jamun":       "File:Two Gulab Jamun in a plate 01.jpg",
    "Chocolate Lava Cake":"File:Chocolate_lava_cake_cut_open.jpg",
    "Medu Vada":         "File:Medu_vada.jpg",
    "Masala Dosa":       "File:Masala Dosa.jpg",
    "Chettinad Chicken": "File:Chettinad chicken.jpg",
    "Sambar Rice":       "File:Sambar Rice.jpg",
    "Payasam":           "File:Payasam Kerala.jpg",
    "Spice Garden Thali":"File:Meals in south India.jpg",
    "Galouti Kebab":     "File:Mouth Watering Gauloti Kababs.jpg",
    "Dum Biryani":       "File:Mutton Dum biryani.jpg",
    "Shahi Paneer":      "File:Shahi Paneer.jpg",
    "Prawn Tempura":     "File:Prawn tempura.jpg",
    "Goan Fish Curry":   "File:Goan fish curry.jpg",
    "Sushi Roll Set":    "File:Various sushi.jpg",
    "Caprese Salad":     "File:Caprese salad (Capreses).jpg",
    "Risotto Funghi":    "File:Risotto funghi.jpg",
    "Panna Cotta":       "File:Panna cotta with caramel.jpg",
}

# ── Unsplash photo IDs as fallback for each ──────────────────────────────────
UNSPLASH = {
    "Dal Makhani":        "photo-1546833999-b9f581a1996d",
    "Mutton Biryani":     "photo-1563379091339-03b21ab4a4f8",
    "Gulab Jamun":        "photo-1605197161470-5d0ab148cddb",
    "Chocolate Lava Cake":"photo-1578985545062-69928b1d9587",
    "Medu Vada":          "photo-1630383249896-24dcbdab8f40",
    "Masala Dosa":        "photo-1589301760014-d929f3979dbc",
    "Chettinad Chicken":  "photo-1574653853027-5382a3d23a15",
    "Sambar Rice":        "photo-1536304993881-ff6e9eefa2a6",
    "Payasam":            "photo-1579954115545-a95591f28bfc",
    "Spice Garden Thali": "photo-1596040033229-a9821ebd058d",
    "Galouti Kebab":      "photo-1565299624946-b28f40a0ae38",
    "Dum Biryani":        "photo-1563379091339-03b21ab4a4f8",
    "Shahi Paneer":       "photo-1585937421612-70a008356fbe",
    "Prawn Tempura":      "photo-1562802378-063ec186a863",
    "Goan Fish Curry":    "photo-1510130387422-82bed34b37e9",
    "Sushi Roll Set":     "photo-1553621042-f6e147245754",
    "Caprese Salad":      "photo-1555939594-58d7cb561ad1",
    "Risotto Funghi":     "photo-1476124369491-e7addf5db371",
    "Panna Cotta":        "photo-1551024506-0bccd828d307",
}

# Specific filenames
FILENAMES = {
    "Dal Makhani":        "dal_makhani.jpg",
    "Mutton Biryani":     "mutton_biryani.jpg",
    "Gulab Jamun":        "gulab_jamun.jpg",
    "Chocolate Lava Cake":"chocolate_lava_cake.jpg",
    "Medu Vada":          "medu_vada.jpg",
    "Masala Dosa":        "masala_dosa.jpg",
    "Chettinad Chicken":  "chettinad_chicken.jpg",
    "Sambar Rice":        "sambar_rice.jpg",
    "Payasam":            "payasam.jpg",
    "Spice Garden Thali": "spice_garden_thali.jpg",
    "Galouti Kebab":      "galouti_kebab.jpg",
    "Dum Biryani":        "dum_biryani.jpg",
    "Shahi Paneer":       "shahi_paneer.jpg",
    "Prawn Tempura":      "prawn_tempura.jpg",
    "Goan Fish Curry":    "goan_fish_curry.jpg",
    "Sushi Roll Set":     "sushi_roll_set.jpg",
    "Caprese Salad":      "caprese_salad.jpg",
    "Risotto Funghi":     "risotto_funghi.jpg",
    "Panna Cotta":        "panna_cotta.jpg",
}


def get_wmc_url(file_title):
    encoded = urllib.parse.quote(file_title.replace(" ", "_"))
    api = (
        "https://commons.wikimedia.org/w/api.php"
        f"?action=query&titles={encoded}&prop=imageinfo"
        "&iiprop=url|size&iiurlwidth=1920&format=json"
    )
    req = urllib.request.Request(api, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read())
    for page in data.get("query", {}).get("pages", {}).values():
        for ii in page.get("imageinfo", []):
            return ii.get("thumburl") or ii.get("url")
    return None


def download(url, dest_path):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
    if len(data) < 8000:
        return 0
    with open(dest_path, "wb") as f:
        f.write(data)
    return len(data) // 1024


def fix(dish, filename):
    dest = os.path.join(DEST_DIR, filename)

    # Try Wikimedia with retry
    wmc_title = WMC.get(dish)
    if wmc_title:
        for attempt in range(3):
            try:
                time.sleep(3 if attempt == 0 else 5)   # polite delay
                img_url = get_wmc_url(wmc_title)
                if img_url:
                    kb = download(img_url, dest)
                    if kb:
                        print(f"  WMC  {dish:<30} {kb}KB")
                        return True
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = 10 * (attempt + 1)
                    print(f"  WMC 429 for {dish} – waiting {wait}s …")
                    time.sleep(wait)
                else:
                    print(f"  WMC err {dish}: {e}")
                    break
            except Exception as e:
                print(f"  WMC err {dish}: {e}")
                break

    # Unsplash fallback
    photo_id = UNSPLASH.get(dish)
    if photo_id:
        try:
            url = f"https://images.unsplash.com/{photo_id}?w=1920&q=85&fit=crop&auto=format"
            time.sleep(0.5)
            kb = download(url, dest)
            if kb:
                print(f"  UNS  {dish:<30} {kb}KB")
                return True
        except Exception as e:
            print(f"  UNS err {dish}: {e}")

    print(f"  FAIL {dish}")
    return False


def main():
    print("=" * 60)
    print("Fixing 19 failed dish images …")
    print("=" * 60)
    ok = fail = 0
    for dish, filename in FILENAMES.items():
        success = fix(dish, filename)
        if success:
            ok += 1
        else:
            fail += 1

    print(f"\nFixed: {ok}  |  Still failed: {fail}")

    if fail == 0:
        print("All images successfully replaced!")
    else:
        print("Some dishes still need manual attention.")

    # Final verification
    sys.path.insert(0, os.path.dirname(__file__))
    os.chdir(os.path.dirname(__file__))
    from app import create_app
    from models import db, Menu

    app = create_app()
    broken = []
    with app.app_context():
        for m in Menu.query.all():
            if m.image_url:
                full = os.path.join(os.path.dirname(__file__), "static", "images", m.image_url)
                if not os.path.exists(full) or os.path.getsize(full) < 5000:
                    broken.append(f"ID {m.id}: {m.name} -> {m.image_url}")
    if broken:
        print(f"\nBroken links ({len(broken)}):")
        for b in broken:
            print(" ", b)
    else:
        print(f"\nAll {Menu.query.count()} dish image links are valid.")


if __name__ == "__main__":
    main()
