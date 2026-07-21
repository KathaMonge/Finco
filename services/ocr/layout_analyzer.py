"""Layout analysis for multi-column OCR text ordering.

Vouchers often have multi-column layouts (e.g., left: description, right: amount).
Simple top-to-bottom ordering mixes columns together. This module groups text
by physical position and orders within columns.
"""


def analyze_layout(detections: list[dict]) -> list[str]:
    """Sort OCR detections intelligently: column-wise, then top-to-bottom.

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

    groups = _group_lines(items)

    sorted_lines = []
    for col_x, lines in _sort_columns(groups):
        for line in lines:
            line.sort(key=lambda i: i["x_left"])
            text = " ".join(item["text"] for item in line).strip()
            if text:
                sorted_lines.append(text)

    return sorted_lines


def _group_lines(items: list[dict], threshold: float = 15.0) -> list[list[list[dict]]]:
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


def _sort_columns(lines: list[list[dict]]) -> list[tuple[float, list[list[dict]]]]:
    """Detect columns and sort lines column-wise.

    Returns list of (column_x, lines_in_column) tuples.
    """
    if not lines:
        return []

    all_x = [item["x_center"] for line in lines for item in line]
    if not all_x:
        return [(0.0, lines)]

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
        columns.append((0.0, left_lines))
    if right_lines:
        columns.append((1.0, right_lines))

    return columns if columns else [(0.0, lines)]
