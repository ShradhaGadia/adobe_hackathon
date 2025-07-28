
# PDF Heading Extractor

This Python script extracts structured headings from a PDF file and outputs them in a clean, hierarchical JSON format. It is useful for summarizing large documents by pulling out titles and section headers.

## What It Does

The script:

- Analyzes the PDF content using formatting clues such as boldness, font size, and numbering patterns
- Identifies and scores potential headings
- Merges multi-line headings that belong together
- Assigns heading levels (H1, H2, H3) based on numbering depth
- Filters out irrelevant or form-like content
- Outputs a structured JSON file with the document title and an outline

## How It Works

1. Opens the PDF using PyMuPDF (`fitz`)
2. Iterates through each line of each page
3. Assigns a score to lines based on:
   - Bold fonts
   - Font size
   - Numbering (e.g., 1., 1.1.)
   - All-caps formatting
   - Early appearance in the document
4. Lines with a high enough score are considered headings
5. Merged and classified into heading levels using regex and numbering
6. Filters out lines like "name", "signature", etc.
7. Outputs the result to `output.json`

## Requirements

Install required packages:

```bash
pip install PyMuPDF
```

## Usage

1. Place your PDF file in the same directory as the script.
2. Edit the `pdf_path` variable in the script:

```python
pdf_path = "your-file-name.pdf"
```

3. Run the script:

```bash
python extract_headings.py
```

4. The output will be saved as `output.json`.

## Sample Output

Example output in `output.json`:

```json
{
  "title": "1 INTRODUCTION",
  "outline": [
    {
      "level": "H1",
      "text": "1 INTRODUCTION",
      "page": 0
    },
    {
      "level": "H2",
      "text": "1.1 Background",
      "page": 0
    },
    {
      "level": "H3",
      "text": "1.1.1 History",
      "page": 1
    }
  ]
}
```

## Limitations and Notes

- This is a heuristic-based tool and may need tuning for different kinds of PDF layouts.
- Works best on well-structured documents like academic papers, reports, or manuals.
- Currently does not support scanned image PDFs or OCR.

## Future Improvements

- Add multilingual OCR support for scanned documents
- Build a simple web interface
- Docker support for easy deployment


