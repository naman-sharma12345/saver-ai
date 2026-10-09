# Receipt scanning: findings

Goal: photograph a paper or UPI receipt and get a pre-filled expense, with no LLM and no external API.

## Verdict
Feasible, and a backend prototype is built. It uses Tesseract (open source OCR) plus a small rule-based parser. Nothing leaves the server and no API key is involved.

## How it works
1. `POST /api/expenses/receipt` takes `{"image_base64": ...}` (5 MB max, PNG/JPG/WebP/TIFF/BMP, checked by file signature).
2. `ml/ocr.py` runs the `tesseract` binary with a 30 second timeout.
3. `ml/receipt_parser.py` finds the merchant (first text-like line), the total (last "total"-style line, ignoring subtotal, tax and discount lines, else the largest amount) and the date (day-first, handles `12/10/2026`, `2026-10-12`, `5 Oct 2026`; rejects impossible dates).
4. The existing category model (and the user's own taught rules) suggests a category.
5. Nothing is saved. The user confirms in the normal add-expense flow.

If Tesseract is not installed the endpoint returns 503 with a clear message. If nothing useful is found it returns 422.

## Why Tesseract
- Apache 2.0 licensed: https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE
- Runs fully offline. A browser build also exists (tesseract.js wraps a WebAssembly port, so images could stay on the phone): https://github.com/naptha/tesseract.js/
- Tesseract.js "does not support PDF files and does not modify the Tesseract recognition model to improve accuracy" (same README), so accuracy equals plain Tesseract.

## What was tested
A synthetic receipt image (clean monospaced text) was read correctly end to end: merchant, total 315.00 and date. That proves the plumbing, not real-world accuracy.

## Known limits (not yet measured)
- Crumpled, faded, skewed or low-light photos will lose accuracy. Tesseract works best on clean, straight, high-contrast text. Pre-processing (deskew, threshold) would help and is not built.
- Handwritten bills and non-English scripts are not handled (the default English model is used).
- Merchant is a heuristic and can pick the wrong line.
- UPI payment screenshots have a different layout from till receipts; a dedicated parser would likely do better there.
- Needs the `tesseract-ocr` package on the server (apt/Docker). It is not in the current docker-compose and not installed in CI, so the image test is skipped in CI.

## Next steps if we continue
1. Add `tesseract-ocr` to the backend Docker image.
2. Collect 30-50 real receipts and UPI screenshots (with consent) and measure total/date accuracy before promising anything to users.
3. Add image pre-processing, then a frontend "Scan receipt" button on Add expense (camera input) with an editable preview.
4. Decide on on-device OCR (tesseract.js) for privacy, since receipts can contain personal data.
Nothing here has had a privacy or legal review.
