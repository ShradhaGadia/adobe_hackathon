import json
import PyPDF2
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import re
import spacy
from typing import List, Dict, Any, Tuple
from collections import Counter

class DocumentAnalyzer:
    def __init__(self):
        # Initialize models
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load("en_core_web_sm")  # Small spaCy model for NER
        
        # Configuration
        self.min_section_length = 150
        self.max_sections_per_doc = 2  # To ensure diversity across documents
        self.target_section_count = 5

    def _create_query_embedding(self, persona: str, job: str) -> np.ndarray:
        """Create a query embedding from persona and job description"""
        query_text = f"{persona}. {job}"
        return self.embedding_model.encode(query_text)
    
    def _calculate_entity_relevance(self, text: str, persona: str, job: str) -> float:
        """
        Boost similarity score if named entities in the section text 
        match terms from the persona or job description.
        """
        if not text:
            return 0.0
    
        doc = self.nlp(text)
        named_entities = {ent.text.lower() for ent in doc.ents if ent.label_ in {'ORG', 'PERSON', 'GPE', 'PRODUCT', 'EVENT'}}
    
        keywords = set(word.lower() for word in (persona + " " + job).split())
    
        overlap = named_entities.intersection(keywords)
        
        return 0.2 * len(overlap)  # small boost per matching entity
    
    def refine_subsection_text(self, text: str, persona: str, job: str) -> Tuple[str, List[str]]:
        """
        Clean up section text and extract key entities that are relevant to persona/job.
        Returns:
            - Refined text (currently just stripped version).
            - List of important entities.
        """
        if not text:
            return "", []
    
        # Basic cleanup
        refined_text = re.sub(r'\s+', ' ', text).strip()
    
        # Named entity extraction
        doc = self.nlp(text)
        all_entities = [ent.text for ent in doc.ents if ent.label_ in {'ORG', 'PERSON', 'GPE', 'PRODUCT', 'EVENT'}]
    
        # Filter based on persona and job context
        context_words = set((persona + " " + job).lower().split())
        important_entities = [e for e in all_entities if e.lower() in context_words]
    
        return refined_text, important_entities



    def extract_structured_sections(self, file_path: str) -> List[Dict[str, Any]]:
        """Robust PDF text extraction with better error handling"""
        sections = []
        
        if not os.path.exists(file_path):
            print(f"Warning: File not found - {file_path}")
            return sections
            
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                current_section = ""
                current_title = "Introduction"
                page_start = 1
                
                for page_num in range(len(reader.pages)):
                    try:
                        page = reader.pages[page_num]
                        text = page.extract_text()
                        
                        if not text:
                            continue
                            
                        # Detect section headings
                        lines = text.split('\n')
                        for line in lines:
                            if self._is_heading(line, current_title):
                                # Save previous section if it has content
                                if len(current_section) >= self.min_section_length:
                                    sections.append({
                                        'document': os.path.basename(file_path),
                                        'page_number': page_start,
                                        'section_title': current_title,
                                        'content': current_section
                                    })
                                # Start new section
                                current_title = line.strip()
                                current_section = ""
                                page_start = page_num + 1
                            else:
                                current_section += line + "\n"
                                
                    except Exception as e:
                        print(f"Error processing page {page_num} in {file_path}: {str(e)}")
                        continue
                
                # Add the last section
                if current_section and len(current_section) >= self.min_section_length:
                    sections.append({
                        'document': os.path.basename(file_path),
                        'page_number': page_start,
                        'section_title': current_title,
                        'content': current_section
                    })
                    
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            
        return sections

    def _is_heading(self, line: str, current_title: str) -> bool:
        """Determine if a line is a section heading"""
        line = line.strip()
        if not line or len(line) > 80 or line.count(' ') > 5 or line == current_title:
            return False
            
        # Heading patterns
        patterns = [
            r'^[A-Z][A-Za-z ]+$',  # Title case
            r'^[IVX]+\.',           # Roman numerals
            r'^[0-9]+\.',           # Numbered
            r'^[A-Z][A-Z ]+$',      # All caps
            r'^[A-Za-z ]+:$'        # Ends with colon
        ]
        
        return any(re.match(p, line) for p in patterns)

    def rank_sections(self, sections: List[Dict[str, Any]], persona: str, job: str) -> List[Dict[str, Any]]:
        """Improved ranking: favors unique, content-rich, non-generic headings"""
        if not sections:
            return []
    
        title_counts = Counter(s['section_title'].strip().lower() for s in sections)
    
        def is_generic(title: str) -> bool:
            doc = self.nlp(title)
            return any(tok.lemma_.lower() in {"ingredient", "instruction", "method", "step", "preparation"} for tok in doc)
    
        def score_section(section: Dict[str, Any]) -> float:
            title = section.get('section_title', '').strip()
            content = section.get('content', '')
            if not title or not content:
                return -1.0  # very low score for empty
            
            doc = self.nlp(title)
            score = 0
    
            if title_counts[title.lower()] == 1:
                score += 2  # unique title
            if len(title.split()) >= 2:
                score += 1  # title with multiple words
            if any(tok.pos_ in {'NOUN', 'PROPN'} for tok in doc):
                score += 1  # has meaningful nouns
            if is_generic(title):
                score -= 2  # penalize generic titles
    
            return score
    
        for section in sections:
            section['similarity_score'] = score_section(section)
    
        ranked = sorted(sections, key=lambda x: x['similarity_score'], reverse=True)
    
        final_sections = []
        docs_used = {}
    
        for section in ranked:
            doc = section.get('document')
            if docs_used.get(doc, 0) < self.max_sections_per_doc:
                final_sections.append(section)
                docs_used[doc] = docs_used.get(doc, 0) + 1
            if len(final_sections) >= self.target_section_count:
                break
    
        for i, sec in enumerate(final_sections):
            sec['importance_rank'] = i + 1
    
        return final_sections
    
    def analyze_documents(self, document_paths: List[str], persona: str, job: str) -> Dict[str, Any]:
        output = self._create_empty_output(document_paths, persona, job)
    
        all_sections = []
        for path in document_paths:
            sections = self.extract_structured_sections(path)
            all_sections.extend(sections)
    
        if not all_sections:
            return output
    
        ranked_sections = self.rank_sections(all_sections, persona, job)
        extracted_sections = []
        subsection_analysis = []
    
        for section in ranked_sections:
            refined_text, important_entities = self.refine_subsection_text(section.get('content', ''), persona, job)
            
            extracted_sections.append({
                'document': section.get('document', ''),
                'section_title': section.get('section_title', ''),
                'importance_rank': section.get('importance_rank', 0),
                'page_number': section.get('page_number', 0)
            })
    
            subsection_analysis.append({
                'document': section.get('document', ''),
                'refined_text': refined_text,
                'page_number': section.get('page_number', 0),
                'key_entities': important_entities
            })
    
        output['extracted_sections'] = extracted_sections
        output['subsection_analysis'] = subsection_analysis
        return output
    
    

    def _create_empty_output(self, document_paths: List[str], persona: str, job: str) -> Dict[str, Any]:
        """Return a valid empty output structure"""
        return {
            'metadata': {
                'input_documents': [os.path.basename(p) for p in document_paths],
                'persona': persona,
                'job_to_be_done': job,
                'processing_timestamp': datetime.now().isoformat()
            },
            'extracted_sections': [],
            'subsection_analysis': []
        }


