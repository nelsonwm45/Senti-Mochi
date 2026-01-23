from sqlmodel import Session, select
from app.database import engine
from app.models import Document, DocumentChunk

DOCUMENT_ID = "7cd74f5b-41e3-4a3b-a1cb-ea1052b4d4b1"

def delete_contaminated_doc():
    with Session(engine) as session:
        # 1. Find the doc
        doc = session.exec(select(Document).where(Document.id == DOCUMENT_ID)).first()
        if not doc:
            print(f"Document {DOCUMENT_ID} not found.")
            return

        print(f"Found contaminated document: {doc.filename}")

        # 2. Delete chunks first (cascade usually handles this but being safe)
        chunks = session.exec(select(DocumentChunk).where(DocumentChunk.document_id == DOCUMENT_ID)).all()
        print(f"Deleting {len(chunks)} chunks associated with this document...")
        for chunk in chunks:
            session.delete(chunk)
            
        # 3. Delete doc
        session.delete(doc)
        session.commit()
        print("Successfully deleted contaminated document and chunks.")

if __name__ == "__main__":
    delete_contaminated_doc()
