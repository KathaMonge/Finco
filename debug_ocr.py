"""Debug script for OCR pipeline - run this to see what the OCR is detecting."""

import sys
import json
import io
from pathlib import Path

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
from services.ocr.onnx_engine import run_ocr_onnx
from services.ocr.preprocessor import preprocess_image
from services.ocr.layout_analyzer import analyze_layout
from services.ocr.parsers.registry import ParserRegistry


def debug_ocr(image_path: str):
    print(f"\n{'='*60}")
    print(f"OCR DEBUG - {image_path}")
    print(f"{'='*60}\n")

    # Load image
    img = Image.open(image_path)
    print(f"Image size: {img.size}")
    print(f"Image mode: {img.mode}")

    # Preprocess
    print("\n[1] Preprocessing...")
    preprocessed = preprocess_image(img)
    preprocessed.save("debug_preprocessed.png")
    print(f"    Saved preprocessed image to debug_preprocessed.png")

    # Run OCR (raw detections before layout analysis)
    print("\n[2] Running OCR detection...")
    import numpy as np
    preprocessed_array = np.array(preprocessed.convert("RGB"))
    raw_detections = run_ocr_onnx(preprocessed)
    print(f"    Found {len(raw_detections)} raw text regions")
    print(f"\n    Raw detections (before layout):")
    for i, det in enumerate(raw_detections):
        bbox = det["bbox"]
        x_center = (bbox[0][0] + bbox[2][0]) / 2
        y_center = (bbox[0][1] + bbox[2][1]) / 2
        print(f"    {i:3d}. [{x_center:7.1f}, {y_center:7.1f}] conf={det['confidence']:.2f} | {det['text']!r}")

    # Layout analysis
    print("\n[3] Layout analysis...")
    sorted_lines = analyze_layout(raw_detections)
    print(f"    Resulted in {len(sorted_lines)} sorted lines")
    print(f"\n    Sorted lines:")
    for i, line in enumerate(sorted_lines):
        print(f"    {i:3d}. {line}")

    # Parse with fallback parser
    print("\n[4] Parsing with FallbackParser...")

    import importlib
    import services.ocr.parsers.fallback as fb
    importlib.reload(fb)

    print("\n    Testing regex patterns on each line:")
    for i, line in enumerate(sorted_lines):
        line_s = line.strip()
        if len(line_s) < 10:
            continue
        m1 = fb.LINE_TX_PATTERN.search(line_s)
        m2 = fb.LINE_TX_GENERIC.search(line_s)
        if m1:
            print(f"    {i:3d}. PATTERN match: groups={m1.groups()}")
        elif m2:
            print(f"    {i:3d}. GENERIC match: groups={m2.groups()}")
        else:
            print(f"    {i:3d}. NO MATCH: {line_s!r}")

    parser = fb.FallbackParser()
    result = parser.parse(sorted_lines)

    from utils.helpers import parse_date as pd, parse_amount as pa
    importlib.reload(__import__('utils.helpers', fromlist=['parse_date']))
    from utils.helpers import parse_date as pd2, parse_amount as pa2
    print("\n    Date/Amount parse tests:")
    test_dates = ['2-MAY-2', '3-MAY-2', '6-MAY-2', '-IUN-2', '1JlUN-2', '3.JUN-2', '5-JUN-2', '5IUN-2', '5=IlUN-2', '6-I11N-2', '8IIUN-2', '9-IIUN-2', '22-MAY-26', '-IUN-2', '-JIUN-2']
    for td in test_dates:
        parsed = pd2(td)
        print(f"    parse_date({td!r:20s}) -> {parsed}")

    test_amounts = ['2850', '511210', 'g9mn', '1hum', '040', 'nun', '4000', '54m0', '38320', '510', '70011', 'moo', 'bonn', '2an', '55130', '0']
    for ta in test_amounts:
        parsed = pa2(ta)
        print(f"    parse_amount({ta!r:10s}) -> {parsed}")

    print(f"\n    Detected emisor: {result.emisor}")
    print(f"    Overall confidence: {result.overall_confidence:.2f}")

    if result.monto:
        print(f"    Monto: {result.monto.value} (conf={result.monto.confidence:.2f}, raw={result.monto.raw_text!r})")
    else:
        print(f"    Monto: NOT FOUND")

    if result.fecha:
        print(f"    Fecha: {result.fecha.value} (conf={result.fecha.confidence:.2f}, raw={result.fecha.raw_text!r})")
    else:
        print(f"    Fecha: NOT FOUND")

    if result.tarjeta:
        print(f"    Tarjeta: {result.tarjeta.value} (conf={result.tarjeta.confidence:.2f}, raw={result.tarjeta.raw_text!r})")
    else:
        print(f"    Tarjeta: NOT FOUND")

    print(f"\n    Transactions found: {len(result.transactions)}")
    for i, tx in enumerate(result.transactions):
        print(f"    {i:3d}. {tx.date} | {tx.description!r:30s} | ${tx.amount} | conf={tx.confidence:.2f}")
        print(f"         raw: {tx.raw_text!r}")

    print(f"\n{'='*60}\n")

    # Also dump raw JSON for inspection
    with open("debug_ocr_result.json", "w", encoding="utf-8") as f:
        json.dump({
            "raw_detections": [
                {
                    "bbox": d["bbox"].tolist() if hasattr(d["bbox"], 'tolist') else d["bbox"],
                    "text": d["text"],
                    "confidence": d["confidence"]
                }
                for d in raw_detections
            ],
            "sorted_lines": sorted_lines,
            "result": {
                "emisor": result.emisor,
                "monto": {"value": result.monto.value, "confidence": result.monto.confidence, "raw": result.monto.raw_text} if result.monto else None,
                "fecha": {"value": result.fecha.value, "confidence": result.fecha.confidence, "raw": result.fecha.raw_text} if result.fecha else None,
                "transactions": [
                    {"date": str(tx.date), "description": tx.description, "amount": str(tx.amount), "raw": tx.raw_text}
                    for tx in result.transactions
                ]
            }
        }, f, indent=2, default=str)
    print("Saved full results to debug_ocr_result.json")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_ocr.py <image_path>")
        sys.exit(1)
    debug_ocr(sys.argv[1])
