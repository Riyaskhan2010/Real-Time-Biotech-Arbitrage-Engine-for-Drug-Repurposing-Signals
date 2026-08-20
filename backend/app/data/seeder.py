"""
Database seeder — populates the database with demo data.
Run via: python -m app.data.seeder  (from backend/ directory)
"""
import sys
import os

# Ensure we can import from backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.drug import Drug
from app.models.disease import Disease
from app.models.signal import RepurposingSignal
from app.models.evidence import Evidence
from app.models.research_source import ResearchSource
from app.models.alert import Alert
from app.data.seed_data import (
    DEMO_DRUGS, DEMO_DISEASES, DEMO_SIGNALS,
    DEMO_EVIDENCE, DEMO_RESEARCH_SOURCES, DEMO_USERS,
)
from app.utils.auth import get_password_hash


def seed_database(db: Session) -> None:
    print("Seeding database with demo data...")

    # --- Users ---
    print("  Creating demo users...")
    user_map = {}
    for u in DEMO_USERS:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            user = User(
                email=u["email"],
                username=u["username"],
                full_name=u["full_name"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"],
                institution=u["institution"],
            )
            db.add(user)
            db.flush()
            user_map[u["email"]] = user
        else:
            user_map[u["email"]] = existing
    db.commit()

    # --- Drugs ---
    print("  Creating demo drugs...")
    drug_map = {}
    for d in DEMO_DRUGS:
        existing = db.query(Drug).filter(Drug.name == d["name"]).first()
        if not existing:
            drug = Drug(**{k: v for k, v in d.items()})
            db.add(drug)
            db.flush()
            drug_map[d["name"]] = drug
        else:
            drug_map[d["name"]] = existing
    db.commit()

    # --- Diseases ---
    print("  Creating demo diseases...")
    disease_map = {}
    for d in DEMO_DISEASES:
        existing = db.query(Disease).filter(Disease.name == d["name"]).first()
        if not existing:
            disease = Disease(**{k: v for k, v in d.items()})
            db.add(disease)
            db.flush()
            disease_map[d["name"]] = disease
        else:
            disease_map[d["name"]] = existing
    db.commit()

    # --- Signals ---
    print("  Creating demo repurposing signals...")
    signal_list = []
    for s in DEMO_SIGNALS:
        drug = drug_map.get(s["drug_name"])
        disease = disease_map.get(s["disease_name"])
        if not drug or not disease:
            print(f"    WARNING: Skipping signal — drug '{s['drug_name']}' or disease '{s['disease_name']}' not found")
            signal_list.append(None)
            continue

        existing = db.query(RepurposingSignal).filter(
            RepurposingSignal.drug_id == drug.id,
            RepurposingSignal.disease_id == disease.id,
        ).first()

        if not existing:
            signal_data = {k: v for k, v in s.items() if k not in ("drug_name", "disease_name")}
            signal = RepurposingSignal(
                drug_id=drug.id,
                disease_id=disease.id,
                **signal_data,
            )
            db.add(signal)
            db.flush()
            signal_list.append(signal)
        else:
            signal_list.append(existing)
    db.commit()

    # --- Evidence ---
    print("  Creating demo evidence items...")
    for e in DEMO_EVIDENCE:
        signal_index = e["signal_index"]
        signal = signal_list[signal_index] if signal_index < len(signal_list) else None
        if not signal:
            continue

        existing = db.query(Evidence).filter(
            Evidence.signal_id == signal.id,
            Evidence.title == e["title"],
        ).first()

        if not existing:
            ev_data = {k: v for k, v in e.items() if k != "signal_index"}
            evidence = Evidence(signal_id=signal.id, **ev_data)
            db.add(evidence)
    db.commit()

    # --- Research Sources ---
    print("  Creating demo research sources...")
    for rs in DEMO_RESEARCH_SOURCES:
        existing = db.query(ResearchSource).filter(
            ResearchSource.title == rs["title"]
        ).first()
        if not existing:
            source = ResearchSource(**rs)
            db.add(source)
    db.commit()

    # --- Alerts for demo researcher ---
    print("  Creating demo alerts...")
    researcher = user_map.get("researcher@bioarbitrage.demo")
    if researcher:
        demo_alerts = [
            {
                "alert_type": "new_signal",
                "entity_type": "drug",
                "entity_id": drug_map["Metformin"].id if "Metformin" in drug_map else 1,
                "entity_name": "Metformin",
                "title": "New high-confidence signal detected for Metformin",
                "message": "A new signal linking Metformin to Alzheimer's Disease has been detected with evidence score 82.",
                "is_read": False,
            },
            {
                "alert_type": "new_evidence",
                "entity_type": "drug",
                "entity_id": drug_map["Sildenafil"].id if "Sildenafil" in drug_map else 4,
                "entity_name": "Sildenafil",
                "title": "New research evidence added for Sildenafil",
                "message": "A new network medicine study has been indexed relating Sildenafil to Alzheimer's Disease.",
                "is_read": False,
            },
            {
                "alert_type": "score_change",
                "entity_type": "disease",
                "entity_id": disease_map["Alzheimer's Disease"].id if "Alzheimer's Disease" in disease_map else 1,
                "entity_name": "Alzheimer's Disease",
                "title": "Signal score updated for Alzheimer's Disease",
                "message": "The Rapamycin–Alzheimer's signal score increased from 72 to 76 after new evidence was indexed.",
                "is_read": True,
            },
        ]
        for al in demo_alerts:
            existing = db.query(Alert).filter(
                Alert.user_id == researcher.id,
                Alert.title == al["title"],
            ).first()
            if not existing:
                alert = Alert(user_id=researcher.id, **al)
                db.add(alert)
        db.commit()

    print("Demo seed data created successfully.")
    print("\n--- Demo Login Credentials ---")
    print("  Researcher: researcher@bioarbitrage.demo / demo1234")
    print("  Admin:      admin@bioarbitrage.demo / admin1234")


def run():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
