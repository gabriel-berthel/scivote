import requests
from pydantic import BaseModel
from typing import List
from datetime import datetime
import arxiv
from pdfminer.high_level import extract_text
import re
from io import BytesIO


class ArxivDocument(BaseModel):
    arxiv_id: str
    title: str
    abstract: str
    authors: List[str]
    categories: List[str]
    published: datetime
    content: str

    @classmethod
    def from_arxiv_id(cls, arxiv_id: str):
        metadata = cls.get_metadata_from_arxiv(arxiv_id)
        content = cls.extract_pdf_content(metadata['pdf_url'])
        
        return cls(
            arxiv_id=arxiv_id,
            title=metadata['title'],
            abstract=metadata['abstract'],
            authors=metadata['authors'],
            categories=metadata['categories'],
            published=metadata['published'],
            content=content
        )

    @staticmethod
    def get_metadata_from_arxiv(arxiv_id: str):
        search = arxiv.Search(id_list=[arxiv_id])
        metadata = {}

        for result in search.results():
            metadata['title'] = result.title
            metadata['abstract'] = result.summary
            metadata['authors'] = [author.name for author in result.authors]
            metadata['categories'] = result.categories
            metadata['published'] = result.published
            metadata['pdf_url'] = result.pdf_url

        return metadata

    @staticmethod
    def extract_pdf_content(pdf_url: str):
        if not pdf_url:
            return ""

        pdf_text = ArxivDocument.download_and_extract_pdf(pdf_url)
        return ArxivDocument.clean_pdf_content(pdf_text)

    @staticmethod
    def download_and_extract_pdf(pdf_url: str):
        response = requests.get(pdf_url)
        response.raise_for_status()

        pdf_content = BytesIO(response.content)
        return extract_text(pdf_content)

    @staticmethod
    def clean_pdf_content(text: str):
        text = re.sub(r'\[\d+(?:,\d+)*\]', '', text)  # Remove citation numbers
        text = re.sub(r'[A-Za-z]+\s+et al\.,\s+\d{4}', '', text)  # Remove author lists with 'et al.'
        text = re.sub(r'References\s+.*', '', text, flags=re.DOTALL)  # Remove references section
        text = re.sub(r'[\d]+\s?Footnote.*', '', text)  # Remove footnotes
        text = re.sub(r'\bPage\s+\d+\b', '', text)  # Remove page numbers
        return text.strip()