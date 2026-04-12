-- MediAssist Patient Database Schema
-- PostgreSQL DDL for patient management

-- Extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR(50) UNIQUE NOT NULL,  -- External patient ID from healthcare system
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10),  -- M, F, O, U
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    blood_type VARCHAR(5),  -- O+, O-, A+, A-, B+, B-, AB+, AB-
    weight_kg DECIMAL(5, 2),
    height_cm DECIMAL(5, 2),
    bmi DECIMAL(5, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_by UUID,
    notes TEXT
);

-- Patient Allergies
CREATE TABLE IF NOT EXISTS patient_allergies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    allergen VARCHAR(200) NOT NULL,
    severity VARCHAR(20),  -- mild, moderate, severe
    reaction TEXT,  -- Description of allergic reaction
    onset_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(patient_id, allergen)
);

-- Medical Conditions (Diagnoses)
CREATE TABLE IF NOT EXISTS patient_conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    condition_code VARCHAR(20),  -- ICD-10 code
    condition_name VARCHAR(200) NOT NULL,
    icd10_code VARCHAR(10),
    onset_date DATE,
    status VARCHAR(50),  -- active, resolved, remission
    severity VARCHAR(20),  -- mild, moderate, severe
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Current Medications (Active Prescription List)
CREATE TABLE IF NOT EXISTS patient_medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    drug_name VARCHAR(200) NOT NULL,
    drug_code VARCHAR(20),  -- NDC or similar
    dosage VARCHAR(50) NOT NULL,  -- e.g., "500mg"
    frequency VARCHAR(100) NOT NULL,  -- e.g., "3 times daily"
    route VARCHAR(50),  -- oral, intravenous, topical, etc
    start_date DATE NOT NULL,
    end_date DATE,
    indication VARCHAR(200),  -- Why the drug is prescribed
    prescriber_name VARCHAR(200),
    prescriber_license VARCHAR(50),
    status VARCHAR(50),  -- active, completed, discontinued
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patient Encounters (Visits, Consultations)
CREATE TABLE IF NOT EXISTS patient_encounters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_type VARCHAR(50),  -- consultation, prescription_fill, lab_work, etc
    encounter_date TIMESTAMP NOT NULL,
    provider_name VARCHAR(200),
    provider_id VARCHAR(50),
    facility VARCHAR(200),
    notes TEXT,
    chief_complaint VARCHAR(500),
    assessment TEXT,
    plan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drug Interaction Cache (from OpenFDA)
CREATE TABLE IF NOT EXISTS drug_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug1_name VARCHAR(200) NOT NULL,
    drug1_code VARCHAR(20),
    drug2_name VARCHAR(200) NOT NULL,
    drug2_code VARCHAR(20),
    severity VARCHAR(20),  -- mild, moderate, severe, critical
    interaction_type VARCHAR(100),  -- drug-drug, food-drug, disease-drug
    description TEXT,
    management_recommendation TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(drug1_code, drug2_code)
);

-- Patient Pharmacy Records (Prescription Fill History)
CREATE TABLE IF NOT EXISTS pharmacy_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    prescription_id VARCHAR(100) UNIQUE,
    drug_name VARCHAR(200) NOT NULL,
    quantity_dispensed INT,
    fill_date TIMESTAMP NOT NULL,
    dui_score DECIMAL(3, 2),  -- Daily Unit Intake score
    naloxone_dispensed BOOLEAN DEFAULT FALSE,
    pharmacist_name VARCHAR(200),
    pharmacist_license VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clinical Observations (Vital Signs, Lab Results, etc)
CREATE TABLE IF NOT EXISTS patient_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    observation_type VARCHAR(100),  -- vital_sign, lab_result, symptom, etc
    observation_date TIMESTAMP NOT NULL,
    value VARCHAR(100),
    unit VARCHAR(50),
    reference_range VARCHAR(100),
    status VARCHAR(50),  -- normal, abnormal, critical
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Regulatory Submissions Log (PMS Sync, FDA Reporting)
CREATE TABLE IF NOT EXISTS regulatory_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    submission_type VARCHAR(100),  -- pms_sync, fda_report, etc
    reference_id VARCHAR(200),
    submission_date TIMESTAMP,
    status VARCHAR(50),  -- pending, submitted, acknowledged, error
    response_text TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_patients_patient_id ON patients(patient_id);
CREATE INDEX idx_allergies_patient_id ON patient_allergies(patient_id);
CREATE INDEX idx_conditions_patient_id ON patient_conditions(patient_id);
CREATE INDEX idx_medications_patient_id ON patient_medications(patient_id);
CREATE INDEX idx_medications_active ON patient_medications(patient_id, is_active);
CREATE INDEX idx_encounters_patient_id ON patient_encounters(patient_id);
CREATE INDEX idx_interactions_drugs ON drug_interactions(drug1_code, drug2_code);
CREATE INDEX idx_pharmacy_patient_id ON pharmacy_records(patient_id);
CREATE INDEX idx_observations_patient_id ON patient_observations(patient_id);
CREATE INDEX idx_submissions_patient_id ON regulatory_submissions(patient_id);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers
CREATE TRIGGER patients_update_trigger
BEFORE UPDATE ON patients FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER allergies_update_trigger
BEFORE UPDATE ON patient_allergies FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER conditions_update_trigger
BEFORE UPDATE ON patient_conditions FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER medications_update_trigger
BEFORE UPDATE ON patient_medications FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER encounters_update_trigger
BEFORE UPDATE ON patient_encounters FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER submissions_update_trigger
BEFORE UPDATE ON regulatory_submissions FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
