from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "fixtures"
PATIENTS_DIR = FIXTURES_DIR / "patients"

ALLOWED_DOCUMENT_TYPES = {
    "discharge_summary",
    "clinic_note",
    "medication_list",
    "operative_note",
    "ed_note",
}

ALLOWED_CATEGORIES = {
    "allergy",
    "medication",
    "condition",
    "surgery",
    "hospitalization",
    "blood_group",
}

ALLOWED_ASSERTIONS = {
    "present",
    "absent",
}

ALLOWED_HEADINGS = {
    "Allergies",
    "Medications",
    "Problems",
    "Past Surgical History",
    "Admissions",
    "Blood Group",
    "Clinical Summary",
}

EXPECTED_CANARIES = {
    "PT-A": "REF-A-7731",
    "PT-B": "REF-B-4402",
    "PT-C": "REF-C-9158",
    "PT-D": "REF-D-2267",
}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def validate_facilities():
    path = FIXTURES_DIR / "facilities.yaml"
    data = load_yaml(path)

    assert isinstance(data, dict), "facilities.yaml must contain a mapping"

    facilities = data.get("facilities")
    assert isinstance(facilities, list), "facilities must be a list"

    codes = set()

    for facility in facilities:
        code = facility.get("code")
        name = facility.get("name")

        assert code, "Facility code is required"
        assert name, f"Facility name is required for {code}"
        assert code not in codes, f"Duplicate facility code: {code}"

        codes.add(code)


def validate_patient(path: Path):
    data = load_yaml(path)

    assert isinstance(data, dict), f"{path.name}: root must be a mapping"

    patient_code = data.get("prototype_code")
    assert patient_code, f"{path.name}: prototype_code is required"

    expected_canary = EXPECTED_CANARIES.get(patient_code)
    assert expected_canary, f"{path.name}: unexpected prototype_code {patient_code}"

    documents = data.get("documents")
    assert isinstance(documents, list), f"{path.name}: documents must be a list"
    assert documents, f"{path.name}: at least one document is required"

    document_keys = set()
    canary_documents = 0

    for document in documents:
        doc_key = document.get("doc_key")
        facility_code = document.get("facility_code")
        document_type = document.get("document_type")
        body = document.get("body", "")
        facts = document.get("facts", [])

        assert doc_key, f"{path.name}: document doc_key is required"

        assert doc_key not in document_keys, (
            f"{path.name}: duplicate doc_key {doc_key}"
        )

        document_keys.add(doc_key)

        assert facility_code, (
            f"{path.name} {doc_key}: facility_code is required"
        )

        assert document_type in ALLOWED_DOCUMENT_TYPES, (
            f"{path.name} {doc_key}: invalid document_type "
            f"{document_type!r}"
        )

        assert isinstance(body, str), (
            f"{path.name} {doc_key}: body must be text"
        )

        if expected_canary in body:
            canary_documents += 1

        for line in body.splitlines():
            stripped = line.strip()

            if stripped.startswith("## "):
                heading = stripped[3:].strip()

                assert heading in ALLOWED_HEADINGS, (
                    f"{path.name} {doc_key}: invalid section heading "
                    f"{heading!r}"
                )

        assert isinstance(facts, list), (
            f"{path.name} {doc_key}: facts must be a list"
        )

        for fact in facts:
            category = fact.get("category")
            normalized_key = fact.get("normalized_key")
            assertion = fact.get("assertion")
            display_text = fact.get("display_text")
            attributes = fact.get("attributes")

            assert category in ALLOWED_CATEGORIES, (
                f"{path.name} {doc_key}: invalid category "
                f"{category!r}"
            )

            assert normalized_key, (
                f"{path.name} {doc_key}: normalized_key is required"
            )

            assert assertion in ALLOWED_ASSERTIONS, (
                f"{path.name} {doc_key}: invalid assertion "
                f"{assertion!r}"
            )

            assert display_text, (
                f"{path.name} {doc_key}: display_text is required"
            )

            assert isinstance(attributes, dict), (
                f"{path.name} {doc_key}: attributes must be a mapping"
            )

            if normalized_key == "*":
                assert assertion == "absent", (
                    f"{path.name} {doc_key}: '*' normalized_key "
                    "must use assertion='absent'"
                )

    assert canary_documents >= 1, (
        f"{path.name}: expected canary {expected_canary!r} "
        "in at least one document"
    )

    return patient_code, len(documents)


def main():
    validate_facilities()

    patient_files = sorted(PATIENTS_DIR.glob("*.yaml"))

    assert patient_files, "No patient fixture files found"

    patient_codes = set()
    total_documents = 0

    for path in patient_files:
        patient_code, document_count = validate_patient(path)

        assert patient_code not in patient_codes, (
            f"Duplicate prototype_code: {patient_code}"
        )

        patient_codes.add(patient_code)
        total_documents += document_count

    expected_codes = set(EXPECTED_CANARIES)

    assert patient_codes == expected_codes, (
        f"Expected patient codes {sorted(expected_codes)}, "
        f"found {sorted(patient_codes)}"
    )

    print("Fixture validation passed.")
    print(f"Patients: {len(patient_codes)}")
    print(f"Documents: {total_documents}")
    print(f"Canaries: {len(EXPECTED_CANARIES)}")


if __name__ == "__main__":
    main()