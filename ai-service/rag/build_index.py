"""풋살 지식 문서를 청크 분할·임베딩하여 ChromaDB에 영구 저장한다.

사용법:
    python -m rag.build_index --raw data/raw --out data/chroma_db
"""
from __future__ import annotations

import argparse
import uuid
from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from .retriever import DEFAULT_COLLECTION, SentenceTransformerEmbedder

CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
SEPARATORS = ["\n\n", "\n", ". ", " "]


def load_pdf(path: Path) -> list[tuple[str, int]]:
    """PDF 파일을 페이지 단위로 (text, page_number) 리스트 반환."""
    reader = PdfReader(str(path))
    out: list[tuple[str, int]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            out.append((text, i))
    return out


def load_markdown(path: Path) -> list[tuple[str, int]]:
    """Markdown 파일은 페이지 개념이 없으므로 page_number=0."""
    text = path.read_text(encoding="utf-8")
    return [(text, 0)] if text.strip() else []


def derive_metadata(path: Path) -> dict:
    stem = path.stem.replace("_", " ")
    return {"source": stem, "section": ""}


def build(raw_dir: Path, persist_dir: Path) -> int:
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        client.delete_collection(name=DEFAULT_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=DEFAULT_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
    )
    embedder = SentenceTransformerEmbedder()

    total_chunks = 0
    for path in sorted(raw_dir.glob("*")):
        if path.suffix.lower() == ".pdf":
            pages = load_pdf(path)
        elif path.suffix.lower() in (".md", ".markdown"):
            pages = load_markdown(path)
        else:
            print(f"[skip] {path.name} (지원하지 않는 형식)")
            continue

        base_meta = derive_metadata(path)
        file_chunks = 0
        for text, page_no in pages:
            chunks = splitter.split_text(text)
            for chunk in chunks:
                if not chunk.strip():
                    continue
                meta = {**base_meta, "page": page_no, "lang": "ko"}
                collection.add(
                    ids=[str(uuid.uuid4())],
                    documents=[chunk],
                    metadatas=[meta],
                    embeddings=[embedder.encode(chunk)],
                )
                file_chunks += 1
                total_chunks += 1
        print(f"[ok] {path.name}: {len(pages)}페이지, {file_chunks}청크")

    print(f"\n총 {total_chunks}개 청크 인덱싱 완료. 저장 위치: {persist_dir}")
    return total_chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="data/raw", type=Path)
    parser.add_argument("--out", default="data/chroma_db", type=Path)
    args = parser.parse_args()

    count = build(args.raw, args.out)
    if count == 0:
        raise SystemExit("0개 청크 — data/raw에 유효한 문서가 있는지 확인하세요.")


if __name__ == "__main__":
    main()
