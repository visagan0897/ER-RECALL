from datetime import date
from pathlib import Path

import yaml
from psycopg.types.json import Jsonb

from database import get_connection


ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "fixtures"
PATIENTS_DIR = FIXTURES_DIR / "patients"


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def parse_date(value) -> date:
    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value))


def load_facilities(cursor):
    data = load_yaml(FIXTURES_DIR / "facilities.yaml")

    facility_ids = {}

    for facility in data["facilities"]:
        cursor.execute(
            """
            INSERT INTO facilities (code, name, city)
            VALUES (%s, %s, %s)
            ON CONFLICT (code)
            DO UPDATE SET
                name = EXCLUDED.name,
                city = EXCLUDED.city
            RETURNING id;
            """,
            (
                facility["code"],
                facility["name"],
                facility.get("city"),
            ),
        )

        facility_ids[facility["code"]] = cursor.fetchone()[0]

    return facility_ids


def load_patient(cursor, data):
    patient = data["patient"]

    cursor.execute(
        """
        INSERT INTO patients (
            prototype_code,
            full_name,
            date_of_birth,
            sex,
            is_synthetic
        )
        VALUES (%s, %s, %s, %s, true)
        ON CONFLICT (prototype_code)
        DO UPDATE SET
            full_name = EXCLUDED.full_name,
            date_of_birth = EXCLUDED.date_of_birth,
            sex = EXCLUDED.sex,
            is_synthetic = true
        RETURNING id;
        """,
        (
            data["prototype_code"],
            patient["full_name"],
            parse_date(patient["date_of_birth"]),
            patient["sex"],
        ),
    )

    return cursor.fetchone()[0]


def load_document(cursor, patient_id, facility_ids, document):
    facility_id = facility_ids[document["facility_code"]]
    document_date = parse_date(document["document_date"])

    cursor.execute(
        """
        INSERT INTO source_documents (
            patient_id,
            facility_id,
            doc_key,
            document_type,
            document_date,
            title,
            body_text
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (doc_key)
        DO UPDATE SET
            patient_id = EXCLUDED.patient_id,
            facility_id = EXCLUDED.facility_id,
            document_type = EXCLUDED.document_type,
            document_date = EXCLUDED.document_date,
            title = EXCLUDED.title,
            body_text = EXCLUDED.body_text
        RETURNING id;
        """,
        (
            patient_id,
            facility_id,
            document["doc_key"],
            document["document_type"],
            document_date,
            document["title"],
            document["body"],
        ),
    )

    return cursor.fetchone()[0], document_date


def load_facts(
    cursor,
    patient_id,
    source_document_id,
    document_date,
    facts,
):
    for fact in facts:
        cursor.execute(
            """
            DELETE FROM clinical_facts
            WHERE patient_id = %s
              AND source_document_id = %s;
            """,
            (
                patient_id,
                source_document_id,
            ),
        )

        break

    for fact in facts:
        cursor.execute(
            """
            INSERT INTO clinical_facts (
                patient_id,
                source_document_id,
                category,
                normalized_key,
                assertion,
                display_text,
                attributes,
                recorded_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                patient_id,
                source_document_id,
                fact["category"],
                fact["normalized_key"],
                fact["assertion"],
                fact["display_text"],
                Jsonb(fact.get("attributes", {})),
                document_date,
            ),
        )


def seed():
    patient_files = sorted(PATIENTS_DIR.glob("*.yaml"))

    if not patient_files:
        raise RuntimeError("No patient fixture files found.")

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            facility_ids = load_facilities(cursor)

            patient_count = 0
            document_count = 0
            fact_count = 0

            for path in patient_files:
                data = load_yaml(path)

                patient_id = load_patient(cursor, data)
                patient_count += 1

                for document in data["documents"]:
                    source_document_id, document_date = load_document(
                        cursor,
                        patient_id,
                        facility_ids,
                        document,
                    )

                    document_count += 1

                    load_facts(
                        cursor,
                        patient_id,
                        source_document_id,
                        document_date,
                        document.get("facts", []),
                    )

                    fact_count += len(document.get("facts", []))

        conn.commit()

        print("Fixture seeding passed.")
        print(f"Patients: {patient_count}")
        print(f"Documents: {document_count}")
        print(f"Facts: {fact_count}")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    seed()