if __name__ == "__main__":
    analyzer = DocumentAnalyzer()
    
    # Define collections with their respective personas and jobs
    collections = [
        {
            "path": "Collection 1/PDFs",
            "persona": "Travel Planner",
            "job": "Plan a trip of 4 days for a group of 10 college friends."
        },
        {
            "path": "Collection 2/PDFs",
            "persona": "HR professional",
            "job": "Create and manage fillable forms for onboarding and compliance"
        },
        {
            "path": "Collection 3/PDFs",
            "persona": "Food Contractor",
            "job": "Prepare a vegetarian buffet-style dinner menu for a corporate gathering, including gluten-free items."
        }
    ]
    
    for collection in collections:
        # Get all PDF files in the collection folder
        try:
            pdf_files = [os.path.join(collection["path"], f) 
                        for f in os.listdir(collection["path"])
                        if f.lower().endswith('.pdf')]
            
            if not pdf_files:
                print(f"No PDF files found in {collection['path']}")
                continue
                
            print(f"\nProcessing collection: {collection['path']}")
            print(f"Persona: {collection['persona']}")
            print(f"Job: {collection['job']}")
            
            # Analyze documents
            result = analyzer.analyze_documents(pdf_files, collection["persona"], collection["job"])
            
            # Save results in the collection folder
            output_path = os.path.join(collection["path"], "../output.json")
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"Analysis complete. Results saved to {output_path}")
            
        except Exception as e:
            print(f"Error processing collection {collection['path']}: {str(e)}")
            continue