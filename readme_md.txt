# SHG D2 Weekly Dashboard

A Streamlit app for generating and browsing the SHG weekly hotel dashboard from three data files.

## Files required

| File | Format | Notes |
|------|--------|-------|
| Bookings dataset | `.xlsx` | Any sheet — BookedDate, FolderStatus, ProdMix, KPIRevenue, etc. |
| Price snapshot | `.xlsx` | Must contain sheet named **D2 Price Snapshot** |
| Special offers | `.csv` | Flexible column names — GIATA, offer details, travel dates |

## Local setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repo, branch, and set **Main file path** to `app.py`.
4. Click **Deploy**.

## Repo structure

```
├── app.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml
```

## Features

- **Upload & Generate** — Upload 1–3 data files and process locally (no API key needed)
- **Hotel Explorer** — Browse all hotels by macro-region with smart/price/stars sorting, offer flags, tier badges, value scores
- **Email Shortlist** — Top 20 hotels ranked by priority formula with export to CSV
- **Data Quality Notes** — Flags unmapped destinations, missing columns, unmatched GIATAs, expiring offers

## Notes

- Processing is done entirely in Python — no external API calls required
- Session state persists within a single browser session; for persistent shared storage across users, add a database backend (e.g. Supabase, SQLite)
- Max file upload size is set to 50 MB in `.streamlit/config.toml`
