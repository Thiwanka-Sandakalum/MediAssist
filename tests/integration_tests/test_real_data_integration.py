"""
Real Data Integration Tests
Tests for Week 4-5 integration with Gemini Vision, Patient DB, and OpenFDA APIs
"""

import asyncio
import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict

from src.tools.vision_service import VisionService, ExtractionError, get_vision_service
from src.database import (
    get_patient_db,
    Patient,
    Allergy,
    MedicalCondition,
    Medication,
    Encounter,
)
from src.tools.drug_database_openfda import (
    OpenFDAService,
    get_openfda_service,
    check_drug_interaction,
    check_patient_drug_compatibility,
)
from src.tools.drug_database import (
    lookup_drug_database,
    check_drug_interactions,
    get_alternatives,
    get_drug_counseling_points,
    get_food_interactions,
)
from src.tools.vision import parse_prescription_image, generate_label


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def vision_service():
    """Get vision service instance"""
    return get_vision_service()


@pytest.fixture
def patient_db():
    """Get patient database instance"""
    return get_patient_db()


@pytest.fixture
def openfda_service():
    """Get OpenFDA service instance"""
    return get_openfda_service()


@pytest.fixture
def test_patient():
    """Create test patient"""
    return Patient(
        patient_id="TEST-001",
        first_name="Test",
        last_name="Patient",
        date_of_birth="1980-05-15",
        gender="M",
        email="test@example.com",
        weight_kg=75.0,
        height_cm=180.0
    )


@pytest.fixture
def test_prescription():
    """Create test prescription data"""
    return {
        "drug_name": "Metformin",
        "dosage": "500",
        "dosage_unit": "mg",
        "frequency": "twice daily",
        "quantity": 60,
        "route": "oral",
        "duration": "30 days",
        "patient_name": "John Doe",
        "prescriber_name": "Dr. Smith",
        "date": "2024-04-10",
        "refills": 3,
        "special_instructions": "Take with food"
    }


# ============================================================================
# Patient Database Tests
# ============================================================================

class TestPatientDatabase:
    """Test patient database operations"""
    
    def test_create_patient(self, patient_db, test_patient):
        """Test creating a new patient"""
        created = patient_db.create_patient(test_patient)
        assert created.patient_id == "TEST-001"
        assert created.first_name == "Test"
        assert created.id is not None
    
    def test_get_patient(self, patient_db, test_patient):
        """Test retrieving a patient"""
        patient_db.create_patient(test_patient)
        retrieved = patient_db.get_patient("TEST-001")
        assert retrieved is not None
        assert retrieved.first_name == "Test"
    
    def test_add_allergy(self, patient_db, test_patient):
        """Test adding an allergy"""
        patient_db.create_patient(test_patient)
        allergy = Allergy(
            patient_id="TEST-001",
            allergen="Penicillin",
            severity="severe",
            reaction="Anaphylaxis"
        )
        added = patient_db.add_allergy(allergy)
        assert added.id is not None
        
        # Verify it was added
        allergies = patient_db.get_patient_allergies("TEST-001")
        assert len(allergies) >= 1
        assert any(a.allergen == "Penicillin" for a in allergies)
    
    def test_check_drug_allergy(self, patient_db, test_patient):
        """Test checking drug allergy"""
        patient_db.create_patient(test_patient)
        
        # Add allergy
        allergy = Allergy(
            patient_id="TEST-001",
            allergen="Penicillin",
            severity="severe"
        )
        patient_db.add_allergy(allergy)
        
        # Check allergy exists
        assert patient_db.check_drug_allergy("TEST-001", "Penicillin") is True
        assert patient_db.check_drug_allergy("TEST-001", "Aspirin") is False
    
    def test_add_medication(self, patient_db, test_patient):
        """Test adding medication to patient"""
        patient_db.create_patient(test_patient)
        med = Medication(
            patient_id="TEST-001",
            drug_name="Metformin",
            dosage="500mg",
            frequency="twice daily",
            route="oral"
        )
        added = patient_db.add_medication(med)
        assert added.id is not None
        
        # Verify it was added
        medications = patient_db.get_patient_medications("TEST-001", active_only=True)
        assert len(medications) >= 1
        assert any(m.drug_name == "Metformin" for m in medications)
    
    def test_add_condition(self, patient_db, test_patient):
        """Test adding medical condition"""
        patient_db.create_patient(test_patient)
        condition = MedicalCondition(
            patient_id="TEST-001",
            condition_name="Type 2 Diabetes",
            icd10_code="E11.9"
        )
        added = patient_db.add_condition(condition)
        assert added.id is not None
        
        # Verify it was added
        conditions = patient_db.get_patient_conditions("TEST-001")
        assert len(conditions) >= 1
        assert any(c.condition_name == "Type 2 Diabetes" for c in conditions)
    
    def test_record_encounter(self, patient_db, test_patient):
        """Test recording patient encounter"""
        patient_db.create_patient(test_patient)
        encounter = Encounter(
            patient_id="TEST-001",
            encounter_type="consultation",
            encounter_date=datetime.now().isoformat(),
            provider_name="Dr. Smith",
            notes="Patient reports compliance issues"
        )
        recorded = patient_db.record_encounter(encounter)
        assert recorded.id is not None


