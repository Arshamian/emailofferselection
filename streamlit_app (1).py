import streamlit as st
import pandas as pd
import numpy as np
import json
import re
from datetime import datetime, date, timedelta
from anthropic import Anthropic

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SHG D2 Weekly Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inject brand CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
  --navy:#1B1464; --gold:#D4AF37; --green:#0A7C4E;
  --amber:#C17A00; --red:#C0392B; --off-white:#F7F8FC;
}
[data-testid="stAppViewContainer"] { background:var(--off-white); }
header[data-testid="stHeader"] { background:var(--navy); }
h1,h2,h3 { color:var(--navy); }
.metric-card {
  background:#fff; border:1px solid #E8EAF0; border-radius:10px;
  padding:16px 20px; text-align:center;
}
.metric-val { font-size:28px; font-weight:700; color:#1B1464; }
.metric-lbl { font-size:11px; color:#8896A8; text-transform:uppercase; letter-spacing:.4px; }
.hotel-card {
  background:#fff; border:1px solid #E8EAF0; border-radius:8px;
  padding:14px 16px; margin-bottom:10px;
}
.hotel-card.tier1 { border-left:4px solid #7c3aed; }
.hotel-card.tier2 { border-left:4px solid #0e6b85; }
.hotel-card.tier3 { border-left:4px solid #4b5563; }
.hotel-card.has-offer { border-top:2px solid #D4AF37; }
.badge {
  display:inline-block; font-size:10px; font-weight:600;
  padding:2px 8px; border-radius:3px; margin-right:4px;
}
.badge-tier1 { background:#F3EEFF; color:#7c3aed; }
.badge-tier2 { background:#E6F4F8; color:#0e6b85; }
.badge-tier3 { background:#F3F4F6; color:#4b5563; }
.badge-offer { background:#D4AF37; color:#412402; }
.badge-exp   { background:#FEF2F2; color:#C0392B; border:1px solid #FCA5A5; }
.badge-score5{ background:#F0FBF5; color:#0A7C4E; }
.badge-score4{ background:#FFFBEB; color:#C17A00; }
.offer-box {
  background:#FFFBEB; border-left:3px solid #D4AF37;
  padding:8px 12px; border-radius:0 6px 6px 0;
  font-size:12px; color:#412402; margin-top:8px;
}
.offer-box.expiring {
  background:#FEF2F2; border-left-color:#C0392B; color:#991B1B;
}
.chip {
  display:inline-block; font-size:11px; font-weight:600;
  padding:4px 12px; border-radius:3px; margin-right:6px;
  margin-bottom:6px; cursor:pointer;
}
.chip-urgent { background:#C0392B; color:#fff; }
.chip-offer  { background:#D4AF37; color:#412402; }
.chip-seller { background:#F3EEFF; color:#7c3aed; border:1px solid #7c3aed; }
.chip-value  { background:#E6F4F8; color:#0e6b85; border:1px solid #0e6b85; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
DEST_MAP = {
    "heraklion - greece": "Crete (Heraklion) - Greece",
    "chania - greece": "Crete (Chania) - Greece",
    "kerkyra - greece": "Corfu - Greece",
    "kos - greece": "Kos - Greece",
    "rhodes - greece": "Rhodes - Greece",
    "zakynthos - greece": "Zante - Greece",
    "thira - greece": "Santorini - Greece",
    "mikonos - greece": "Mykonos - Greece",
    "thessaloniki - greece": "Halkidiki - Greece",
    "kavala - greece": "Halkidiki - Greece",
    "kefallinia - greece": "Kefalonia - Greece",
    "skiathos - greece": "Skiathos - Greece",
    "kalamata - greece": "Kalamata - Greece",
    "preveza lefkas - greece": "Lefkas - Greece",
    "preveza/lefkas - greece": "Lefkas - Greece",
    "athens - greece": "Athens - Greece",
    "phuket - thailand": "Phuket - Thailand",
    "koh samui - thailand": "Koh Samui - Thailand",
    "krabi - thailand": "Krabi - Thailand",
    "dubai - united arab emirates": "Dubai - United Arab Emirates",
    "abu dhabi - united arab emirates": "Abu Dhabi - United Arab Emirates",
    "ras al khaimah - united arab emirates": "Ras al Khaimah - United Arab Emirates",
    "male - maldives": "Maldives - Indian Ocean",
    "mauritius - mauritius": "Mauritius - Indian Ocean",
    "mahe island - seychelles": "Seychelles - Indian Ocean",
    "colombo - sri lanka": "Sri Lanka - Indian Ocean",
    "doha - qatar": "Doha - Qatar",
    "muscat - oman": "Muscat - Oman",
    "salalah - oman": "Salalah - Oman",
    "antalya - turkey": "Antalya - Turkey",
    "bodrum - turkey": "Bodrum - Turkey",
    "dalaman - turkey": "Dalaman - Turkey",
    "cancun - mexico": "All Resorts inc Cancun - Mexico",
    "punta cana - dominican republic": "Dominican Republic South East - Caribbean",
    "barbados - barbados": "Barbados - Caribbean",
    "st lucia - saint lucia": "Saint Lucia - Caribbean",
    "antigua - antigua and barbuda": "Antigua - Caribbean",
    "kingston - jamaica": "Jamaica - Caribbean",
    "montego bay - jamaica": "Jamaica - Caribbean",
    "tenerife - spain - canaries": "Tenerife Spain - Canaries",
    "gran canaria - spain - canaries": "Gran Canaria Spain - Canaries",
    "lanzarote - spain - canaries": "Lanzarote Spain - Canaries",
    "fuerteventura - spain - canaries": "Fuerteventura Spain - Canaries",
    "palma mallorca - spain - balearics": "Majorca Spain - Balearics",
    "ibiza - spain - balearics": "Ibiza Spain - Balearics",
    "menorca - spain - balearics": "Menorca Spain - Balearics",
    "malaga - spain - mainland": "Costa Del Sol - Spain",
    "alicante - spain - mainland": "Costa Blanca (Benidorm, Alicante) - Spain",
    "goa - india": "Goa - India",
    "denpasar bali - indonesia": "Bali - Indonesia",
    "faro - portugal": "Algarve - Portugal",
    "funchal - portugal": "Madeira - Portugal",
    "larnaca - cyprus": "Larnaca - Cyprus",
    "paphos - cyprus": "Paphos - Cyprus",
    "marrakech - morocco": "Marrakech - Morocco",
    "agadir - morocco": "Agadir - Morocco",
    "hurghada - egypt": "Hurghada - Egypt",
    "sharm el sheikh - egypt": "Sharm El Sheikh - Egypt",
    "zanzibar - tanzania": "Zanzibar - Tanzania",
    "phuket - thailand": "Phuket - Thailand",
    "koh lanta - thailand": "Koh Lanta - Thailand",
    "bangkok - thailand": "Bangkok - Thailand",
    "chiang mai - thailand": "Chiang Mai - Thailand",
    "dubrovnik - croatia": "Dubrovnik - Croatia",
    "malta - malta": "Malta",
    "cape town - south africa": "Cape Town - South Africa",
    "singapore - singapore": "Singapore - Singapore",
    "da nang - viet nam": "Danang - Vietnam",
    "hanoi - viet nam": "Hanoi - Vietnam",
    "ho chi minh city - viet nam": "Ho Chi Minh City - Vietnam",
    "tokyo - japan": "Tokyo - Japan",
    "las vegas - united states": "Las Vegas - United States",
    "new york ny - united states": "New York - United States",
    "orlando fl - united states": "Orlando Florida - United States",
}

MACRO_MAP = {
    "Greece": "Mediterranean", "Turkey": "Mediterranean", "Cyprus": "Mediterranean",
    "Croatia": "Mediterranean", "Malta": "Mediterranean", "Italy": "Mediterranean",
    "Spain": "Mediterranean", "Portugal": "Mediterranean", "Bulgaria": "Mediterranean",
    "Egypt": "Mediterranean",
    "Canaries": "Africa & Canaries", "Morocco": "Africa & Canaries",
    "South Africa": "Africa & Canaries", "Tanzania": "Africa & Canaries",
    "United Arab Emirates": "Middle East & Indian Ocean",
    "Qatar": "Middle East & Indian Ocean", "Oman": "Middle East & Indian Ocean",
    "Bahrain": "Middle East & Indian Ocean", "Indian Ocean": "Middle East & Indian Ocean",
    "Maldives": "Middle East & Indian Ocean",
    "Thailand": "Asia Pacific", "Indonesia": "Asia Pacific", "India": "Asia Pacific",
    "Malaysia": "Asia Pacific", "Singapore": "Asia Pacific", "Vietnam": "Asia Pacific",
    "Japan": "Asia Pacific", "HongKong": "Asia Pacific",
    "Caribbean": "Caribbean & Americas", "Mexico": "Caribbean & Americas",
    "United States": "Caribbean & Americas", "Jamaica": "Caribbean & Americas",
    "Barbados": "Caribbean & Americas",
}

TODAY = date.today()

# ── Session state init ────────────────────────────────────────────────────────
for k, v in [("payload", None), ("shortlist", []), ("dq_notes", []),
              ("last_updated", None), ("generating", False)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── Processing functions ──────────────────────────────────────────────────────

def parse_date_safe(val):
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


def normalise_col(df, candidates, target):
    for c in candidates:
        matches = [col for col in df.columns if col.strip().lower() == c.lower()]
        if matches:
            df = df.rename(columns={matches[0]: target})
            break
    return df


def get_macro(region_str):
    for k, v in MACRO_MAP.items():
        if k.lower() in region_str.lower():
            return v
    return "Other"


def process_snapshot(df):
    dq = []
    # Normalise columns
    col_map = {
        "Name": "Name", "Name.1": "Region", "Giata": "Giata",
        "StarRating": "Stars", "CheapestPrice": "Price",
        "CheapestBoard": "Board", "CheapestPriceDate": "PriceDate",
        "PricesLastRefreshed": "Refreshed",
    }
    rename = {}
    for src, tgt in col_map.items():
        for col in df.columns:
            if col.strip() == src:
                rename[col] = tgt
    df = df.rename(columns=rename)

    required = ["Name", "Region", "Price"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        dq.append(f"Missing snapshot columns: {', '.join(missing)}")

    df["Price"] = pd.to_numeric(df.get("Price", 0), errors="coerce").fillna(0)
    df = df[df["Price"] > 0].copy()

    df["Giata"] = df.get("Giata", "").astype(str).str.strip()
    df["Stars"] = pd.to_numeric(df.get("Stars", 0), errors="coerce").fillna(0).astype(int)
    df["Region"] = df.get("Region", "").astype(str).str.strip()
    df["Country"] = df["Region"].apply(lambda r: r.split(" - ")[-1] if " - " in r else r)

    # Deduplicate
    before = len(df)
    df = df.drop_duplicates(subset=["Name", "Region"], keep="first")
    removed = before - len(df)
    if removed:
        dq.append(f"Removed {removed} duplicate hotels (Name+Region).")

    # Cache refresh date
    cache_refreshed = ""
    if "Refreshed" in df.columns:
        try:
            cache_refreshed = pd.to_datetime(df["Refreshed"], errors="coerce").max().strftime("%d %b %Y")
        except Exception:
            pass

    df = df.sort_values(["Region", "Price"])
    return df, dq, cache_refreshed


def process_bookings(df):
    dq = []
    if df is None or df.empty:
        return pd.DataFrame(), dq, None, None

    # Normalise BookedDate
    df["BookedDate"] = pd.to_datetime(df.get("BookedDate", pd.Series(dtype=str)), errors="coerce")
    df = df.dropna(subset=["BookedDate"])

    valid_status = {"AUTH", "PROV", "OPS"}
    if "FolderStatus" in df.columns:
        df = df[df["FolderStatus"].str.upper().isin(valid_status)]
    if "ProdMix" in df.columns:
        df = df[df["ProdMix"].str.strip().str.lower() == "mixed"]

    df["FolderPax"] = pd.to_numeric(df.get("FolderPax", 1), errors="coerce").fillna(0)
    df = df[df["FolderPax"] > 0]
    df["KPIRevenue"] = pd.to_numeric(df.get("KPIRevenue", 0), errors="coerce").fillna(0)
    df["KPIProfit"] = pd.to_numeric(df.get("KPIProfit", 0), errors="coerce").fillna(0)
    df["rev_pp"] = df["KPIRevenue"] / df["FolderPax"]
    df["profit_pp"] = df["KPIProfit"] / df["FolderPax"]

    # Map destination to region
    unmapped = set()
    def map_dest(row):
        dest = str(row.get("HotelNames", "")).strip().lower()
        # try destination columns
        for col in ["Destination", "destination", "DestName", "destname"]:
            if col in row and pd.notna(row[col]):
                dest_col = str(row[col]).strip().lower()
                country_col = ""
                for cc in ["DestCountry", "destcountry", "Country", "country"]:
                    if cc in row and pd.notna(row[cc]):
                        country_col = str(row[cc]).strip().lower()
                        break
                key = f"{dest_col} - {country_col}" if country_col else dest_col
                if key in DEST_MAP:
                    return DEST_MAP[key]
        return None

    # Build destination key from available columns
    dest_cols = [c for c in df.columns if "dest" in c.lower() or "destination" in c.lower()]
    country_cols = [c for c in df.columns if "country" in c.lower()]

    if dest_cols:
        dc = dest_cols[0]
        cc = country_cols[0] if country_cols else None
        def make_key(row):
            d = str(row.get(dc, "")).strip().lower()
            c = str(row.get(cc, "")).strip().lower() if cc else ""
            return f"{d} - {c}" if c else d
        df["_dest_key"] = df.apply(make_key, axis=1)
        df["mapped_region"] = df["_dest_key"].map(DEST_MAP)
        unmapped_keys = df[df["mapped_region"].isna()]["_dest_key"].unique()
        for k in unmapped_keys[:10]:
            unmapped.add(k)
    else:
        df["mapped_region"] = None

    if unmapped:
        dq.append(f"Unmapped booking destinations ({len(unmapped)}): {', '.join(list(unmapped)[:5])}{'...' if len(unmapped) > 5 else ''}")

    max_date = df["BookedDate"].max().date()
    min_date = (df["BookedDate"].max() - pd.Timedelta(weeks=6)).date()
    return df, dq, min_date, max_date


def compute_region_stats(bookings_df, min_date, max_date):
    stats = {}
    if bookings_df.empty or "mapped_region" not in bookings_df.columns:
        return stats
    window = bookings_df[
        (bookings_df["BookedDate"].dt.date >= min_date) &
        (bookings_df["BookedDate"].dt.date <= max_date) &
        bookings_df["mapped_region"].notna()
    ]
    for region, grp in window.groupby("mapped_region"):
        rev = grp["rev_pp"].dropna()
        stats[region] = {
            "bookings_6w": len(grp),
            "avg_rev_pp": float(rev.mean()) if len(rev) else None,
            "median_rev_pp": float(rev.median()) if len(rev) else None,
            "p25_rev_pp": float(rev.quantile(0.25)) if len(rev) else None,
            "p75_rev_pp": float(rev.quantile(0.75)) if len(rev) else None,
            "avg_profit_pp": float(grp["profit_pp"].mean()) if len(grp) else None,
            "total_profit_6w": float(grp["profit_pp"].sum() * grp["FolderPax"].mean()) if len(grp) else None,
        }
    return stats


def compute_seller_tiers(bookings_df):
    tiers = {}  # region -> {hotel_name -> {tier, count}}
    if bookings_df.empty or "mapped_region" not in bookings_df.columns:
        return tiers
    hotel_col = next((c for c in bookings_df.columns if "hotel" in c.lower()), None)
    if not hotel_col:
        return tiers
    valid = bookings_df[bookings_df["mapped_region"].notna()]
    for region, grp in valid.groupby("mapped_region"):
        counts = grp[hotel_col].value_counts()
        total = counts.sum()
        cum = 0
        region_tiers = {}
        for i, (name, cnt) in enumerate(counts.items()):
            cum += cnt
            share = cum / total
            if share <= 0.40 and i < 5:
                t = 1
            elif share <= 0.75:
                t = 2
            else:
                t = 3
            region_tiers[name.strip().lower()] = {"tier": t, "count": int(cnt)}
        tiers[region] = region_tiers
    return tiers


def value_score(price, stats):
    if not stats or stats.get("median_rev_pp") is None:
        return 1, "no_data"
    p25 = stats.get("p25_rev_pp") or 0
    med = stats.get("median_rev_pp") or 0
    p75 = stats.get("p75_rev_pp") or 0
    if price <= p25:
        return 5, "exceptional"
    elif price <= med:
        return 4, "good_value"
    elif price <= p75:
        return 3, "fair"
    else:
        return 2, "above_typical"


def normalise_offers(df):
    col_aliases = {
        "giata": ["giata", "GIATA"],
        "hotel": ["hotel", "Hotel", "HotelName"],
        "summary": ["tacticalofferdetails", "offer_details", "details", "Summary"],
        "travel_from": ["travelfrom", "travel_from", "TravelFrom"],
        "travel_to": ["travelto", "travel_to", "TravelTo"],
        "booking_from": ["bookingfrom", "booking_from", "BookingFrom"],
        "booking_to": ["bookingto", "booking_to", "BookingTo"],
        "type": ["offertype", "offer_type", "OfferType", "Type"],
        "category": ["offertypecategory", "offer_type_category"],
    }
    for target, aliases in col_aliases.items():
        for col in df.columns:
            if col.strip().lower() in [a.lower() for a in aliases] and target not in df.columns:
                df = df.rename(columns={col: target})
    df["giata"] = df.get("giata", pd.Series(dtype=str)).astype(str).str.strip()
    return df


def parse_offer_date(val):
    if not val or pd.isna(val):
        return None
    try:
        return pd.to_datetime(val, dayfirst=True).date()
    except Exception:
        return None


def build_payload(snap_df, region_stats, seller_tiers, offers_df, cache_refreshed, bm_from, bm_to):
    dq = []
    today_dt = TODAY

    # Build offers lookup by giata
    offers_map = {}
    unmatched_giatas = 0
    if offers_df is not None and not offers_df.empty:
        offers_df = normalise_offers(offers_df)
        for _, row in offers_df.iterrows():
            g = str(row.get("giata", "")).strip()
            if not g or g == "nan":
                continue
            book_to = parse_offer_date(row.get("booking_to"))
            is_active = (book_to is None) or (book_to >= today_dt)
            if not is_active:
                continue
            expiring = book_to is not None and (book_to - today_dt).days <= 7
            tags = []
            summary = str(row.get("summary", ""))
            for tag in ["discount", "room upgrade", "board upgrade", "kids free",
                        "free nights", "transfers", "resort credit"]:
                if tag.lower() in summary.lower():
                    tags.append(tag)
            offers_map[g] = {
                "summary": summary,
                "type": str(row.get("type", "")),
                "tags": tags,
                "travel_to": str(row.get("travel_to", "")) if pd.notna(row.get("travel_to", "")) else "",
                "book_to": book_to.strftime("%d %b %Y") if book_to else "",
                "book_to_date": book_to,
                "expiring_soon": expiring,
            }

    # Build nested data structure
    data = {}
    hotels_with_offers = 0

    for region in snap_df["Region"].unique():
        rdf = snap_df[snap_df["Region"] == region]
        country = rdf["Country"].iloc[0] if len(rdf) else ""
        macro = get_macro(region)
        stats = region_stats.get(region, {})
        rtiers = seller_tiers.get(region, {})

        if macro not in data:
            data[macro] = {}

        hotels = []
        for _, row in rdf.iterrows():
            name = str(row.get("Name", "")).strip()
            giata = str(row.get("Giata", "")).strip()
            price = float(row.get("Price", 0))
            stars = int(row.get("Stars", 0))
            board = str(row.get("Board", ""))
            price_date = str(row.get("PriceDate", ""))[:10]

            # Seller tier
            norm_name = re.sub(r"[^\w\s]", "", name.lower()).strip()
            tier_info = rtiers.get(norm_name) or rtiers.get(name.lower())
            if tier_info:
                tier = tier_info["tier"]
                bkgs_total = tier_info["count"]
            elif rtiers:
                tier = 0
                bkgs_total = 0
            else:
                tier = -1
                bkgs_total = 0

            score, value_tag = value_score(price, stats)

            offer = offers_map.get(giata)
            if offer:
                hotels_with_offers += 1
                offer_out = {k: v for k, v in offer.items() if k != "book_to_date"}
            else:
                if giata and giata != "nan":
                    unmatched_giatas += 1
                offer_out = None

            hotels.append({
                "h": name, "giata": giata, "s": stars, "r": region,
                "c": country, "p": round(price, 2), "b": board, "d": price_date,
                "seller_tier": tier, "bookings_total": bkgs_total,
                "bookings_6w": stats.get("bookings_6w", 0),
                "score": score, "value_tag": value_tag,
                "offer": offer_out,
            })

        data[macro][region] = {
            "bookings_6w": stats.get("bookings_6w", 0),
            "median_rev_pp": stats.get("median_rev_pp"),
            "avg_rev_pp": stats.get("avg_rev_pp"),
            "p25_rev_pp": stats.get("p25_rev_pp"),
            "p75_rev_pp": stats.get("p75_rev_pp"),
            "avg_profit_pp": stats.get("avg_profit_pp"),
            "total_profit_6w": stats.get("total_profit_6w"),
            "hotels": hotels,
        }

    if unmatched_giatas > 0:
        dq.append(f"Offer GIATAs with no price snapshot match: {unmatched_giatas}")

    # Explorer flags
    all_hotels_flat = [h for macro in data.values() for reg in macro.values() for h in reg["hotels"]]
    expiring_count = sum(1 for h in all_hotels_flat if h.get("offer") and h["offer"].get("expiring_soon"))

    top_offer_dest = sorted(
        [h for h in all_hotels_flat if h.get("offer")],
        key=lambda h: (h["offer"].get("expiring_soon", False), h["score"]),
        reverse=True
    )
    top_offer_dest_names = list(dict.fromkeys([h["c"] for h in top_offer_dest]))[:3]

    top_seller_regions = sorted(
        [(rname, rdata.get("bookings_6w", 0))
         for macro in data.values() for rname, rdata in macro.items()],
        key=lambda x: x[1], reverse=True
    )[:3]

    best_value_regions = sorted(
        [(rname, sum(1 for h in rdata["hotels"] if h["score"] >= 5))
         for macro in data.values() for rname, rdata in macro.items()],
        key=lambda x: x[1], reverse=True
    )[:3]

    meta = {
        "generated_at": datetime.utcnow().isoformat(),
        "cache_refreshed": cache_refreshed,
        "benchmark_from": str(bm_from) if bm_from else "",
        "benchmark_to": str(bm_to) if bm_to else "",
        "total_hotels": len(all_hotels_flat),
        "total_regions": sum(len(v) for v in data.values()),
        "hotels_with_offers": hotels_with_offers,
        "explorer_flags": {
            "top_offer_destinations": top_offer_dest_names,
            "expiring_soon_count": expiring_count,
            "top_seller_regions": [r[0] for r in top_seller_regions],
            "best_value_regions": [r[0] for r in best_value_regions],
            "new_bookable_regions": [],
        }
    }

    return {"meta": meta, "data": data}, dq


def build_shortlist(payload):
    shortlist = []
    today_dt = TODAY
    all_hotels = []
    for macro, regions in payload["data"].items():
        for rname, rdata in regions.items():
            for h in rdata["hotels"]:
                all_hotels.append((h, rdata, rname))

    def priority(h, reg):
        has_offer = 1 if h.get("offer") else 0
        expiring = 1 if h.get("offer") and h["offer"].get("expiring_soon") else 0
        tier_sc = {1: 300, 2: 200, 3: 100}.get(h["seller_tier"], 0)
        bkgs6w = min(reg.get("bookings_6w") or 0, 100)
        bkgs_total = min(h.get("bookings_total") or 0, 75)
        med = reg.get("median_rev_pp") or 0
        pct_below_med = max(0, (med - h["p"]) / med * 100) if med else 0
        p25 = reg.get("p25_rev_pp") or 0
        pct_below_p25 = max(0, (p25 - h["p"]) / p25 * 100) if p25 else 0
        return (has_offer * 400 + expiring * 150 + tier_sc + 40 * h["score"]
                + bkgs6w + bkgs_total + min(pct_below_med, 50) + min(pct_below_p25, 25))

    # Filter candidates
    candidates = []
    for score_thresh in [4, 3]:
        for h, reg, rname in all_hotels:
            tier = h["seller_tier"]
            has_offer = bool(h.get("offer"))
            if (tier in {1, 2, 3} and h["score"] >= score_thresh) or has_offer:
                p = priority(h, reg)
                candidates.append((p, h, reg, rname))
        if len(candidates) >= 20:
            break

    candidates.sort(key=lambda x: x[0], reverse=True)

    region_count = {}
    country_count = {}
    result = []
    for cap in [2, 3]:
        result = []
        region_count = {}
        country_count = {}
        for p, h, reg, rname in candidates:
            rc = region_count.get(rname, 0)
            cc = country_count.get(h["c"], 0)
            if rc >= cap or cc >= cap:
                continue
            region_count[rname] = rc + 1
            country_count[h["c"]] = cc + 1
            med = reg.get("median_rev_pp")
            below_med = round((med - h["p"]) / med * 100, 1) if med and med > 0 else None
            offer = h.get("offer") or {}
            result.append({
                "rank": len(result) + 1,
                "hotel": h["h"], "region": rname, "country": h["c"],
                "board": h["b"], "price": h["p"], "median": med,
                "bookings_total": h["bookings_total"],
                "region_bkgs": reg.get("bookings_6w", 0),
                "seller_tier": h["seller_tier"], "score": h["score"],
                "has_offer": bool(offer),
                "offer_type": offer.get("type", ""),
                "offer_summary": offer.get("summary", ""),
                "book_to": offer.get("book_to", ""),
                "travel_to": offer.get("travel_to", ""),
                "expiring_soon": offer.get("expiring_soon", False),
                "below_median_pct": below_med,
                "priority": round(p),
                "why": f"{'[OFFER] ' + offer.get('type','') + ' · ' if offer else ''}Tier {h['seller_tier']} · {h['value_tag'].replace('_',' ').title()} vs median · {rname}",
            })
            if len(result) >= 20:
                break
        if len(result) >= 20:
            break

    return result


# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_meta = st.columns([3, 1])
with col_logo:
    st.markdown(f"""
    <div style="background:#1B1464;padding:16px 24px;border-radius:10px;margin-bottom:16px">
      <span style="color:#D4AF37;font-size:22px;font-weight:700;letter-spacing:.5px">
        SHG // D2 Weekly Dashboard
      </span>
    </div>""", unsafe_allow_html=True)
with col_meta:
    if st.session_state.last_updated:
        st.caption(f"Last updated: {st.session_state.last_updated}")
        if st.session_state.payload:
            st.caption(f"Prices refreshed: {st.session_state.payload['meta'].get('cache_refreshed','')}")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_upload, tab_explorer, tab_shortlist, tab_dq = st.tabs([
    "📁 Upload & Generate", "🏨 Hotel Explorer", "📧 Email Shortlist", "⚠️ Data Quality"
])

# ── Tab 1: Upload ─────────────────────────────────────────────────────────────
with tab_upload:
    st.subheader("Upload Data Files")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**📊 Bookings Dataset**")
        st.caption("Excel (.xlsx) — any sheet")
        bk_file = st.file_uploader("Bookings", type=["xlsx"], label_visibility="collapsed", key="bk")
    with c2:
        st.markdown("**💰 Price Snapshot** *(required)*")
        st.caption("Excel (.xlsx) — 'D2 Price Snapshot' sheet")
        sn_file = st.file_uploader("Snapshot", type=["xlsx"], label_visibility="collapsed", key="sn")
    with c3:
        st.markdown("**🏷️ Special Offers**")
        st.caption("CSV file")
        of_file = st.file_uploader("Offers", type=["csv"], label_visibility="collapsed", key="of")

    st.divider()

    if st.button("🚀 Generate Dashboard", type="primary", disabled=sn_file is None):
        with st.spinner("Processing files..."):
            progress = st.progress(0, text="Reading price snapshot...")

            # Snapshot
            snap_raw = pd.read_excel(sn_file,
                sheet_name="D2 Price Snapshot" if "D2 Price Snapshot" in
                pd.ExcelFile(sn_file).sheet_names else 0)
            snap_df, snap_dq, cache_refreshed = process_snapshot(snap_raw)
            progress.progress(25, text=f"Snapshot: {len(snap_df)} hotels loaded")

            # Bookings
            bm_from = bm_to = None
            bookings_df = pd.DataFrame()
            bk_dq = []
            if bk_file:
                bk_raw = pd.read_excel(bk_file)
                bookings_df, bk_dq, bm_from, bm_to = process_bookings(bk_raw)
                progress.progress(45, text=f"Bookings: {len(bookings_df)} rows processed")
            else:
                bk_dq = ["No bookings file uploaded — seller tiers and benchmarks unavailable."]
                progress.progress(45, text="No bookings file — skipping")

            # Offers
            offers_df = None
            if of_file:
                offers_df = pd.read_csv(of_file)
                progress.progress(55, text=f"Offers: {len(offers_df)} rows loaded")
            else:
                progress.progress(55, text="No offers file — skipping")

            # Compute stats
            progress.progress(60, text="Computing region stats...")
            region_stats = compute_region_stats(bookings_df, bm_from, bm_to) if not bookings_df.empty else {}
            seller_tiers = compute_seller_tiers(bookings_df) if not bookings_df.empty else {}

            progress.progress(75, text="Building payload...")
            payload, build_dq = build_payload(snap_df, region_stats, seller_tiers, offers_df, cache_refreshed, bm_from, bm_to)

            progress.progress(88, text="Building shortlist...")
            shortlist = build_shortlist(payload)

            all_dq = snap_dq + bk_dq + build_dq
            if not all_dq:
                all_dq = ["No data quality issues detected."]

            st.session_state.payload = payload
            st.session_state.shortlist = shortlist
            st.session_state.dq_notes = all_dq
            st.session_state.last_updated = datetime.now().strftime("%d %b %Y %H:%M")

            progress.progress(100, text="Done!")
            st.success(f"✅ Dashboard generated — {payload['meta']['total_hotels']:,} hotels across {payload['meta']['total_regions']} regions, {len(shortlist)} shortlisted.")

    if st.session_state.payload:
        st.divider()
        st.subheader("Current Dashboard")
        m = st.session_state.payload["meta"]
        cols = st.columns(5)
        for col, (val, lbl) in zip(cols, [
            (f"{m['total_hotels']:,}", "Hotels"),
            (m["total_regions"], "Regions"),
            (m["hotels_with_offers"], "Active Offers"),
            (m["explorer_flags"]["expiring_soon_count"], "Expiring Soon"),
            (len(st.session_state.shortlist), "Shortlisted"),
        ]):
            col.metric(lbl, val)

        # Download JSON
        st.download_button(
            "⬇️ Download dashboard_data.json",
            data=json.dumps(st.session_state.payload, indent=2),
            file_name="dashboard_data.json",
            mime="application/json",
        )


# ── Tab 2: Hotel Explorer ─────────────────────────────────────────────────────
with tab_explorer:
    if not st.session_state.payload:
        st.info("Upload files and generate the dashboard first.")
    else:
        payload = st.session_state.payload
        flags = payload["meta"]["explorer_flags"]

        # Guidance chips (rendered as info boxes)
        chip_cols = st.columns(6)
        chip_idx = 0
        if flags["expiring_soon_count"] > 0:
            chip_cols[chip_idx % 6].error(f"⚡ {flags['expiring_soon_count']} expiring soon")
            chip_idx += 1
        for d in flags["top_offer_destinations"][:2]:
            chip_cols[chip_idx % 6].warning(f"🏷️ {d} offers")
            chip_idx += 1
        for r in flags["top_seller_regions"][:2]:
            chip_cols[chip_idx % 6].info(f"⭐ Hot: {r.split(' - ')[0]}")
            chip_idx += 1
        for r in flags["best_value_regions"][:1]:
            chip_cols[chip_idx % 6].success(f"💰 Value: {r.split(' - ')[0]}")
            chip_idx += 1

        st.divider()

        # Filters
        fc1, fc2, fc3, fc4 = st.columns([3, 2, 1.5, 1.5])
        search_q = fc1.text_input("Search hotels, regions, destinations", placeholder="e.g. Maldives, Barbados...", label_visibility="collapsed")
        macros = ["All"] + sorted(set(payload["data"].keys()))
        macro_sel = fc2.selectbox("Macro-region", macros, label_visibility="collapsed")
        sort_mode = fc3.selectbox("Sort", ["Recommended", "Price ↑", "Stars ↓"], label_visibility="collapsed")
        offers_only = fc4.checkbox("Offers only")

        all_regions = []
        for macro, regions in payload["data"].items():
            for rname, rdata in regions.items():
                if macro_sel != "All" and macro != macro_sel:
                    continue
                hotels = rdata.get("hotels", [])
                if search_q:
                    q = search_q.lower()
                    hotels = [h for h in hotels if q in h["h"].lower() or q in h["r"].lower() or q in h["c"].lower()]
                if offers_only:
                    hotels = [h for h in hotels if h.get("offer")]
                if not hotels:
                    continue
                # Sort
                if sort_mode == "Price ↑":
                    hotels = sorted(hotels, key=lambda h: h["p"])
                elif sort_mode == "Stars ↓":
                    hotels = sorted(hotels, key=lambda h: h["s"], reverse=True)
                else:
                    hotels = sorted(hotels, key=lambda h: (
                        (h.get("offer") and 400 or 0) +
                        (h.get("offer") and h["offer"].get("expiring_soon") and 150 or 0) +
                        {1:300,2:200,3:100}.get(h["seller_tier"],0) +
                        40*h["score"] + min(rdata.get("bookings_6w") or 0, 100)
                    ), reverse=True)
                all_regions.append((rname, rdata, macro, hotels))

        st.caption(f"Showing {len(all_regions)} regions")

        for rname, rdata, macro, hotels in all_regions[:40]:
            with st.expander(f"**{rname}** — {macro} · {len(hotels)} hotels" +
                             (f" · 📈 {rdata['bookings_6w']} bkgs (6w)" if rdata.get('bookings_6w') else "") +
                             (f" · Med £{round(rdata['median_rev_pp'])}" if rdata.get('median_rev_pp') else "")):
                h_cols = st.columns(3)
                for i, h in enumerate(hotels[:12]):
                    with h_cols[i % 3]:
                        tier_cls = {1: "tier1", 2: "tier2", 3: "tier3"}.get(h["seller_tier"], "")
                        offer_cls = "has-offer" if h.get("offer") else ""
                        badges = ""
                        if h["seller_tier"] in (1, 2, 3):
                            badges += f'<span class="badge badge-tier{h["seller_tier"]}">Tier {h["seller_tier"]}</span>'
                        if h["score"] == 5:
                            badges += '<span class="badge badge-score5">Exceptional</span>'
                        elif h["score"] == 4:
                            badges += '<span class="badge badge-score4">Good value</span>'
                        if h.get("offer"):
                            exp = h["offer"].get("expiring_soon")
                            badges += f'<span class="badge {"badge-exp" if exp else "badge-offer"}">{"⚡ Expiring" if exp else "Offer"}</span>'
                        offer_html = ""
                        if h.get("offer"):
                            exp_cls = "expiring" if h["offer"].get("expiring_soon") else ""
                            offer_html = f'''<div class="offer-box {exp_cls}">
                                <b>{h["offer"].get("type","")}</b><br>
                                {h["offer"].get("summary","")[:100]}
                                {"<br><b>Book by: " + h["offer"]["book_to"] + "</b>" if h["offer"].get("book_to") else ""}
                            </div>'''
                        st.markdown(f'''<div class="hotel-card {tier_cls} {offer_cls}">
                            <div style="font-weight:600;font-size:13px;color:#0E2841;margin-bottom:4px">{h["h"]}</div>
                            <div style="font-size:18px;font-weight:700;color:#0A7C4E">
                                £{round(h["p"])} <span style="font-size:11px;color:#8896A8">{h["b"]}</span>
                            </div>
                            <div style="font-size:11px;color:#8896A8">{"★"*h["s"]} · {h["d"]}</div>
                            <div style="margin-top:6px">{badges}</div>
                            {offer_html}
                        </div>''', unsafe_allow_html=True)
                if len(hotels) > 12:
                    st.caption(f"+ {len(hotels)-12} more hotels — refine search to see more")


# ── Tab 3: Email Shortlist ────────────────────────────────────────────────────
with tab_shortlist:
    if not st.session_state.shortlist:
        st.info("Generate the dashboard to see the shortlist.")
    else:
        sl = st.session_state.shortlist
        st.subheader(f"Weekly Email Shortlist — {len(sl)} hotels")

        rows = []
        for r in sl:
            tier_label = {1: "🟣 T1", 2: "🔵 T2", 3: "⚫ T3"}.get(r["seller_tier"], "—")
            score_label = {5: "⭐ Exceptional", 4: "✅ Good value", 3: "🟡 Fair"}.get(r["score"], str(r["score"]))
            urgent = "⚡ " if r.get("expiring_soon") else ""
            rows.append({
                "#": r["rank"],
                "Hotel": r["hotel"],
                "Region": r["region"],
                "Board": r["board"],
                "Price": f"£{round(r['price'])}",
                "Median": f"£{round(r['median'])}" if r.get("median") else "—",
                "Hist. Bkgs": r["bookings_total"],
                "Tier": tier_label,
                "Score": score_label,
                "Offer": f"{urgent}{r['offer_summary'][:60]}..." if r.get("has_offer") and r["offer_summary"] else "",
                "Book By": f"{urgent}{r['book_to']}" if r.get("book_to") else "—",
                "Rationale": r["why"],
            })

        df_sl = pd.DataFrame(rows)

        def highlight_urgent(row):
            if "⚡" in str(row.get("Book By", "")):
                return ["background-color:#FEF2F2"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_sl.style.apply(highlight_urgent, axis=1),
            use_container_width=True, hide_index=True
        )

        # CSV download
        st.download_button(
            "⬇️ Download shortlist CSV",
            data=df_sl.to_csv(index=False),
            file_name="shg_shortlist.csv",
            mime="text/csv",
        )


# ── Tab 4: Data Quality ───────────────────────────────────────────────────────
with tab_dq:
    if not st.session_state.dq_notes:
        st.info("Generate the dashboard to see data quality notes.")
    else:
        st.subheader("Data Quality Notes")
        for note in st.session_state.dq_notes:
            if "No data quality" in note:
                st.success(note)
            elif any(w in note.lower() for w in ["error", "missing", "unmatched", "unmapped"]):
                st.warning(note)
            else:
                st.info(note)

        if st.session_state.payload:
            m = st.session_state.payload["meta"]
            st.divider()
            st.caption(f"Generated: {m['generated_at']} · Benchmark: {m['benchmark_from']} → {m['benchmark_to']}")
