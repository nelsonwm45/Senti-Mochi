from app.services.embedding_service import embedding_service
from sqlmodel import Session, select, col
from app.database import engine
from app.models import DocumentChunk, Document

company_id = "12a99d4a-eeec-4c62-aecd-520ac04c83f0"

env_query = "Net Zero 2050 NZBA, Just Transition, SBTi, Sectoral Decarbonisation Pathways (Palm Oil, Power, O&G), PCAF Financed Emissions Scope 3, Carbon Neutrality, Green Energy Tariff, RECs, Stranded Assets, Climate Scenario Analysis NGFS, Physical Risk Acute Chronic, TNFD Nature-positive, NDPE, HCV."

print("Generating query embedding...")
env_vector = embedding_service.generate_embeddings([env_query])[0]

with Session(engine) as session:
    print("Executing search...")
    statement = (
        select(DocumentChunk, DocumentChunk.embedding.l2_distance(env_vector).label("dist"))
        .join(Document)
        .where(Document.company_id == company_id)
        .order_by(col(DocumentChunk.embedding).l2_distance(env_vector))
        .limit(5)
    )
    results = session.exec(statement).all()
    
    print(f"Found {len(results)} chunks.")
    for i, (c, dist) in enumerate(results):
        print(f"--- Chunk {i+1} (ID: {c.id}) --- Distance: {dist}")
        print(c.content[:100] + "...")
