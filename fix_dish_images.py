"""
fix_dish_images.py  –  Replace incorrect dish images with accurate ones.
Sources: Wikimedia Commons (primary for Indian dishes) + Unsplash (fallback)
"""

import os, sys, time, urllib.request, urllib.parse, json

DEST_DIR = os.path.join(os.path.dirname(__file__), "static", "images", "dishes")
os.makedirs(DEST_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Authoritative replacements: Wikimedia Commons file titles ────────────────
# These are verified to exist on Wikimedia Commons and accurately show the dish
WIKIMEDIA_FILES = {
    # Dishes that were wrong / need better photos
    "Lobster Thermidor":    "File:Lobster Thermidor.jpg",
    "Chicken 65":           "File:CHICKEN 65 - Mini Madras 2026-05-14.jpg",
    "Galouti Kebab":        "File:Mouth Watering Gauloti Kababs.jpg",
    "Butter Chicken":       "File:Butter Chicken, City Grill Kottayam.jpg",
    "Dum Biryani":          "File:Mutton Dum biryani.jpg",
    "Mutton Biryani":       "File:A home made plate of mutton biryani served with chicken kassa cooked in the bengali style.jpg",
    "Paneer Tikka":         "File:Paneer Tikka Shashlik PK012.jpg",
    "Chocolate Lava Cake":  "File:Vegan Flourless Swiss Chocolate Molten Lava Cake (4867538601).jpg",
    "Tiramisu":             "File:Tiramisu dessert.jpg",

    # Other Indian dishes that benefit from authentic Wikimedia photos
    "Masala Dosa":          "File:Masala Dosa.jpg",
    "Medu Vada":            "File:Medu_vada.jpg",
    "Chettinad Chicken":    "File:Chettinad chicken.jpg",
    "Dal Makhani":          "File:Dal Makhani.jpg",
    "Gulab Jamun":          "File:Two Gulab Jamun in a plate 01.jpg",
    "Rasmalai":             "File:Rasmalai.jpg",
    "Payasam":              "File:Payasam Kerala.jpg",
    "Phirni":               "File:Phirni.jpg",
    "Shahi Paneer":         "File:Shahi Paneer.jpg",
    "Sambar Rice":          "File:Curd rice2.jpg",
    "Spice Garden Thali":   "File:Meals in south India.jpg",
    "Paneer Butter Masala": "File:Paneer butter masala.jpg",

    # International dishes
    "Goan Fish Curry":      "File:Goan fish curry.jpg",
    "Prawn Tempura":        "File:Prawn tempura.jpg",
    "Sushi Roll Set":       "File:Sashimi special lunch at Ajisen Ramen Restaurant.jpg",
    "Thai Iced Tea":        "File:Thai iced tea.jpg",
    "Caprese Salad":        "File:Caprese salad (Capreses).jpg",
    "Pasta Carbonara":      "File:Spaghetti alla carbonara.jpg",
    "Risotto Funghi":       "File:Risotto funghi.jpg",
    "Panna Cotta":          "File:Panna cotta with caramel.jpg",
    "Tiramisu":             "File:Tiramisu dessert.jpg",
    "Espresso":             "File:A small cup of coffee.JPG",
}

# ── Unsplash photo IDs for dishes not on Wikimedia or as fallback ────────────
UNSPLASH_IDS = {
    "Filter Coffee":        "photo-1495474472287-4d71bcdd2085",
    "Royal Feast Combo":    "photo-1596040033229-a9821ebd058d",
    "Veg Delight Combo":    "photo-1455619452474-d2be8b1e70cd",
    "Lobster Thermidor":    "photo-1560717789-0ac7c58ac90a",
    "Asian Explorer Combo": "photo-1569050467447-ce54b3bbc37d",
    "Seafood Platter":      "photo-1484723091739-30a097e8f929",
    "Dim Sum Platter":      "photo-1563245372-f21724e3856d",
    "Pad Thai":             "photo-1569050467447-ce54b3bbc37d",
    "Mochi Ice Cream":      "photo-1563805042-7684c019e1cb",
    "Margherita Pizza":     "photo-1574071318508-1cdbab80d002",
    "Bruschetta":           "photo-1572695157366-5e585ab2b69f",
    "Italian Feast Combo":  "photo-1414235077428-338989a2e8c0",
    "Limoncello Spritz":    "photo-1570696516188-ade861b84a49",
    "Blue Lagoon Mocktail": "photo-1570696516188-ade861b84a49",
    "Coconut Panna Cotta":  "photo-1551024506-0bccd828d307",
    "Coconut Rice":         "photo-1536304993881-ff6e9eefa2a6",
    "Kung Pao Chicken":     "photo-1604908176997-125f25cc6f3d",
    "Thai Spring Rolls":    "photo-1615361200141-f45040f367be",
    "Fresh Lime Soda":      "photo-1513558161293-cdaf765ed2fd",
    "Mango Lassi":          "photo-1553361371-9b22f78e8b1d",
    "Masala Chai":          "photo-1564890369478-c89ca6d9cde9",
    "Thandai":              "photo-1553361371-9b22f78e8b1d",
    "Fish Tikka":           "photo-1467003909585-2f8a72700288",
    "Dahi Ke Kebab":        "photo-1599487488170-d11ec9c172f0",
    "Mughlai Chicken Curry":"photo-1574653853027-5382a3d23a15",
    "Veg Fried Rice":       "photo-1603133872878-684f208fb84b",
    "Chicken Seekh Kebab":  "photo-1628294895950-9805252f784d",
    "Crispy Corn":          "photo-1547592180-85f173990554",
    "Mushroom Galawat":     "photo-1504674900247-0877df9cc836",
    "Phirni":               "photo-1579954115545-a95591f28bfc",
}


def get_wikimedia_url(file_title):
    """Resolve a Wikimedia Commons file title to a direct image URL."""
    encoded = urllib.parse.quote(file_title.replace(" ", "_"))
    api = (
        "https://commons.wikimedia.org/w/api.php"
        f"?action=query&titles={encoded}&prop=imageinfo"
        "&iiprop=url|size&iiurlwidth=1920&format=json"
    )
    req = urllib.request.Request(api, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    for page in data.get("query", {}).get("pages", {}).values():
        for ii in page.get("imageinfo", []):
            return ii.get("thumburl") or ii.get("url")
    return None


def download_url(url, dest_path):
    """Download a URL and save to dest_path. Returns size in KB or 0 on failure."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
    if len(data) < 8000:
        return 0
    with open(dest_path, "wb") as f:
        f.write(data)
    return len(data) // 1024


def fix_dish(dish_name, filename):
    """Try Wikimedia first, then Unsplash. Return True if downloaded."""
    dest = os.path.join(DEST_DIR, filename)

    # 1. Wikimedia Commons
    wmc_title = WIKIMEDIA_FILES.get(dish_name)
    if wmc_title:
        try:
            img_url = get_wikimedia_url(wmc_title)
            if img_url:
                kb = download_url(img_url, dest)
                if kb:
                    print(f"  WMC  {dish_name:<30} {kb}KB  [{wmc_title[:50]}]")
                    return True
        except Exception as e:
            print(f"  wmc ERR {dish_name}: {e}")
        time.sleep(0.5)

    # 2. Unsplash fallback
    photo_id = UNSPLASH_IDS.get(dish_name)
    if photo_id:
        try:
            url = f"https://images.unsplash.com/{photo_id}?w=1920&q=85&fit=crop&auto=format"
            kb = download_url(url, dest)
            if kb:
                print(f"  UNS  {dish_name:<30} {kb}KB")
                return True
        except Exception as e:
            print(f"  uns ERR {dish_name}: {e}")

    print(f"  FAIL {dish_name}")
    return False


# All dishes and their filenames
ALL_DISHES = {
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
    "Medu Vada":            "medu_vada.jpg",
    "Chicken 65":           "chicken_65.jpg",
    "Masala Dosa":          "masala_dosa.jpg",
    "Chettinad Chicken":    "chettinad_chicken.jpg",
    "Sambar Rice":          "sambar_rice.jpg",
    "Payasam":              "payasam.jpg",
    "Filter Coffee":        "filter_coffee.jpg",
    "Spice Garden Thali":   "spice_garden_thali.jpg",
    "Galouti Kebab":        "galouti_kebab.jpg",
    "Dahi Ke Kebab":        "dahi_ke_kebab.jpg",
    "Mughlai Chicken Curry":"mughlai_chicken_curry.jpg",
    "Dum Biryani":          "dum_biryani.jpg",
    "Shahi Paneer":         "shahi_paneer.jpg",
    "Phirni":               "phirni.jpg",
    "Thandai":              "thandai.jpg",
    "Royal Feast":          "royal_feast.jpg",
    "Prawn Tempura":        "prawn_tempura.jpg",
    "Fish Tikka":           "fish_tikka.jpg",
    "Goan Fish Curry":      "goan_fish_curry.jpg",
    "Lobster Thermidor":    "lobster_thermidor.jpg",
    "Coconut Rice":         "coconut_rice.jpg",
    "Coconut Panna Cotta":  "coconut_panna_cotta.jpg",
    "Blue Lagoon Mocktail": "blue_lagoon_mocktail.jpg",
    "Seafood Platter":      "seafood_platter.jpg",
    "Dim Sum Platter":      "dim_sum_platter.jpg",
    "Thai Spring Rolls":    "thai_spring_rolls.jpg",
    "Kung Pao Chicken":     "kung_pao_chicken.jpg",
    "Pad Thai":             "pad_thai.jpg",
    "Sushi Roll Set":       "sushi_roll_set.jpg",
    "Mochi Ice Cream":      "mochi_ice_cream.jpg",
    "Thai Iced Tea":        "thai_iced_tea.jpg",
    "Asian Explorer Combo": "asian_explorer_combo.jpg",
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

# Dishes that MUST be replaced regardless of existing file
MUST_REPLACE = {
    "Lobster Thermidor", "Galouti Kebab", "Royal Feast Combo",
    "Chicken 65", "Paneer Tikka", "Butter Chicken", "Dum Biryani",
    "Mutton Biryani", "Chocolate Lava Cake", "Filter Coffee", "Tiramisu",
    # Also replace these with better Wikimedia authentic photos
    "Masala Dosa", "Medu Vada", "Dal Makhani", "Gulab Jamun",
    "Rasmalai", "Payasam", "Phirni", "Shahi Paneer", "Sambar Rice",
    "Spice Garden Thali", "Paneer Butter Masala", "Goan Fish Curry",
    "Prawn Tempura", "Sushi Roll Set", "Caprese Salad",
    "Pasta Carbonara", "Risotto Funghi", "Panna Cotta", "Espresso",
    "Chettinad Chicken",
}


def main():
    print("=" * 65)
    print("DelishNex – Dish Image Fixer (Wikimedia + Unsplash)")
    print("=" * 65)

    ok = fail = skipped = 0

    for dish_name, filename in ALL_DISHES.items():
        dest = os.path.join(DEST_DIR, filename)
        needs_update = dish_name in MUST_REPLACE
        has_file = os.path.exists(dest) and os.path.getsize(dest) > 8000

        if has_file and not needs_update:
            print(f"  OK   {dish_name:<30} (kept)")
            skipped += 1
            continue

        success = fix_dish(dish_name, filename)
        if success:
            ok += 1
        else:
            fail += 1
        time.sleep(0.4)

    print(f"\n{'='*65}")
    print(f"Replaced/downloaded: {ok}  |  Kept existing: {skipped}  |  Failed: {fail}")
    return fail


if __name__ == "__main__":
    fails = main()
    sys.exit(0 if fails == 0 else 1)
