# Document Analyzer

This project provides a robust PDF analysis tool that extracts, ranks, and refines content from multiple PDF documents based on a defined persona and job context. It's designed to help domain-specific users (like HR professionals, travel planners, etc.) automatically pull the most relevant sections from large document collections.

## Features

- Extracts structured sections from PDF files using heading detection
- Uses sentence embeddings and NLP to find relevant content
- Ranks sections based on uniqueness, richness, and contextual fit
- Identifies and extracts key named entities
- Supports multiple collections with different personas and job goals
- Saves output in structured JSON format for further use

## Requirements

- Python 3.7+
- pip packages:
  - PyPDF2
  - sentence-transformers
  - scikit-learn
  - numpy
  - spacy
  - en_core_web_sm (spaCy model)

Install requirements with:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Folder Structure

- Each collection should have a `PDFs` folder with input files
- Output is saved as `output.json` in the parent directory of each collection

Example:
```
Collection 1/
├── PDFs/
│   ├── doc1.pdf
│   └── doc2.pdf
└── output.json
```

## How to Run

```bash
python document_analyzer.py
```

## Output Format

```json
{
  "metadata": {
    "input_documents": [...],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a trip of 4 days...",
    "processing_timestamp": "..."
  },
  "extracted_sections": [...],
  "subsection_analysis": [...]
}
```

## License

This project is open-source and licensed under the MIT License.