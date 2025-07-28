import fitz
import re
import json
from collections import OrderedDict
from pprint import pprint

def extract_lines_with_scores(pdf_path):
    doc = fitz.open(pdf_path)
    all_lines = []

    for page_num, page in enumerate(doc):  
        blocks = page.get_text("dict")["blocks"]
        title_extracted = False

        for block in blocks:
            if title_extracted:
                break

            for line in block.get("lines", []):
                combined_text = ""
                max_font = 0
                is_bold = False

                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue

                    combined_text += text + " "
                    max_font = max(max_font, span["size"])
                    if "Bold" in span["font"]:
                        is_bold = True

                combined_text = combined_text.strip()
                if not combined_text or len(combined_text) < 3:
                    continue

                if re.match(r"^\d{1,2}\s+[A-Z]{3,9}\s+\d{4}$", combined_text):
                    continue

                score = 0
                if is_bold: score += 2
                if max_font > 14: score += 2
                if re.match(r"^\d+(\.\d+)*\s", combined_text): score += 2
                if combined_text.isupper(): score += 1
                if page_num <= 1: score += 1

                if score >= 3:
                    all_lines.append({
                        "text": combined_text,
                        "score": score,
                        "font_size": max_font,
                        "page": page_num
                    })
                    title_extracted = True
                    break
    return all_lines

def merge_heading_lines(lines, score_threshold=3):
    merged = []
    current = None

    for line in lines:
        if line['score'] < score_threshold:
            if current:
                merged.append(current)
                current = None
            continue

        if current and line['page'] == current['page']:
            current['text'] += ' ' + line['text']
            current['score'] = max(current['score'], line['score'])
        else:
            if current:
                merged.append(current)
            current = line.copy()

    if current:
        merged.append(current)

    return merged


def assign_heading_levels(merged_lines):
    outline = []
    split_lines = []

    for line in merged_lines:
        parts = re.split(r"(?=\d+\.\d+\s)", line['text'])
        for part in parts:
            clean = part.strip()
            if clean:
                split_lines.append({
                    "text": clean,
                    "page": line["page"]
                })

    for line in split_lines:
        text = line["text"]
        level = "H1"

        match = re.match(r"^(\d+(\.\d+)*)(\s|:)", text)
        if match:
            depth = match.group(1).count(".") + 1
            if depth == 1:
                level = "H1"
            elif depth == 2:
                level = "H2"
            else:
                level = "H3"

        outline.append({
            "level": level,
            "text": text,
            "page": line["page"]
        })

    return outline
def build_final_json(merged_lines):
    if not merged_lines:
        return OrderedDict([("title", "Untitled Document"), ("outline", [])])

    first_page_lines = [l for l in merged_lines if l['page'] == 1]
    first_page_lines.sort(key=lambda x: x['score'], reverse=True)
    title = first_page_lines[0]['text'] if first_page_lines else merged_lines[0]['text']

    merged_lines = [line for line in merged_lines if line["text"].strip() != title.strip()]
    outline = assign_heading_levels(merged_lines)

    filtered_outline = []
    form_phrases = ["date", "signature", "s.no", "name", "age", "relationship", "amount of advance"]

    for item in outline:
        text = item["text"].lower()
        if len(text) < 5 or any(p in text for p in form_phrases):
            continue
        filtered_outline.append(item)

    return OrderedDict([
        ("title", title),
        ("outline", filtered_outline)
    ])

def process_pdf(pdf_path, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)
    raw_lines = extract_lines_with_scores(pdf_path)
    merged_lines = merge_heading_lines(raw_lines, score_threshold=3)
    final_output = build_final_json(merged_lines)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    json_filename = os.path.join(output_dir, f"{base_name}.json")
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)
    print(f"Saved output to {json_filename}")

for filename in os.listdir("inputs"):
    if filename.endswith(".pdf"):
        process_pdf(os.path.join("inputs", filename))
