import streamlit as st
import pandas as pd
import numpy as np
import json
import re
from datetime import datetime, date, timedelta

st.set_page_config(page_title="SHG D2 Weekly Dashboard", page_icon="🏨", layout="wide")

st.markdown("""
<style>
:root{--navy:#1B1464;--gold:#D4AF37;--green:#0A7C4E;--amber:#C17A00;--red:#C0392B;}
[data-testid="stAppViewContainer"]{background:#F7F8FC;}
.hotel-card{background:#fff;border:1px solid #E8EAF0;border-radius:8px;padding:14px 16px;margin-bottom:10px;}
.hotel-card.tier1{border-left:4px solid #7c3aed;}
.hotel-card.tier2{border-left:4px solid #0e6b85;}
.hotel-card.tier3{border-left:4px solid #4b5563;}
.hotel-card.has-offer{border-top:2px solid #D4AF37;}
.badge{display:inline-block;font-size:10px;font-weight:600;padding:2px 8px;border-radius:3px;margin-right:4px;}
.badge-tier1{background:#F3EEFF;color:#7c3aed;}
.badge-tier2{background:#E6F4F8;color:#0e6b85;}
.badge-tier3{background:#F3F4F6;color:#4b5563;}
.badge-offer{background:#D4AF37;color:#412402;}
.badge-exp{background:#FEF2F2;color:#C0392B;border:1px solid #FCA5A5;}
.badge-score5{background:#F0FBF5;color:#0A7C4E;}
.badge-score4{background:#FFFBEB;color:#C17A00;}
.badge-sent{background:#E0E7FF;color:#3730A3;border:1px solid #A5B4FC;}
.badge-alt{background:#ECFDF5;color:#065F46;border:1px solid #6EE7B7;}
.sent-box{background:#EEF2FF;border-left:3px solid #6366F1;padding:6px 10px;border-radius:0 6px 6px 0;font-size:11px;color:#3730A3;margin-top:6px;}
.alt-row td{background:#ECFDF5 !important;}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
DEST_MAP = {
    "heraklion - greece":"Crete (Heraklion) - Greece","chania - greece":"Crete (Chania) - Greece",
    "kerkyra - greece":"Corfu - Greece","kos - greece":"Kos - Greece",
    "rhodes - greece":"Rhodes - Greece","zakynthos - greece":"Zante - Greece",
    "thira - greece":"Santorini - Greece","mikonos - greece":"Mykonos - Greece",
    "thessaloniki - greece":"Halkidiki - Greece","kavala - greece":"Halkidiki - Greece",
    "kefallinia - greece":"Kefalonia - Greece","skiathos - greece":"Skiathos - Greece",
    "kalamata - greece":"Kalamata - Greece","preveza lefkas - greece":"Lefkas - Greece",
    "preveza/lefkas - greece":"Lefkas - Greece","athens - greece":"Athens - Greece",
    "phuket - thailand":"Phuket - Thailand","koh lanta - thailand":"Koh Lanta - Thailand",
    "koh samui - thailand":"Koh Samui - Thailand","krabi - thailand":"Krabi - Thailand",
    "bangkok - thailand":"Bangkok - Thailand","chiang mai - thailand":"Chiang Mai - Thailand",
    "dubai - united arab emirates":"Dubai - United Arab Emirates",
    "abu dhabi - united arab emirates":"Abu Dhabi - United Arab Emirates",
    "ras al khaimah - united arab emirates":"Ras al Khaimah - United Arab Emirates",
    "male - maldives":"Maldives - Indian Ocean","mauritius - mauritius":"Mauritius - Indian Ocean",
    "mahe island - seychelles":"Seychelles - Indian Ocean","colombo - sri lanka":"Sri Lanka - Indian Ocean",
    "doha - qatar":"Doha - Qatar","muscat - oman":"Muscat - Oman","salalah - oman":"Salalah - Oman",
    "antalya - turkey":"Antalya - Turkey","bodrum - turkey":"Bodrum - Turkey",
    "dalaman - turkey":"Dalaman - Turkey","cancun - mexico":"All Resorts inc Cancun - Mexico",
    "punta cana - dominican republic":"Dominican Republic South East - Caribbean",
    "barbados - barbados":"Barbados - Caribbean","st lucia - saint lucia":"Saint Lucia - Caribbean",
    "antigua - antigua and barbuda":"Antigua - Caribbean",
    "kingston - jamaica":"Jamaica - Caribbean","montego bay - jamaica":"Jamaica - Caribbean",
    "tenerife - spain - canaries":"Tenerife Spain - Canaries",
    "gran canaria - spain - canaries":"Gran Canaria Spain - Canaries",
    "lanzarote - spain - canaries":"Lanzarote Spain - Canaries",
    "fuerteventura - spain - canaries":"Fuerteventura Spain - Canaries",
    "palma mallorca - spain - balearics":"Majorca Spain - Balearics",
    "ibiza - spain - balearics":"Ibiza Spain - Balearics",
    "menorca - spain - balearics":"Menorca Spain - Balearics",
    "malaga - spain - mainland":"Costa Del Sol - Spain",
    "alicante - spain - mainland":"Costa Blanca (Benidorm, Alicante) - Spain",
    "goa - india":"Goa - India","denpasar bali - indonesia":"Bali - Indonesia",
    "faro - portugal":"Algarve - Portugal","funchal - portugal":"Madeira - Portugal",
    "larnaca - cyprus":"Larnaca - Cyprus","paphos - cyprus":"Paphos - Cyprus",
    "marrakech - morocco":"Marrakech - Morocco","agadir - morocco":"Agadir - Morocco",
    "hurghada - egypt":"Hurghada - Egypt","sharm el sheikh - egypt":"Sharm El Sheikh - Egypt",
    "zanzibar - tanzania":"Zanzibar - Tanzania","dubrovnik - croatia":"Dubrovnik - Croatia",
    "malta - malta":"Malta","cape town - south africa":"Cape Town - South Africa",
    "singapore - singapore":"Singapore - Singapore","da nang - viet nam":"Danang - Vietnam",
    "hanoi - viet nam":"Hanoi - Vietnam","ho chi minh city - viet nam":"Ho Chi Minh City - Vietnam",
    "tokyo - japan":"Tokyo - Japan","las vegas - united states":"Las Vegas - United States",
    "new york ny - united states":"New York - United States",
    "orlando fl - united states":"Orlando Florida - United States",
}

MACRO_MAP = {
    "Greece":"Mediterranean","Turkey":"Mediterranean","Cyprus":"Mediterranean",
    "Croatia":"Mediterranean","Malta":"Mediterranean","Italy":"Mediterranean",
    "Spain":"Mediterranean","Portugal":"Mediterranean","Bulgaria":"Mediterranean","Egypt":"Mediterranean",
    "Canaries":"Africa & Canaries","Morocco":"Africa & Canaries",
    "South Africa":"Africa & Canaries","Tanzania":"Africa & Canaries",
    "United Arab Emirates":"Middle East & Indian Ocean","Qatar":"Middle East & Indian Ocean",
    "Oman":"Middle East & Indian Ocean","Bahrain":"Middle East & Indian Ocean",
    "Indian Ocean":"Middle East & Indian Ocean","Maldives":"Middle East & Indian Ocean",
    "Thailand":"Asia Pacific","Indonesia":"Asia Pacific","India":"Asia Pacific",
    "Malaysia":"Asia Pacific","Singapore":"Asia Pacific","Vietnam":"Asia Pacific",
    "Japan":"Asia Pacific","HongKong":"Asia Pacific",
    "Caribbean":"Caribbean & Americas","Mexico":"Caribbean & Americas",
    "United States":"Caribbean & Americas","Jamaica":"Caribbean & Americas","Barbados":"Caribbean & Americas",
}

TODAY = date.today()

for k, v in [("payload",None),("shortlist",[]),("dq_notes",[]),("last_updated",None),("sent_log",{})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────────────────────
def norm_col(s):
    return str(s).lower().strip().replace(" ","").replace("_","").replace("-","")

def safe_str_series(series):
    """Convert a pandas Series to plain Python str dtype, killing Arrow backing."""
    return series.astype(object).fillna("").apply(str).str.strip()

def get_macro(region_str):
    for k, v in MACRO_MAP.items():
        if k.lower() in str(region_str).lower():
            return v
    return "Other"

def parse_offer_date(val):
    if not val or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        return pd.to_datetime(val, dayfirst=True).date()
    except Exception:
        return None

def parse_sent_log(df):
    """Returns dict keyed by giata (str) → list of sent records."""
    df = df.copy()
    df.columns = pd.Index([str(c).strip() for c in df.columns])
    rename = {}
    aliases = {
        "giata":       ["giata","Giata","GIATA"],
        "name":        ["name","Name","HotelName"],
        "region":      ["region","Region"],
        "date_sent":   ["datesentinemaileoffers","date sent in email offers","datesent","DateSentInEmailOffers"],
        "price_sent":  ["pricesentat","price sent at","PriceSentAt"],
        "board":       ["boardused","board used","BoardUsed"],
        "url":         ["url","URL"],
    }
    used = set()
    for col in df.columns:
        cn = norm_col(col)
        for target, als in aliases.items():
            if target in used:
                continue
            if cn in [norm_col(a) for a in als]:
                rename[col] = target
                used.add(target)
                break
    df = df.rename(columns=rename)
    if "giata" not in df.columns:
        return {}
    df["giata"] = safe_str_series(df["giata"]).str.replace(r"\.0$","",regex=True).replace("nan","")
    log = {}
    for _, row in df.iterrows():
        g = str(row.get("giata","")).strip()
        if not g or g == "nan":
            continue
        entry = {
            "name":       str(row.get("name","")).strip(),
            "region":     str(row.get("region","")).strip(),
            "date_sent":  str(row.get("date_sent","")).strip(),
            "price_sent": str(row.get("price_sent","")).strip(),
            "board":      str(row.get("board","")).strip(),
            "url":        str(row.get("url","")).strip(),
        }
        log.setdefault(g, []).append(entry)
    return log


    if not val or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        return pd.to_datetime(val, dayfirst=True).date()
    except Exception:
        return None

# ── process_snapshot ──────────────────────────────────────────────────────────
def process_snapshot(raw_df):
    dq = []
    df = raw_df.copy()

    # Normalise column names
    df.columns = pd.Index([str(c).strip() for c in df.columns])

    col_targets = {
        "Name":         ["name","hotelname","hotelnames"],
        "Region":       ["destination","hermesdestination"],
        "SearchDestId": ["destid","searchdestinationid"],
        "Giata":        ["giata"],
        "Stars":        ["starrating","star rating","stars"],
        "Price":        ["cheapestprice","cheapest price","price"],
        "Board":        ["cheapestboard","cheapest board","board","defaultbbstatic"],
        "PriceDate":    ["cheapestpricedate","cheapest price date","pricedate"],
        "Refreshed":    ["priceslastrefreshed","prices last refreshed"],
    }
    rename, used = {}, set()
    for col in df.columns:
        cn = norm_col(col)
        for target, aliases in col_targets.items():
            if target in used:
                continue
            if cn in [norm_col(a) for a in aliases]:
                rename[col] = target
                used.add(target)
                break
    df = df.rename(columns=rename)
    dq.append(f"Snapshot columns detected: {', '.join(df.columns.tolist()[:14])}")

    # Ensure all columns exist
    for col, default in [("Name",""),("Region",""),("Giata",""),("Stars",0),
                         ("Price",0),("Board",""),("PriceDate",""),("Refreshed","")]:
        if col not in df.columns:
            df[col] = default
            dq.append(f"Column '{col}' not found in snapshot.")

    # Fallback: if Region blank, use SearchDestId
    region_series = safe_str_series(df["Region"])
    if region_series.replace("","").str.strip().eq("").all():
        if "SearchDestId" in df.columns:
            region_series = safe_str_series(df["SearchDestId"]).str.replace(r"\.0$","",regex=True)
            dq.append("No Destination column found — using Search Destination Id as region.")
        else:
            region_series = pd.Series(["All Hotels"] * len(df))
    df["Region"] = region_series.replace("nan","")

    # Convert types — all via safe_str_series to avoid Arrow
    df["Name"]      = safe_str_series(df["Name"]).replace("nan","")
    df["Giata"]     = safe_str_series(df["Giata"]).str.replace(r"\.0$","",regex=True).replace("nan","")
    df["Board"]     = safe_str_series(df["Board"]).replace("nan","")
    df["PriceDate"] = safe_str_series(df["PriceDate"]).str[:10].replace("nan","")
    df["Price"]     = pd.to_numeric(df["Price"], errors="coerce").fillna(0)
    df["Stars"]     = pd.to_numeric(df["Stars"], errors="coerce").fillna(0).astype(int)

    # Country from Region — fully vectorised, no apply/lambda
    df["Country"] = df["Region"].str.split(" - ").str[-1].where(
        df["Region"].str.contains(" - ", regex=False), df["Region"]
    )

    df = df[df["Price"] > 0].copy()
    df = df[df["Region"].str.len() > 0].copy()

    before = len(df)
    df = df.drop_duplicates(subset=["Name","Region"], keep="first")
    removed = before - len(df)
    if removed:
        dq.append(f"Removed {removed} duplicate hotels.")

    cache_refreshed = ""
    try:
        cache_refreshed = pd.to_datetime(df["Refreshed"], errors="coerce").max().strftime("%d %b %Y")
    except Exception:
        pass

    dq.append(f"Snapshot loaded: {len(df)} hotels across {df['Region'].nunique()} regions.")
    df = df.sort_values(["Region","Price"])
    return df, dq, cache_refreshed

# ── process_bookings ──────────────────────────────────────────────────────────
def process_bookings(raw_df):
    dq = []
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(), dq, None, None, {}

    df = raw_df.copy()
    df.columns = pd.Index([str(c).strip() for c in df.columns])

    col_aliases = {
        "BookedDate":   ["bookeddate","bookdate","booked date","createdate","createddate","bookingdate"],
        "FolderStatus": ["folderstatus","folder status","status","bookingstatus"],
        "ProdMix":      ["prodmix","productmix","prod mix"],
        "FolderPax":    ["folderpax","folder pax","pax","passengers","totalpax"],
        "KPIRevenue":   ["kpirevenue","kpi revenue","revenue","totalrevenue","sellingprice"],
        "KPIProfit":    ["kpiprofit","kpi profit","profit","totalprofit","margin"],
        "HotelName":    ["hotelname","hotel name","hotel","hotelnames"],
        "Destination":  ["destination","destname","hermesdestination","destinationname","resort"],
        "DestCountry":  ["destcountry","dest country","country","countryname"],
    }
    rename, used = {}, set()
    for col in df.columns:
        cn = norm_col(col)
        for target, aliases in col_aliases.items():
            if target in used:
                continue
            if cn in [norm_col(a) for a in aliases]:
                rename[col] = target
                used.add(target)
                break
    df = df.rename(columns=rename)

    if "BookedDate" not in df.columns:
        dq.append("BookedDate column not found — skipping bookings.")
        return pd.DataFrame(), dq, None, None, {}

    df["BookedDate"] = pd.to_datetime(df["BookedDate"], errors="coerce")
    df = df.dropna(subset=["BookedDate"])
    if df.empty:
        return pd.DataFrame(), dq, None, None, {}

    if "FolderStatus" in df.columns:
        df = df[safe_str_series(df["FolderStatus"]).str.upper().isin({"AUTH","PROV","OPS"})]
    if "ProdMix" in df.columns:
        df = df[safe_str_series(df["ProdMix"]).str.lower() == "mixed"]

    for col, default in [("FolderPax",1),("KPIRevenue",0),("KPIProfit",0)]:
        if col not in df.columns:
            df[col] = default
    df["FolderPax"]  = pd.to_numeric(df["FolderPax"],  errors="coerce").fillna(0)
    df["KPIRevenue"] = pd.to_numeric(df["KPIRevenue"], errors="coerce").fillna(0)
    df["KPIProfit"]  = pd.to_numeric(df["KPIProfit"],  errors="coerce").fillna(0)
    df = df[df["FolderPax"] > 0]
    df["rev_pp"]    = df["KPIRevenue"] / df["FolderPax"]
    df["profit_pp"] = df["KPIProfit"]  / df["FolderPax"]

    # Destination mapping — fully vectorised
    dest_col    = "Destination" if "Destination" in df.columns else None
    country_col = "DestCountry" if "DestCountry" in df.columns else None
    unmapped = set()

    if dest_col:
        d_series = safe_str_series(df[dest_col]).str.lower()
        c_series = safe_str_series(df[country_col]).str.lower() if country_col else pd.Series([""] * len(df), index=df.index)
        df["_dest_key"] = d_series + " - " + c_series
        df["mapped_region"] = df["_dest_key"].map(DEST_MAP)
        for k in df[df["mapped_region"].isna()]["_dest_key"].unique()[:10]:
            if k and k.strip(" -"):
                unmapped.add(k)
    else:
        df["mapped_region"] = None
        dq.append("No destination column found in bookings.")

    if unmapped:
        dq.append(f"Unmapped booking destinations ({len(unmapped)}): {', '.join(list(unmapped)[:5])}")

    dq.append(f"Bookings loaded: {len(df)} valid rows.")
    max_date = df["BookedDate"].max().date()
    min_date = (df["BookedDate"].max() - pd.Timedelta(weeks=6)).date()

    # Build dest_id → name map
    dest_id_map = {}
    dest_id_col = next((c for c in df.columns if norm_col(c) in ["destid","searchdestinationid"]), None)
    if dest_id_col and dest_col:
        for did, dname in zip(safe_str_series(df[dest_id_col]).str.replace(r"\.0$","",regex=True),
                              safe_str_series(df[dest_col])):
            if did and dname and did != "nan" and dname != "nan":
                dest_id_map[did] = dname

    return df, dq, min_date, max_date, dest_id_map

# ── Compute stats ─────────────────────────────────────────────────────────────
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
    tiers = {}
    if bookings_df.empty or "mapped_region" not in bookings_df.columns:
        return tiers
    hotel_col = "HotelName" if "HotelName" in bookings_df.columns else next(
        (c for c in bookings_df.columns if "hotel" in c.lower()), None)
    if not hotel_col:
        return tiers
    valid = bookings_df[bookings_df["mapped_region"].notna()]
    for region, grp in valid.groupby("mapped_region"):
        counts = grp[hotel_col].value_counts()
        total  = counts.sum()
        cum, region_tiers = 0, {}
        for i, (name, cnt) in enumerate(counts.items()):
            cum += cnt
            share = cum / total
            t = 1 if (share <= 0.40 and i < 5) else 2 if share <= 0.75 else 3
            region_tiers[re.sub(r"[^\w\s]","",str(name).lower()).strip()] = {"tier":t,"count":int(cnt)}
        tiers[region] = region_tiers
    return tiers

def value_score(price, stats):
    if not stats or stats.get("median_rev_pp") is None:
        return 1, "no_data"
    p25 = stats.get("p25_rev_pp") or 0
    med = stats.get("median_rev_pp") or 0
    p75 = stats.get("p75_rev_pp") or 0
    if price <= p25:   return 5, "exceptional"
    elif price <= med: return 4, "good_value"
    elif price <= p75: return 3, "fair"
    else:              return 2, "above_typical"

def normalise_offers(df):
    df = df.copy()
    df.columns = pd.Index([str(c).strip() for c in df.columns])
    col_aliases = {
        "giata":        ["giata","GIATA"],
        "hotel":        ["hotel","hotelname","hotel name","Hotel Name"],
        "summary":      ["tacticalofferdetails","TacticalOfferDetails","offer_details","details"],
        "travel_from":  ["travelfrom","TravelFrom","travel from"],
        "travel_to":    ["travelto","TravelTo","travel to"],
        "booking_from": ["bookingfrom","BookingFrom","booking from"],
        "booking_to":   ["bookingto","BookingTo","booking to"],
        "type":         ["offertype","OfferType","offertypename","OfferTypeName","type"],
        "category":     ["offertypecategory","OfferTypeCategory"],
    }
    rename, used = {}, set()
    for col in df.columns:
        cn = norm_col(col)
        for target, aliases in col_aliases.items():
            if target in used:
                continue
            if cn in [norm_col(a) for a in aliases]:
                rename[col] = target
                used.add(target)
                break
    df = df.rename(columns=rename)
    if "giata" in df.columns:
        df["giata"] = safe_str_series(df["giata"]).str.replace(r"\.0$","",regex=True).replace("nan","")
    return df

# ── build_payload ─────────────────────────────────────────────────────────────
def build_payload(snap_df, region_stats, seller_tiers, offers_df, cache_refreshed, bm_from, bm_to, dest_id_map=None):
    dq = []
    dest_id_map = dest_id_map or {}

    # Build offers maps
    offers_map, offers_name_map = {}, {}
    unmatched_giatas = 0
    if offers_df is not None and not offers_df.empty:
        offers_df = normalise_offers(offers_df)
        for _, row in offers_df.iterrows():
            g = str(row.get("giata","")).strip()
            booking_to = parse_offer_date(row.get("booking_to"))
            is_active  = (booking_to is None) or (booking_to >= TODAY)
            if not is_active:
                continue
            expiring = booking_to is not None and (booking_to - TODAY).days <= 7
            summary  = str(row.get("summary",""))
            tags = [t for t in ["discount","room upgrade","board upgrade","kids free",
                                 "free nights","transfers","resort credit"] if t in summary.lower()]
            offer_obj = {
                "summary": summary,
                "type":    str(row.get("type","")),
                "tags":    tags,
                "travel_to":    str(row.get("travel_to","")) if pd.notna(row.get("travel_to","")) else "",
                "book_to":      booking_to.strftime("%d %b %Y") if booking_to else "",
                "book_to_date": booking_to,
                "expiring_soon": expiring,
            }
            if g and g != "nan":
                offers_map[g] = offer_obj
            hotel_name = str(row.get("hotel","")).strip()
            if hotel_name:
                offers_name_map[re.sub(r"[^\w]","",hotel_name.lower())] = offer_obj

    data = {}
    hotels_with_offers = 0

    for region in snap_df["Region"].unique():
        rdf    = snap_df[snap_df["Region"] == region]
        country = str(rdf["Country"].iloc[0]) if len(rdf) else ""

        # Enrich numeric region ID with name from dest_id_map
        region_str = str(region).strip()
        region_label = dest_id_map.get(region_str, region_str)
        macro  = get_macro(region_label)
        stats  = region_stats.get(region_label, region_stats.get(region_str, {}))
        rtiers = seller_tiers.get(region_label, seller_tiers.get(region_str, {}))

        if macro not in data:
            data[macro] = {}

        hotels = []
        for _, row in rdf.iterrows():
            name       = str(row.get("Name","")).strip()
            giata      = str(row.get("Giata","")).strip()
            price      = float(row.get("Price",0))
            stars      = int(row.get("Stars",0))
            board      = str(row.get("Board",""))
            price_date = str(row.get("PriceDate",""))[:10]

            norm_name  = re.sub(r"[^\w\s]","",name.lower()).strip()
            tier_info  = rtiers.get(norm_name) or rtiers.get(name.lower())
            if tier_info:
                tier, bkgs_total = tier_info["tier"], tier_info["count"]
            elif rtiers:
                tier, bkgs_total = 0, 0
            else:
                tier, bkgs_total = -1, 0

            score, value_tag = value_score(price, stats)

            offer = offers_map.get(giata)
            if not offer:
                offer = offers_name_map.get(re.sub(r"[^\w]","",name.lower()))
            if offer:
                hotels_with_offers += 1
                offer_out = {k:v for k,v in offer.items() if k != "book_to_date"}
            else:
                if giata and giata != "nan" and offers_map:
                    unmatched_giatas += 1
                offer_out = None

            hotels.append({
                "h":name,"giata":giata,"s":stars,"r":region_label,
                "c":country,"p":round(price,2),"b":board,"d":price_date,
                "seller_tier":tier,"bookings_total":bkgs_total,
                "bookings_6w":stats.get("bookings_6w",0),
                "score":score,"value_tag":value_tag,"offer":offer_out,
            })

        data[macro][region_label] = {
            "bookings_6w":    stats.get("bookings_6w",0),
            "median_rev_pp":  stats.get("median_rev_pp"),
            "avg_rev_pp":     stats.get("avg_rev_pp"),
            "p25_rev_pp":     stats.get("p25_rev_pp"),
            "p75_rev_pp":     stats.get("p75_rev_pp"),
            "avg_profit_pp":  stats.get("avg_profit_pp"),
            "total_profit_6w":stats.get("total_profit_6w"),
            "hotels": hotels,
        }

    if unmatched_giatas:
        dq.append(f"Offer GIATAs with no price snapshot match: {unmatched_giatas}")

    all_hotels_flat = [h for m in data.values() for r in m.values() for h in r["hotels"]]
    expiring_count  = sum(1 for h in all_hotels_flat if h.get("offer") and h["offer"].get("expiring_soon"))

    top_offer = sorted([h for h in all_hotels_flat if h.get("offer")],
                       key=lambda h:(h["offer"].get("expiring_soon",False),h["score"]),reverse=True)
    top_offer_dest = list(dict.fromkeys([h["c"] for h in top_offer]))[:3]

    top_seller = sorted(
        [(rn,rd.get("bookings_6w",0)) for m in data.values() for rn,rd in m.items()],
        key=lambda x:x[1],reverse=True)[:3]
    best_value = sorted(
        [(rn,sum(1 for h in rd["hotels"] if h["score"]>=5)) for m in data.values() for rn,rd in m.items()],
        key=lambda x:x[1],reverse=True)[:3]

    meta = {
        "generated_at":   datetime.utcnow().isoformat(),
        "cache_refreshed":cache_refreshed,
        "benchmark_from": str(bm_from) if bm_from else "",
        "benchmark_to":   str(bm_to)   if bm_to   else "",
        "total_hotels":   len(all_hotels_flat),
        "total_regions":  sum(len(v) for v in data.values()),
        "hotels_with_offers": hotels_with_offers,
        "explorer_flags": {
            "top_offer_destinations": top_offer_dest,
            "expiring_soon_count":    expiring_count,
            "top_seller_regions":     [r[0] for r in top_seller],
            "best_value_regions":     [r[0] for r in best_value],
            "new_bookable_regions":   [],
        }
    }
    return {"meta":meta,"data":data}, dq

# ── build_shortlist ───────────────────────────────────────────────────────────
def build_shortlist(payload, sent_log=None):
    sent_log = sent_log or {}
    all_hotels = [(h,rdata,rname)
                  for macro in payload["data"].values()
                  for rname,rdata in macro.items()
                  for h in rdata["hotels"]]

    def priority(h, reg):
        has_offer = 1 if h.get("offer") else 0
        expiring  = 1 if h.get("offer") and h["offer"].get("expiring_soon") else 0
        tier_sc   = {1:300,2:200,3:100}.get(h["seller_tier"],0)
        bkgs6w    = min(reg.get("bookings_6w") or 0, 100)
        bkgs_tot  = min(h.get("bookings_total") or 0, 75)
        med       = reg.get("median_rev_pp") or 0
        p25       = reg.get("p25_rev_pp") or 0
        pct_med   = max(0,(med - h["p"])/med*100) if med else 0
        pct_p25   = max(0,(p25 - h["p"])/p25*100) if p25 else 0
        return has_offer*400+expiring*150+tier_sc+40*h["score"]+bkgs6w+bkgs_tot+min(pct_med,50)+min(pct_p25,25)

    def make_row(h, reg, rname, rank, is_alt=False, alt_for=None):
        med = reg.get("median_rev_pp")
        below_med = round((med-h["p"])/med*100,1) if med and med>0 else None
        offer = h.get("offer") or {}
        prev = sent_log.get(h["giata"], [])
        last_sent = prev[-1] if prev else None
        return {
            "rank": rank,
            "hotel": h["h"], "region": rname, "country": h["c"],
            "board": h["b"], "price": h["p"],
            "price_date": h.get("d",""), "median": med,
            "bookings_total": h["bookings_total"],
            "region_bkgs": reg.get("bookings_6w",0),
            "seller_tier": h["seller_tier"], "score": h["score"],
            "has_offer": bool(offer),
            "offer_type": offer.get("type",""),
            "offer_summary": offer.get("summary",""),
            "book_to": offer.get("book_to",""),
            "travel_to": offer.get("travel_to",""),
            "expiring_soon": offer.get("expiring_soon",False),
            "below_median_pct": below_med, "priority": round(priority(h,reg)),
            "previously_sent": bool(last_sent),
            "last_sent_date": last_sent["date_sent"] if last_sent else "",
            "last_sent_price": last_sent["price_sent"] if last_sent else "",
            "is_alternative": is_alt,
            "alt_for": alt_for or "",
            "why": (f"{'[OFFER] '+offer.get('type','') +' · ' if offer else ''}"
                    f"{'⚠️ PREV SENT ' + (last_sent['date_sent'] if last_sent else '') + ' · ' if last_sent else ''}"
                    f"{'🔄 ALT for '+alt_for+' · ' if is_alt else ''}"
                    f"Tier {h['seller_tier']} · {h['value_tag'].replace('_',' ').title()} vs median · {rname}"),
        }

    for score_thresh in [4, 3]:
        candidates = []
        for h, reg, rname in all_hotels:
            if (h["seller_tier"] in {1,2,3} and h["score"] >= score_thresh) or h.get("offer"):
                candidates.append((priority(h,reg), h, reg, rname))
        candidates.sort(key=lambda x:x[0], reverse=True)

        for cap in [2, 3]:
            region_count, country_count, result = {}, {}, []
            # Track which regions need an alternative (because selected hotel was previously sent)
            needs_alt = {}  # rname -> previously_sent hotel name

            for p, h, reg, rname in candidates:
                if region_count.get(rname,0) >= cap or country_count.get(h["c"],0) >= cap:
                    continue
                region_count[rname]  = region_count.get(rname,0) + 1
                country_count[h["c"]]= country_count.get(h["c"],0) + 1
                row = make_row(h, reg, rname, len(result)+1)
                result.append(row)
                if row["previously_sent"]:
                    needs_alt[rname] = h["h"]
                if len(result) >= 20:
                    break

            # Inject alternatives for previously-sent shortlist hotels
            alt_results = []
            for rname, sent_hotel_name in needs_alt.items():
                # Find best unsent candidate in same region not already in shortlist
                shortlisted_giatas = {r["hotel"] for r in result}
                for p, h, reg, rn in candidates:
                    if rn != rname:
                        continue
                    if h["h"] in shortlisted_giatas:
                        continue
                    if sent_log.get(h["giata"]):
                        continue  # also previously sent, skip
                    alt_row = make_row(h, reg, rname, 0, is_alt=True, alt_for=sent_hotel_name)
                    alt_results.append(alt_row)
                    break

            # Insert alt rows immediately after their paired previously-sent row
            final = []
            for row in result:
                final.append(row)
                if row["previously_sent"] and row["region"] in needs_alt:
                    matching_alts = [a for a in alt_results if a["alt_for"] == row["hotel"]]
                    for a in matching_alts:
                        a["rank"] = f"{row['rank']}b"
                        final.append(a)

            # Re-number
            for i, r in enumerate(final):
                if not r["is_alternative"]:
                    r["rank"] = i + 1

            if len(result) >= 20:
                break
        if len(result) >= 20:
            break
    return final
    all_hotels = [(h,rdata,rname)
                  for macro in payload["data"].values()
                  for rname,rdata in macro.items()
                  for h in rdata["hotels"]]

    def priority(h, reg):
        has_offer = 1 if h.get("offer") else 0
        expiring  = 1 if h.get("offer") and h["offer"].get("expiring_soon") else 0
        tier_sc   = {1:300,2:200,3:100}.get(h["seller_tier"],0)
        bkgs6w    = min(reg.get("bookings_6w") or 0, 100)
        bkgs_tot  = min(h.get("bookings_total") or 0, 75)
        med       = reg.get("median_rev_pp") or 0
        p25       = reg.get("p25_rev_pp") or 0
        pct_med   = max(0,(med - h["p"])/med*100) if med else 0
        pct_p25   = max(0,(p25 - h["p"])/p25*100) if p25 else 0
        return has_offer*400+expiring*150+tier_sc+40*h["score"]+bkgs6w+bkgs_tot+min(pct_med,50)+min(pct_p25,25)

    for score_thresh in [4, 3]:
        candidates = []
        for h, reg, rname in all_hotels:
            if (h["seller_tier"] in {1,2,3} and h["score"] >= score_thresh) or h.get("offer"):
                candidates.append((priority(h,reg), h, reg, rname))
        candidates.sort(key=lambda x:x[0], reverse=True)

        for cap in [2, 3]:
            region_count, country_count, result = {}, {}, []
            for p, h, reg, rname in candidates:
                if region_count.get(rname,0) >= cap or country_count.get(h["c"],0) >= cap:
                    continue
                region_count[rname]  = region_count.get(rname,0) + 1
                country_count[h["c"]]= country_count.get(h["c"],0) + 1
                med = reg.get("median_rev_pp")
                below_med = round((med-h["p"])/med*100,1) if med and med>0 else None
                offer = h.get("offer") or {}
                result.append({
                    "rank": len(result)+1, "hotel":h["h"], "region":rname,
                    "country":h["c"], "board":h["b"], "price":h["p"],
                    "price_date":h.get("d",""), "median":med,
                    "bookings_total":h["bookings_total"],
                    "region_bkgs":reg.get("bookings_6w",0),
                    "seller_tier":h["seller_tier"], "score":h["score"],
                    "has_offer":bool(offer),
                    "offer_type":offer.get("type",""),
                    "offer_summary":offer.get("summary",""),
                    "book_to":offer.get("book_to",""),
                    "travel_to":offer.get("travel_to",""),
                    "expiring_soon":offer.get("expiring_soon",False),
                    "below_median_pct":below_med, "priority":round(p),
                    "why":(f"{'[OFFER] '+offer.get('type','') +' · ' if offer else ''}"
                           f"Tier {h['seller_tier']} · {h['value_tag'].replace('_',' ').title()} vs median · {rname}"),
                })
                if len(result) >= 20:
                    break
            if len(result) >= 20:
                break
        if len(result) >= 20:
            break
    return result

# ── Header ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([3,1])
with c1:
    st.markdown('<div style="background:#1B1464;padding:16px 24px;border-radius:10px;margin-bottom:16px">'
                '<span style="color:#D4AF37;font-size:22px;font-weight:700">SHG // D2 Weekly Dashboard</span>'
                '</div>', unsafe_allow_html=True)
with c2:
    if st.session_state.last_updated:
        st.caption(f"Last updated: {st.session_state.last_updated}")
    if st.session_state.payload:
        st.caption(f"Prices refreshed: {st.session_state.payload['meta'].get('cache_refreshed','')}")

tab_upload, tab_explorer, tab_shortlist, tab_dq = st.tabs(
    ["📁 Upload & Generate","🏨 Hotel Explorer","📧 Email Shortlist","⚠️ Data Quality"])

# ── Tab 1: Upload ─────────────────────────────────────────────────────────────
with tab_upload:
    st.subheader("Upload Data Files")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**📊 Bookings Dataset**"); st.caption("Excel (.xlsx)")
        bk_file = st.file_uploader("Bookings", type=["xlsx"], label_visibility="collapsed", key="bk")
    with c2:
        st.markdown("**💰 Price Snapshot** *(required)*"); st.caption("Excel (.xlsx)")
        sn_file = st.file_uploader("Snapshot", type=["xlsx"], label_visibility="collapsed", key="sn")
    with c3:
        st.markdown("**🏷️ Special Offers**"); st.caption("CSV file")
        of_file = st.file_uploader("Offers", type=["csv"], label_visibility="collapsed", key="of")

    c4, c5 = st.columns([1,2])
    with c4:
        st.markdown("**📋 Previously Sent Offers Log**"); st.caption("Excel or CSV — tracks hotels already emailed")
        sl_file = st.file_uploader("Sent log", type=["xlsx","csv"], label_visibility="collapsed", key="sl")

    st.divider()
    if st.button("🚀 Generate Dashboard", type="primary", disabled=sn_file is None):
        with st.spinner("Processing files..."):
            prog = st.progress(0, text="Reading price snapshot...")

            snap_raw = pd.read_excel(sn_file, sheet_name=0, engine="openpyxl")
            # Try to load the named sheet if it exists
            try:
                xf = pd.ExcelFile(sn_file, engine="openpyxl")
                sheet = "D2 Price Snapshot" if "D2 Price Snapshot" in xf.sheet_names else xf.sheet_names[0]
                snap_raw = pd.read_excel(sn_file, sheet_name=sheet, engine="openpyxl")
            except Exception:
                pass
            snap_df, snap_dq, cache_refreshed = process_snapshot(snap_raw)
            prog.progress(25, text=f"Snapshot: {len(snap_df)} hotels loaded")

            bm_from = bm_to = None
            bookings_df = pd.DataFrame()
            bk_dq, dest_id_map = [], {}
            if bk_file:
                bk_raw = pd.read_excel(bk_file, engine="openpyxl")
                bookings_df, bk_dq, bm_from, bm_to, dest_id_map = process_bookings(bk_raw)
                prog.progress(45, text=f"Bookings: {len(bookings_df)} rows processed")
            else:
                bk_dq = ["No bookings file — seller tiers and benchmarks unavailable."]
                prog.progress(45)

            offers_df = None
            if of_file:
                offers_df = pd.read_csv(of_file)
                prog.progress(55, text=f"Offers: {len(offers_df)} rows loaded")
            else:
                prog.progress(55)

            sent_log = {}
            if sl_file:
                try:
                    sl_raw = pd.read_csv(sl_file) if sl_file.name.endswith(".csv") else pd.read_excel(sl_file, engine="openpyxl")
                    sent_log = parse_sent_log(sl_raw)
                    prog.progress(58, text=f"Sent log: {len(sent_log)} previously sent hotels loaded")
                except Exception as e:
                    st.warning(f"Could not parse sent log: {e}")
            st.session_state.sent_log = sent_log

            prog.progress(60, text="Computing region stats...")
            region_stats  = compute_region_stats(bookings_df, bm_from, bm_to) if not bookings_df.empty else {}
            seller_tiers  = compute_seller_tiers(bookings_df) if not bookings_df.empty else {}

            prog.progress(75, text="Building payload...")
            payload, build_dq = build_payload(snap_df, region_stats, seller_tiers,
                                               offers_df, cache_refreshed, bm_from, bm_to, dest_id_map)

            prog.progress(88, text="Building shortlist...")
            shortlist = build_shortlist(payload, sent_log)

            all_dq = snap_dq + bk_dq + build_dq
            if not all_dq:
                all_dq = ["No data quality issues detected."]

            st.session_state.payload      = payload
            st.session_state.shortlist    = shortlist
            st.session_state.dq_notes     = all_dq
            st.session_state.last_updated = datetime.now().strftime("%d %b %Y %H:%M")
            prog.progress(100, text="Done!")
            st.success(f"✅ Dashboard generated — {payload['meta']['total_hotels']:,} hotels, "
                       f"{payload['meta']['total_regions']} regions, {len(shortlist)} shortlisted.")

    if st.session_state.payload:
        st.divider()
        st.subheader("Current Dashboard")
        m = st.session_state.payload["meta"]
        cols = st.columns(5)
        for col,(val,lbl) in zip(cols,[
            (f"{m['total_hotels']:,}","Hotels"),(m["total_regions"],"Regions"),
            (m["hotels_with_offers"],"Active Offers"),
            (m["explorer_flags"]["expiring_soon_count"],"Expiring Soon"),
            (len(st.session_state.shortlist),"Shortlisted")]):
            col.metric(lbl, val)
        st.download_button("⬇️ Download dashboard_data.json",
            data=json.dumps(st.session_state.payload, indent=2),
            file_name="dashboard_data.json", mime="application/json")

# ── Tab 2: Hotel Explorer ─────────────────────────────────────────────────────
with tab_explorer:
    if not st.session_state.payload:
        st.info("Upload files and generate the dashboard first.")
    else:
        payload = st.session_state.payload
        flags   = payload["meta"]["explorer_flags"]

        chip_cols = st.columns(6)
        ci = 0
        if flags["expiring_soon_count"] > 0:
            chip_cols[ci%6].error(f"⚡ {flags['expiring_soon_count']} expiring soon"); ci+=1
        for d in flags["top_offer_destinations"][:2]:
            chip_cols[ci%6].warning(f"🏷️ {d} offers"); ci+=1
        for r in flags["top_seller_regions"][:2]:
            chip_cols[ci%6].info(f"⭐ Hot: {r.split(' - ')[0]}"); ci+=1
        for r in flags["best_value_regions"][:1]:
            chip_cols[ci%6].success(f"💰 Value: {r.split(' - ')[0]}"); ci+=1

        st.divider()
        fc1,fc2,fc3,fc4 = st.columns([3,2,1.5,1.5])
        search_q    = fc1.text_input("Search", placeholder="e.g. Maldives, Dubai...", label_visibility="collapsed")
        macros      = ["All"] + sorted(set(payload["data"].keys()))
        macro_sel   = fc2.selectbox("Macro-region", macros, label_visibility="collapsed")
        sort_mode   = fc3.selectbox("Sort", ["Recommended","Price ↑","Stars ↓"], label_visibility="collapsed")
        offers_only = fc4.checkbox("Offers only")

        all_regions = []
        for macro, regions in payload["data"].items():
            for rname, rdata in regions.items():
                if macro_sel != "All" and macro != macro_sel:
                    continue
                hotels = rdata.get("hotels",[])
                if search_q:
                    q = search_q.lower()
                    hotels = [h for h in hotels if q in h["h"].lower() or q in h["r"].lower() or q in h["c"].lower()]
                if offers_only:
                    hotels = [h for h in hotels if h.get("offer")]
                if not hotels:
                    continue
                if sort_mode == "Price ↑":
                    hotels = sorted(hotels, key=lambda h: h["p"])
                elif sort_mode == "Stars ↓":
                    hotels = sorted(hotels, key=lambda h: h["s"], reverse=True)
                else:
                    hotels = sorted(hotels, key=lambda h:(
                        (h.get("offer") and 400 or 0)+
                        (h.get("offer") and h["offer"].get("expiring_soon") and 150 or 0)+
                        {1:300,2:200,3:100}.get(h["seller_tier"],0)+40*h["score"]+
                        min(rdata.get("bookings_6w") or 0,100)), reverse=True)
                all_regions.append((rname, rdata, macro, hotels))

        st.caption(f"Showing {len(all_regions)} regions")

        for rname, rdata, macro, hotels in all_regions[:50]:
            label = (f"**{rname}** — {macro} · {len(hotels)} hotels" +
                     (f" · 📈 {rdata['bookings_6w']} bkgs (6w)" if rdata.get("bookings_6w") else "") +
                     (f" · Med £{round(rdata['median_rev_pp'])}" if rdata.get("median_rev_pp") else ""))
            with st.expander(label):
                show_key = f"show_{rname}"
                if show_key not in st.session_state:
                    st.session_state[show_key] = 12
                visible  = st.session_state[show_key]
                h_cols   = st.columns(3)

                for i, h in enumerate(hotels[:visible]):
                    with h_cols[i % 3]:
                        sent_log = st.session_state.get("sent_log", {})
                        prev_sent = sent_log.get(h["giata"], [])
                        was_sent  = len(prev_sent) > 0

                        badge_parts = []
                        if h["seller_tier"] in (1,2,3):
                            badge_parts.append(f'<span class="badge badge-tier{h["seller_tier"]}">Tier {h["seller_tier"]}</span>')
                        if h["score"] == 5:
                            badge_parts.append('<span class="badge badge-score5">Exceptional</span>')
                        elif h["score"] == 4:
                            badge_parts.append('<span class="badge badge-score4">Good value</span>')
                        if h.get("offer"):
                            exp = h["offer"].get("expiring_soon")
                            badge_parts.append(f'<span class="badge {"badge-exp" if exp else "badge-offer"}">{"⚡ Expiring" if exp else "Offer"}</span>')
                        if was_sent:
                            badge_parts.append('<span class="badge badge-sent">📤 Prev. sent</span>')

                        offer_html = ""
                        if h.get("offer"):
                            exp_cls  = "expiring" if h["offer"].get("expiring_soon") else ""
                            o_type   = str(h["offer"].get("type","")).replace("<","&lt;").replace(">","&gt;")
                            o_sum    = str(h["offer"].get("summary",""))[:100].replace("<","&lt;").replace(">","&gt;")
                            o_bookto = str(h["offer"].get("book_to","")).replace("<","&lt;").replace(">","&gt;")
                            bt_html  = f"<br><b>Book by: {o_bookto}</b>" if o_bookto else ""
                            offer_html = f'<div class="offer-box {exp_cls}"><b>{o_type}</b><br>{o_sum}{bt_html}</div>'

                        # Previously sent history box
                        sent_html = ""
                        if was_sent:
                            last = prev_sent[-1]
                            url_part = f' · <a href="{last["url"]}" target="_blank">View</a>' if last.get("url") and last["url"] != "nan" else ""
                            sent_html = (f'<div class="sent-box">'
                                         f'📤 Last sent: <b>{last["date_sent"]}</b> · £{last["price_sent"]} {last["board"]}{url_part}'
                                         f'</div>')

                        h_name  = str(h["h"]).replace("<","&lt;").replace(">","&gt;")
                        h_board = str(h["b"]).replace("<","&lt;").replace(">","&gt;")
                        stars   = "★" * min(int(h.get("s",0)),5)
                        tier_cls  = {1:"tier1",2:"tier2",3:"tier3"}.get(h["seller_tier"],"")
                        offer_cls = "has-offer" if h.get("offer") else ""
                        sent_cls  = " prev-sent" if was_sent else ""

                        st.markdown(
                            f'<div class="hotel-card {tier_cls} {offer_cls}{sent_cls}">'
                            f'<div style="font-weight:600;font-size:13px;color:#0E2841;margin-bottom:4px">{h_name}</div>'
                            f'<div style="font-size:18px;font-weight:700;color:#0A7C4E">£{round(h["p"])} '
                            f'<span style="font-size:11px;color:#8896A8">{h_board}</span></div>'
                            f'<div style="font-size:11px;color:#8896A8">{stars} · {h["d"]}</div>'
                            f'<div style="margin-top:6px">{"".join(badge_parts)}</div>'
                            f'{sent_html}{offer_html}</div>', unsafe_allow_html=True)

                if len(hotels) > visible:
                    remaining = len(hotels) - visible
                    if st.button(f"Load {min(12,remaining)} more ({remaining} remaining)", key=f"more_{rname}"):
                        st.session_state[show_key] += 12
                        st.rerun()

# ── Tab 3: Shortlist ──────────────────────────────────────────────────────────
with tab_shortlist:
    if not st.session_state.shortlist:
        st.info("Generate the dashboard to see the shortlist.")
    else:
        sl = st.session_state.shortlist
        st.subheader(f"Weekly Email Shortlist — {len(sl)} hotels")
        rows = []
        for r in sl:
            tier_label  = {1:"🟣 T1",2:"🔵 T2",3:"⚫ T3"}.get(r["seller_tier"],"—")
            score_label = {5:"⭐ Exceptional",4:"✅ Good value",3:"🟡 Fair"}.get(r["score"],str(r["score"]))
            urgent = "⚡ " if r.get("expiring_soon") else ""
            status = ""
            if r.get("is_alternative"):
                status = f"🔄 Alt for: {r['alt_for']}"
            elif r.get("previously_sent"):
                status = f"📤 Sent {r['last_sent_date']} @ £{r['last_sent_price']}"
            rows.append({
                "#": r["rank"],
                "Status": status,
                "Hotel": r["hotel"], "Region": r["region"],
                "Board": r["board"],
                "Price": f"£{round(r['price'])}",
                "Price Date": r.get("price_date",""),
                "Median": f"£{round(r['median'])}" if r.get("median") else "—",
                "Hist. Bkgs": r["bookings_total"],
                "Tier": tier_label, "Score": score_label,
                "Offer": f"{urgent}{r['offer_summary'][:60]}..." if r.get("has_offer") and r["offer_summary"] else "",
                "Book By": f"{urgent}{r['book_to']}" if r.get("book_to") else "—",
                "Rationale": r["why"],
                "_prev_sent": r.get("previously_sent", False),
                "_is_alt": r.get("is_alternative", False),
            })
        df_sl = pd.DataFrame(rows)

        def highlight_row(row):
            if row.get("_is_alt"):
                return ["background-color:#ECFDF5"] * len(row)
            if row.get("_prev_sent"):
                return ["background-color:#EEF2FF"] * len(row)
            if "⚡" in str(row.get("Book By","")):
                return ["background-color:#FEF2F2"] * len(row)
            return [""] * len(row)

        display_cols = [c for c in df_sl.columns if not c.startswith("_")]
        st.dataframe(
            df_sl[display_cols].style.apply(highlight_row, axis=1),
            use_container_width=True, hide_index=True
        )
        st.markdown("🟦 Blue rows = previously sent &nbsp;&nbsp; 🟩 Green rows = alternative suggestion")
        st.download_button("⬇️ Download shortlist CSV",
            data=df_sl[display_cols].to_csv(index=False),
            file_name="shg_shortlist.csv", mime="text/csv")

# ── Tab 4: Data Quality ───────────────────────────────────────────────────────
with tab_dq:
    if not st.session_state.dq_notes:
        st.info("Generate the dashboard to see data quality notes.")
    else:
        st.subheader("Data Quality Notes")
        for note in st.session_state.dq_notes:
            if "No data quality" in note:
                st.success(note)
            elif any(w in note.lower() for w in ["error","missing","unmatched","unmapped","warning","not found"]):
                st.warning(note)
            else:
                st.info(note)
        if st.session_state.payload:
            m = st.session_state.payload["meta"]
            st.divider()
            st.caption(f"Generated: {m['generated_at']} · Benchmark: {m['benchmark_from']} → {m['benchmark_to']}")
