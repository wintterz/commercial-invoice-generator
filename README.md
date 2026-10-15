# Commercial Invoice Generator

A small **Flask** app that generates export **commercial invoices** as **PDF** (ReportLab)
and **Excel** (openpyxl) from a single data model. The same invoice is rendered differently
per destination **region** — currency, bank block and the trade-terms footer change
automatically.

> Demo project with **fictitious data** (companies, bank details and products are invented).
> It reproduces, in a generic form, the structure of an internal tool I built at work.

## Features

- One data model (`Invoice`, `Party`, `LineItem`) rendered to **two formats**: PDF and Excel.
- **Region bifurcation** via a `RegionConfig`: `AMERICA` (USD, no trade-terms footer) and
  `EUROPE` (EUR, IBAN/BIC bank block, FOB/freight/insurance footer).
- Clean, styled output: header, seller/buyer blocks, line-item table, totals and bank details.
- Minimal **web UI** (pick region, optional buyer/number, download PDF or Excel).
- Easy to extend: add a new region by adding one entry to `REGIONS`.

## Tech stack

`Python` · `Flask` · `ReportLab` (PDF) · `openpyxl` (Excel)

## Run it

```bash
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000
```

Generate sample invoices (one PDF + one Excel per region) without starting the server:

```bash
python app.py --samples
# -> sample_america.pdf / .xlsx and sample_europe.pdf / .xlsx
```

## Project structure

```
invoice_models.py    # Invoice / Party / LineItem + REGIONS config
pdf_generator.py     # invoice_to_pdf()  — ReportLab
excel_generator.py   # invoice_to_xlsx() — openpyxl
app.py               # Flask web UI + download routes
```

## How the region design works

`invoice_models.REGIONS` maps a region code to a `RegionConfig` (currency, bank details,
and whether to show the FOB/freight/insurance footer). `Invoice.total` and both renderers
read from that config, so adding a region is a one-line change and nothing else needs to
know about it.

---

Built by **Bruno Meirelles** · [LinkedIn](https://www.linkedin.com/in/bruno-meirelles-0b35b51b9/)
