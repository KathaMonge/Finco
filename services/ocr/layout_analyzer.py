"""Layout analysis for multi-column OCR text ordering.

Supports two layout modes:
- Table mode: documents with tabular structure (bank statements, receipts with rows).
  Each row is a horizontal band; items at the same y-level belong together.
- Column mode: documents with independent vertical columns (newsletters, reports).
  Each column is read top-to-bottom before moving to the next.

The mode is auto-detected based on whether items form clear horizontal rows
vs. independent vertical columns.
"""


def analyze_layout(detections: list[dict]) -> list[str]:
    """Sort OCR detections intelligently based on document layout.

    Args:
        detections: list of dicts with keys bbox, text, confidence

    Returns:
        list of text strings in reading order
    """
    if not detections:
        return []

    items = []
    for d in detections:
        bbox = d["bbox"]
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        items.append({
            "text": d["text"],
            "confidence": d.get("confidence", 1.0),
            "x_center": (min(x_coords) + max(x_coords)) / 2,
            "y_center": (min(y_coords) + max(y_coords)) / 2,
            "y_top": min(y_coords),
            "x_left": min(x_coords),
            "width": max(x_coords) - min(x_coords),
        })

    items.sort(key=lambda i: i["y_top"])

    lines = _group_lines(items)

    if _is_tabular(lines):
        return _sort_tabular(lines)
    else:
        return _sort_columnar(lines)


def _group_lines(items: list[dict], threshold: float = 15.0) -> list[list[dict]]:
    """Group detections into lines based on vertical proximity."""
    if not items:
        return []

    lines = [[items[0]]]
    for item in items[1:]:
        if abs(item["y_center"] - lines[-1][-1]["y_center"]) < threshold:
            lines[-1].append(item)
        else:
            lines.append([item])

    return lines


def _is_tabular(lines: list[list[dict]]) -> bool:
    """Detect whether the document is tabular (rows) or columnar.

    Tabular: items in the same line span wide x-ranges with items at multiple
    distinct x-positions, and lines overlap in x-range significantly.
    Columnar: lines belong to clearly separated x-zones with little overlap.
    """
    if len(lines) < 3:
        return False

    line_x_ranges = []
    for line in lines:
        xs = [item["x_center"] for item in line]
        line_x_ranges.append((min(xs), max(xs)))

    overlap_count = 0
    for i in range(len(line_x_ranges)):
        for j in range(i + 1, len(line_x_ranges)):
            lo_a, hi_a = line_x_ranges[i]
            lo_b, hi_b = line_x_ranges[j]
            overlap_lo = max(lo_a, lo_b)
            overlap_hi = min(hi_a, hi_b)
            if overlap_hi > overlap_lo:
                overlap_count += 1

    total_pairs = len(line_x_ranges) * (len(line_x_ranges) - 1) / 2
    overlap_ratio = overlap_count / total_pairs if total_pairs > 0 else 0

    wide_lines = sum(
        1 for lo, hi in line_x_ranges
        if (hi - lo) > 200
    )

    return overlap_ratio > 0.4 or wide_lines > len(lines) * 0.3


def _sort_tabular(lines: list[list[dict]]) -> list[str]:
    """Sort for tabular documents: top-to-bottom, left-to-right within each row."""
    sorted_lines = []
    for line in lines:
        line.sort(key=lambda i: i["x_left"])
        text = " ".join(item["text"] for item in line).strip()
        if text:
            sorted_lines.append(text)
    return sorted_lines


def _sort_columnar(lines: list[list[dict]]) -> list[str]:
    """Sort for columnar documents: group into columns, read each column top-to-bottom."""
    if not lines:
        return []

    all_x = [item["x_center"] for line in lines for item in line]
    if not all_x:
        return _sort_tabular(lines)

    avg_x = sum(all_x) / len(all_x)

    left_lines = []
    right_lines = []

    for line in lines:
        line_avg_x = sum(item["x_center"] for item in line) / len(line)
        if line_avg_x < avg_x:
            left_lines.append(line)
        else:
            right_lines.append(line)

    columns = []
    if left_lines:
        columns.append(left_lines)
    if right_lines:
        columns.append(right_lines)

    if len(columns) <= 1:
        return _sort_tabular(lines)

    sorted_lines = []
    for col_lines in columns:
        for line in col_lines:
            line.sort(key=lambda i: i["x_left"])
            text = " ".join(item["text"] for item in line).strip()
            if text:
                sorted_lines.append(text)

    return sorted_lines
