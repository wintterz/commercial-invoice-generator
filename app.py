"""Small Flask app to generate commercial invoices as PDF or Excel.

Run locally:
    pip install -r requirements.txt
    python app.py
    # open http://127.0.0.1:5000

Generate the sample files without starting the server:
    python app.py --samples
"""

import io
import sys

from flask import Flask, request, render_template_string, send_file

from invoice_models import REGIONS, build_sample_invoice
from pdf_generator import invoice_to_pdf
from excel_generator import invoice_to_xlsx

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Commercial Invoice Generator</title>
  <style>
    :root { --accent:#1F3864; }
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto;
           padding: 0 16px; color:#222; }
    h1 { color: var(--accent); }
    form { display: grid; gap: 14px; margin-top: 24px; }
    label { font-weight: 600; font-size: 14px; display:block; margin-bottom:4px; }
    input, select { width: 100%; padding: 8px; border:1px solid #ccc; border-radius:6px;
                    font-size: 14px; box-sizing: border-box; }
    .row { display:flex; gap:10px; }
    .row > div { flex:1; }
    button { padding: 10px 18px; border:0; border-radius:6px; background: var(--accent);
             color:#fff; font-size:14px; cursor:pointer; }
    .muted { color:#666; font-size:13px; }
  </style>
</head>
<body>
  <h1>Commercial Invoice Generator</h1>
  <p class="muted">Pick a destination region and generate a sample commercial
  invoice as PDF or Excel. Currency, bank block and the trade-terms footer
  change automatically by region.</p>
  <form method="post" action="/generate">
    <div>
      <label>Destination region</label>
      <select name="region">
        {% for code in regions %}<option value="{{code}}">{{code}}</option>{% endfor %}
      </select>
    </div>
    <div>
      <label>Buyer name (optional)</label>
      <input name="buyer_name" placeholder="Leave blank to use the sample buyer">
    </div>
    <div>
      <label>Invoice number (optional)</label>
      <input name="number" placeholder="INV-2026-0042">
    </div>
    <div class="row">
      <div><button name="fmt" value="pdf" type="submit">Download PDF</button></div>
      <div><button name="fmt" value="xlsx" type="submit">Download Excel</button></div>
    </div>
  </form>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE, regions=list(REGIONS))


@app.route("/generate", methods=["POST"])
def generate():
    region = request.form.get("region", "AMERICA")
    if region not in REGIONS:
        region = "AMERICA"
    fmt = request.form.get("fmt", "pdf")
    invoice = build_sample_invoice(
        region=region,
        buyer_name=request.form.get("buyer_name", "").strip(),
        number=request.form.get("number", "").strip(),
    )

    tmp = io.BytesIO()
    # generators write to a path, so use a temp file then read it back
    import tempfile, os
    suffix = ".pdf" if fmt == "pdf" else ".xlsx"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        path = f.name
    if fmt == "pdf":
        invoice_to_pdf(invoice, path)
        mime = "application/pdf"
    else:
        invoice_to_xlsx(invoice, path)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    with open(path, "rb") as f:
        tmp.write(f.read())
    os.unlink(path)
    tmp.seek(0)
    return send_file(tmp, mimetype=mime, as_attachment=True,
                     download_name=f"{invoice.number}_{region}{suffix}")


def write_samples():
    """Write sample PDF + Excel files for both regions (used by the README)."""
    for region in REGIONS:
        inv = build_sample_invoice(region)
        invoice_to_pdf(inv, f"sample_{region.lower()}.pdf")
        invoice_to_xlsx(inv, f"sample_{region.lower()}.xlsx")
        print(f"Wrote sample_{region.lower()}.pdf and sample_{region.lower()}.xlsx")


if __name__ == "__main__":
    if "--samples" in sys.argv:
        write_samples()
    else:
        app.run(debug=True)