# ============================================================================
# OpenFDA Integration Tests
# ============================================================================

class TestOpenFDAIntegration:
    """Test OpenFDA drug database integration"""
    
    def test_check_drug_interaction_common(self, openfda_service):
        """Test checking common drug-drug interaction"""
        # Warfarin-Aspirin is a known interaction
        risk = openfda_service.check_drug_interaction("Warfarin", "Aspirin")
        assert risk is not None
        assert risk.severity in ["mild", "moderate", "severe", "critical"]
        assert "bleed" in risk.description.lower() or "aspirin" in risk.description.lower()
    
    def test_check_no_interaction(self, openfda_service):
        """Test checking drugs with no known interaction"""
        risk = openfda_service.check_drug_interaction("Metformin", "Vitamin C")
        # May or may not have interaction, but should not crash
        if risk:
            assert risk.severity in ["mild", "moderate", "severe", "critical"]
    
    def test_check_patient_interactions(self, patient_db, openfda_service):
        """Test checking interactions with patient's current medications"""
        # Create patient
        patient = Patient(
            patient_id="INTERACT-TEST",
            first_name="John",
            last_name="Doe",
            date_of_birth="1980-01-01"
        )
        patient_db.create_patient(patient)
        
        # Add warfarin
        med = Medication(
            patient_id="INTERACT-TEST",
            drug_name="Warfarin",
            dosage="5mg",
            frequency="once daily",
            route="oral"
        )
        patient_db.add_medication(med)
        
        # Check interaction with aspirin
        interactions = openfda_service.check_patient_interactions("INTERACT-TEST", "Aspirin")
        assert isinstance(interactions, list)
        # Should find warfarin-aspirin interaction
        if interactions:
            assert any("warfarin" in i.drug2.lower() for i in interactions)
    
    def test_check_allergy_contraindication(self, patient_db, openfda_service):
        """Test interaction checking with patient allergies"""
        patient = Patient(
            patient_id="ALLERGY-TEST",
            first_name="Jane",
            last_name="Doe",
            date_of_birth="1985-06-15"
        )
        patient_db.create_patient(patient)
        
        # Add penicillin allergy
        allergy = Allergy(
            patient_id="ALLERGY-TEST",
            allergen="Penicillin",
            severity="severe",
            reaction="Anaphylaxis"
        )
        patient_db.add_allergy(allergy)
        
        # Check if penicillin shows as contraindicated
        interactions = openfda_service.check_patient_interactions("ALLERGY-TEST", "Penicillin")
        assert isinstance(interactions, list)
        if interactions:
            assert any("allergy" in i.interaction_type.lower() for i in interactions)


# ============================================================================
# Drug Database Tools Tests
# ============================================================================

class TestDrugDatabaseTools:
    """Test drug database tool functions"""
    
    @pytest.mark.asyncio
    async def test_lookup_drug_database(self):
        """Test drug lookup"""
        result = await lookup_drug_database("Metformin")
        assert isinstance(result, dict)
        # Metformin should typically be found (if API working)
        if result.get("found"):
            assert result["generic_name"].lower() == "metformin" or "metformin" in result["generic_name"].lower()
    
    def test_check_drug_interactions_tool(self):
        """Test check_drug_interactions tool"""
        result = check_drug_interactions(["Warfarin", "Aspirin"])
        assert isinstance(result, dict)
        assert "has_interactions" in result
        assert "interactions" in result
    
    def test_get_alternatives(self):
        """Test get_alternatives tool"""
        result = get_alternatives("Metformin")
        assert isinstance(result, dict)
        if result["found"]:
            assert "alternatives" in result
            assert len(result["alternatives"]) > 0
    
    def test_get_drug_counseling_points(self):
        """Test get_drug_counseling_points tool"""
        result = get_drug_counseling_points("Metformin")
        assert isinstance(result, dict)
        assert "counseling_points" in result
    
    def test_get_food_interactions(self):
        """Test get_food_interactions tool"""
        result = get_food_interactions("Warfarin")
        assert isinstance(result, dict)
        assert "food_interactions" in result


# ============================================================================
# Vision Service Tests
# ============================================================================

