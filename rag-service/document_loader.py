import csv
import json
from pathlib import Path

from docx import Document
from pypdf import PdfReader


class DocumentLoader:
    def __init__(self, folder, chunk_size=800, overlap=100):
        self.folder = Path(folder)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def load(self):
        chunks = []
        for path in sorted(self.folder.rglob("*")):
            if path.is_file():
                chunks.extend(self.load_file(path))
        return chunks

    def load_file(self, path):
        extension = path.suffix.lower()
        name = path.relative_to(self.folder).as_posix()

        # Ready-made chunks: a JSON list of dicts
        if extension == ".json":
            chunks = json.loads(path.read_text(encoding="utf-8"))
            for chunk in chunks:
                chunk.setdefault("source", name)
                chunk.setdefault("source_type", "json")
            return chunks

        try:
            text = self.read_text(path, extension)
        except Exception as error:
            print(f"Skipped {path.name}: {error}")
            return []

        if not text or not text.strip():
            print(f"Skipped {path.name}: unsupported or empty")
            return []

        return [
            {
                "id": f"{name}::{number}",
                "title": path.stem,
                "section": path.parent.name,
                "text": piece,
                "source": name,
                "source_type": extension.lstrip("."),
            }
            for number, piece in enumerate(self.split(text))
        ]

    def read_text(self, path, extension):
        if extension in (".txt", ".md"):
            return path.read_text(encoding="utf-8")
        if extension == ".pdf":
            return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        if extension == ".docx":
            return "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
        if extension == ".csv":
            with open(path, encoding="utf-8", newline="") as csv_file:
                return "\n".join(", ".join(row) for row in csv.reader(csv_file))
        return None  # unsupported type

    def split(self, text):
        step = self.chunk_size - self.overlap
        return [text[start:start + self.chunk_size] for start in range(0, len(text), step)]