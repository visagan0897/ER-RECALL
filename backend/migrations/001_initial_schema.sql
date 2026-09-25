CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE clinicians (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username text UNIQUE NOT NULL,
    display_name text NOT NULL,
    password_hash text NOT NULL,
    role text NOT NULL CHECK (role IN ('clinician', 'admin')),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);


CREATE TABLE patients (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    prototype_code text UNIQUE NOT NULL,
    full_name text NOT NULL,
    date_of_birth date NOT NULL,
    sex text NOT NULL CHECK (sex IN ('female', 'male', 'other', 'unknown')),
    is_synthetic boolean NOT NULL CHECK (is_synthetic = true),
    created_at timestamptz NOT NULL DEFAULT now()
);


CREATE TABLE facilities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text UNIQUE NOT NULL,
    name text NOT NULL,
    city text
);


CREATE TABLE source_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id uuid NOT NULL REFERENCES patients(id),
    facility_id uuid NOT NULL REFERENCES facilities(id),
    doc_key text UNIQUE NOT NULL,
    document_type text NOT NULL CHECK (
        document_type IN (
            'discharge_summary',
            'clinic_note',
            'medication_list',
            'operative_note',
            'ed_note'
        )
    ),
    document_date date NOT NULL,
    title text NOT NULL,
    body_text text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (id, patient_id)
);


CREATE TABLE clinical_facts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id uuid NOT NULL,
    source_document_id uuid NOT NULL,

    category text NOT NULL CHECK (
        category IN (
            'allergy',
            'medication',
            'condition',
            'surgery',
            'hospitalization',
            'blood_group'
        )
    ),

    normalized_key text NOT NULL,
    assertion text NOT NULL CHECK (assertion IN ('present', 'absent')),
    display_text text NOT NULL,
    attributes jsonb NOT NULL DEFAULT '{}',
    recorded_date date NOT NULL,

    CHECK (normalized_key <> '*' OR assertion = 'absent'),

    FOREIGN KEY (source_document_id, patient_id)
        REFERENCES source_documents(id, patient_id)
);


CREATE TABLE biometric_credentials (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id uuid NOT NULL REFERENCES patients(id),
    label text UNIQUE NOT NULL,
    credential_id bytea UNIQUE NOT NULL,
    public_key bytea NOT NULL,
    sign_count bigint NOT NULL DEFAULT 0,
    user_handle bytea UNIQUE NOT NULL,
    transports text[],
    created_by uuid REFERENCES clinicians(id),
    created_at timestamptz NOT NULL DEFAULT now()
);


CREATE TABLE scanner_devices (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    label text NOT NULL,
    token_hash text UNIQUE,
    paired_by uuid REFERENCES clinicians(id),
    paired_at timestamptz,
    revoked_at timestamptz
);


CREATE TABLE scan_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinician_id uuid NOT NULL REFERENCES clinicians(id),
    challenge bytea NOT NULL,
    status text NOT NULL CHECK (
        status IN (
            'pending',
            'completed',
            'failed',
            'expired',
            'consumed',
            'cancelled'
        )
    ),
    method text CHECK (method IN ('webauthn', 'simulated')),
    patient_id uuid REFERENCES patients(id),
    scanner_device_id uuid REFERENCES scanner_devices(id),
    failure_code text,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,
    completed_at timestamptz,
    consumed_at timestamptz
);


CREATE TABLE patient_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id uuid NOT NULL REFERENCES patients(id),
    clinician_id uuid NOT NULL REFERENCES clinicians(id),
    scan_request_id uuid UNIQUE REFERENCES scan_requests(id),
    identification_method text NOT NULL CHECK (
        identification_method IN ('webauthn', 'simulated')
    ),
    status text NOT NULL CHECK (
        status IN ('active', 'closed', 'expired')
    ),
    index_status text NOT NULL CHECK (
        index_status IN ('ready', 'fts_only', 'empty', 'failed')
    ),
    created_at timestamptz NOT NULL DEFAULT now(),
    last_activity_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    closed_at timestamptz,
    close_reason text CHECK (
        close_reason IS NULL OR close_reason IN (
            'clinician_closed',
            'superseded',
            'idle_timeout',
            'absolute_timeout',
            'server_restart'
        )
    ),

    UNIQUE (id, patient_id)
);


CREATE UNIQUE INDEX uq_patient_sessions_active_clinician
    ON patient_sessions (clinician_id)
    WHERE status = 'active';


CREATE TABLE audit_events (
    id bigserial PRIMARY KEY,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    request_id text,
    actor_type text NOT NULL CHECK (
        actor_type IN ('clinician', 'scanner', 'system')
    ),
    actor_id uuid,
    event_type text NOT NULL,
    patient_id uuid,
    patient_session_id uuid,
    outcome text NOT NULL CHECK (
        outcome IN ('success', 'failure')
    ),
    detail jsonb NOT NULL DEFAULT '{}'
);


CREATE TABLE session_chunks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_session_id uuid NOT NULL,
    patient_id uuid NOT NULL,

    source_document_id uuid NOT NULL,

    chunk_index int NOT NULL,
    section_heading text NOT NULL,
    category text,
    content text NOT NULL,

    content_tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('english', content)
    ) STORED,

    embedding vector(768),

    created_at timestamptz NOT NULL DEFAULT now(),

    FOREIGN KEY (patient_session_id, patient_id)
        REFERENCES patient_sessions(id, patient_id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_document_id, patient_id)
        REFERENCES source_documents(id, patient_id)
);


CREATE INDEX idx_session_chunks_patient_session
    ON session_chunks (patient_session_id);


CREATE TABLE session_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_session_id uuid NOT NULL REFERENCES patient_sessions(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('clinician', 'assistant')),
    content text NOT NULL,
    answer_status text CHECK (
        answer_status IS NULL OR answer_status IN (
            'answered',
            'not_documented',
            'out_of_scope',
            'grounding_failed',
            'ai_unavailable'
        )
    ),
    citations jsonb,
    related_conflicts jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);