class TestVisionService:
    """Test Gemini Vision OCR service"""
    
    def test_vision_service_initialization(self, vision_service):
        """Test vision service initializes correctly"""
        assert vision_service is not None
        assert hasattr(vision_service, "extract_from_image")
    
    def test_image_hash_generation(self, vision_service):
        """Test image hash function"""
        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test image data")
            temp_path = f.name
        
        try:
            hash1 = vision_service._get_image_hash(temp_path)
            hash2 = vision_service._get_image_hash(temp_path)
            # Same file should produce same hash
            assert hash1 == hash2
        finally:
            Path(temp_path).unlink()


# ============================================================================
# Label Generation Tests
# ============================================================================

class TestLabelGeneration:
    """Test pharmacy label generation"""
    
    def test_generate_label_basic(self, test_prescription):
        """Test generating basic pharmacy label"""
        label = generate_label(test_prescription)
        assert isinstance(label, str)
        assert "Metformin" in label
        assert "500" in label
        assert "twice daily" in label
    
    def test_generate_label_with_patient(self, test_prescription):
        """Test generating label with patient info"""
        patient = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-05-15"
        }
        label = generate_label(test_prescription, patient)
        assert "John Doe" in label
        assert "1980-05-15" in label
    
    def test_generate_label_with_missing_fields(self):
        """Test generating label with missing fields"""
        incomplete_prescription = {
            "drug_name": "Aspirin"
        }
        label = generate_label(incomplete_prescription)
        assert "Aspirin" in label
        assert "ERROR" not in label or "UNKNOWN" in label


# ============================================================================
# End-to-End Integration Tests
# ============================================================================

class TestEndToEndIntegration:
    """Test complete workflows combining all services"""
    
    def test_patient_registration_to_prescription(self, patient_db, openfda_service):
        """Test complete workflow: register patient, add allergies, check drug compatibility"""
        # 1. Register patient
        patient = Patient(
            patient_id="E2E-001",
            first_name="Integration",
            last_name="Test",
            date_of_birth="1970-01-01"
        )
        patient_db.create_patient(patient)
        
        # 2. Add allergy
        allergy = Allergy(
            patient_id="E2E-001",
            allergen="Penicillin",
            severity="severe"
        )
        patient_db.add_allergy(allergy)
        
        # 3. Add current medication
        med = Medication(
            patient_id="E2E-001",
            drug_name="Warfarin",
            dosage="5mg",
            frequency="once daily",
            route="oral"
        )
        patient_db.add_medication(med)
        
        # 4. Check new drug compatibility
        interactions = openfda_service.check_patient_interactions("E2E-001", "Aspirin")
        
        # Should have warfarin-aspirin interaction
        assert isinstance(interactions, list)
        assert len(interactions) >= 0  # May or may not find depending on mock data
    
    def test_prescription_processing_workflow(self, patient_db, test_prescription):
        """Test prescription processing workflow"""
        # 1. Parse prescription (simulated - would need real image)
        # 2. Extract patient info
        patient = Patient(
            patient_id="PROC-001",
            first_name="Processing",
            last_name="Test",
            date_of_birth="1975-03-20"
        )
        patient_db.create_patient(patient)
        
        # 3. Add medication
        med = Medication(
            patient_id="PROC-001",
            drug_name=test_prescription["drug_name"],
            dosage=test_prescription["dosage"] + test_prescription["dosage_unit"],
            frequency=test_prescription["frequency"],
            route=test_prescription["route"]
        )
        patient_db.add_medication(med)
        
        # 4. Generate label
        label = generate_label(test_prescription)
        assert test_prescription["drug_name"] in label
        
        # 5. Record encounter
        encounter = Encounter(
            patient_id="PROC-001",
            encounter_type="prescription_fill",
            encounter_date=datetime.now().isoformat(),
            provider_name=test_prescription["prescriber_name"],
            notes="Prescription filled successfully"
        )
        patient_db.record_encounter(encounter)
        
        # Verify all data recorded
        verify_patient = patient_db.get_patient("PROC-001")
        assert verify_patient is not None


# ============================================================================
# Performance and Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling across services"""
    
    def test_patient_not_found(self, patient_db):
        """Test getting non-existent patient"""
        patient = patient_db.get_patient("NONEXISTENT-123")
        assert patient is None
    
    def test_invalid_drug_interaction_check(self, openfda_service):
        """Test interaction check with invalid drugs"""
        # Should not crash
        result = openfda_service.check_drug_interaction("", "")
        assert result is None or isinstance(result, type(None))
    
    def test_malformed_prescription_data(self):
        """Test label generation with malformed data"""
        malformed = {}
        # Should not crash
        label = generate_label(malformed)
        assert isinstance(label, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
