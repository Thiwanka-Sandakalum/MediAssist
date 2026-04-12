"""
Patient Database Service
Manages patient records, allergies, medications, conditions, and encounters
Supports both real PostgreSQL and mock in-memory implementations
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from src.config import config
from src.utilities.timeout import with_timeout

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class Patient(BaseModel):
    """Patient profile"""
    id: Optional[str] = None
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None


class Allergy(BaseModel):
    """Drug/food allergy"""
    id: Optional[str] = None
    patient_id: str
    allergen: str
    severity: str  # mild, moderate, severe
    reaction: Optional[str] = None


class MedicalCondition(BaseModel):
    """Patient medical condition/diagnosis"""
    id: Optional[str] = None
    patient_id: str
    condition_name: str
    icd10_code: Optional[str] = None
    status: str = "active"  # active, resolved
    severity: Optional[str] = None


class Medication(BaseModel):
    """Current medication"""
    id: Optional[str] = None
    patient_id: str
    drug_name: str
    drug_code: Optional[str] = None
    dosage: str
    frequency: str
    route: str
    start_date: Optional[str] = None
    status: str = "active"


class Encounter(BaseModel):
    """Patient visit/encounter record"""
    id: Optional[str] = None
    patient_id: str
    encounter_type: str  # consultation, prescription_fill, etc
    encounter_date: str
    provider_name: Optional[str] = None
    notes: Optional[str] = None


# ============================================================================
# Abstract Base Service
# ============================================================================

class PatientDBService(ABC):
    """Abstract base class for patient database services"""
    
    @abstractmethod
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Retrieve patient by ID"""
        pass
    
    @abstractmethod
    def create_patient(self, patient: Patient) -> Patient:
        """Create new patient record"""
        pass
    
    @abstractmethod
    def update_patient(self, patient: Patient) -> Patient:
        """Update patient record"""
        pass
    
    @abstractmethod
    def get_patient_allergies(self, patient_id: str) -> List[Allergy]:
        """Get all allergies for patient"""
        pass
    
    @abstractmethod
    def add_allergy(self, allergy: Allergy) -> Allergy:
        """Add allergy to patient"""
        pass
    
    @abstractmethod
    def get_patient_conditions(self, patient_id: str) -> List[MedicalCondition]:
        """Get all medical conditions for patient"""
        pass
    
    @abstractmethod
    def add_condition(self, condition: MedicalCondition) -> MedicalCondition:
        """Add medical condition to patient"""
        pass
    
    @abstractmethod
    def get_patient_medications(self, patient_id: str, active_only: bool = True) -> List[Medication]:
        """Get medications for patient"""
        pass
    
    @abstractmethod
    def add_medication(self, medication: Medication) -> Medication:
        """Add medication to patient"""
        pass
    
    @abstractmethod
    def record_encounter(self, encounter: Encounter) -> Encounter:
        """Record patient encounter/visit"""
        pass
    
    @abstractmethod
    def check_drug_allergy(self, patient_id: str, drug_name: str) -> bool:
        """Check if patient is allergic to drug"""
        pass


# ============================================================================
# Mock Implementation
# ============================================================================

class MockPatientDB(PatientDBService):
    """In-memory mock database for testing without PostgreSQL"""
    
    def __init__(self):
        """Initialize mock database"""
        self.patients: Dict[str, Patient] = {}
        self.allergies: Dict[str, List[Allergy]] = {}
        self.conditions: Dict[str, List[MedicalCondition]] = {}
        self.medications: Dict[str, List[Medication]] = {}
        self.encounters: Dict[str, List[Encounter]] = {}
        self._seed_test_data()
    
    def _seed_test_data(self):
        """Load sample test data"""
        test_patient = Patient(
            id=str(uuid4()),
            patient_id="PAT-001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1980-05-15",
            gender="M",
            email="john.doe@example.com",
            weight_kg=75.5,
            height_cm=180
        )
        self.patients["PAT-001"] = test_patient
        
        # Add sample allergies
        self.allergies["PAT-001"] = [
            Allergy(
                id=str(uuid4()),
                patient_id="PAT-001",
                allergen="Penicillin",
                severity="severe",
                reaction="Anaphylaxis"
            ),
            Allergy(
                id=str(uuid4()),
                patient_id="PAT-001",
                allergen="Sulfonamides",
                severity="moderate",
                reaction="Rash"
            )
        ]
        
        # Add sample conditions
        self.conditions["PAT-001"] = [
            MedicalCondition(
                id=str(uuid4()),
                patient_id="PAT-001",
                condition_name="Type 2 Diabetes",
                icd10_code="E11.9",
                status="active"
            ),
            MedicalCondition(
                id=str(uuid4()),
                patient_id="PAT-001",
                condition_name="Hypertension",
                icd10_code="I10",
                status="active"
            )
        ]
        
        # Add sample medications
        self.medications["PAT-001"] = [
            Medication(
                id=str(uuid4()),
                patient_id="PAT-001",
                drug_name="Metformin",
                dosage="500mg",
                frequency="twice daily",
                route="oral",
                status="active"
            ),
            Medication(
                id=str(uuid4()),
                patient_id="PAT-001",
                drug_name="Lisinopril",
                dosage="10mg",
                frequency="once daily",
                route="oral",
                status="active"
            )
        ]
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Retrieve patient from mock database"""
        return self.patients.get(patient_id)
    
    def create_patient(self, patient: Patient) -> Patient:
        """Create patient in mock database"""
        patient.id = str(uuid4())
        self.patients[patient.patient_id] = patient
        self.allergies[patient.patient_id] = []
        self.conditions[patient.patient_id] = []
        self.medications[patient.patient_id] = []
        logger.info(f"Created patient: {patient.patient_id}")
        return patient
    
    def update_patient(self, patient: Patient) -> Patient:
        """Update patient in mock database"""
        self.patients[patient.patient_id] = patient
        logger.info(f"Updated patient: {patient.patient_id}")
        return patient
    
    def get_patient_allergies(self, patient_id: str) -> List[Allergy]:
        """Get allergies from mock database"""
        return self.allergies.get(patient_id, [])
    
    def add_allergy(self, allergy: Allergy) -> Allergy:
        """Add allergy to mock database"""
        allergy.id = str(uuid4())
        if allergy.patient_id not in self.allergies:
            self.allergies[allergy.patient_id] = []
        self.allergies[allergy.patient_id].append(allergy)
        logger.info(f"Added allergy for patient {allergy.patient_id}: {allergy.allergen}")
        return allergy
    
    def get_patient_conditions(self, patient_id: str) -> List[MedicalCondition]:
        """Get conditions from mock database"""
        return self.conditions.get(patient_id, [])
    
    def add_condition(self, condition: MedicalCondition) -> MedicalCondition:
        """Add condition to mock database"""
        condition.id = str(uuid4())
        if condition.patient_id not in self.conditions:
            self.conditions[condition.patient_id] = []
        self.conditions[condition.patient_id].append(condition)
        logger.info(f"Added condition for patient {condition.patient_id}: {condition.condition_name}")
        return condition
    
    def get_patient_medications(self, patient_id: str, active_only: bool = True) -> List[Medication]:
        """Get medications from mock database"""
        meds = self.medications.get(patient_id, [])
        if active_only:
            return [m for m in meds if m.status == "active"]
        return meds
    
    def add_medication(self, medication: Medication) -> Medication:
        """Add medication to mock database"""
        medication.id = str(uuid4())
        if medication.patient_id not in self.medications:
            self.medications[medication.patient_id] = []
        self.medications[medication.patient_id].append(medication)
        logger.info(f"Added medication for patient {medication.patient_id}: {medication.drug_name}")
        return medication
    
    def record_encounter(self, encounter: Encounter) -> Encounter:
        """Record encounter in mock database"""
        encounter.id = str(uuid4())
        if encounter.patient_id not in self.encounters:
            self.encounters[encounter.patient_id] = []
        self.encounters[encounter.patient_id].append(encounter)
        logger.info(f"Recorded encounter for patient {encounter.patient_id}")
        return encounter
    
    def check_drug_allergy(self, patient_id: str, drug_name: str) -> bool:
        """Check if patient is allergic to drug"""
        allergies = self.get_patient_allergies(patient_id)
        drug_lower = drug_name.lower()
        for allergy in allergies:
            if allergy.allergen.lower() == drug_lower:
                return True
        return False


# ============================================================================
# PostgreSQL Implementation
# ============================================================================

class PostgresPatientDB(PatientDBService):
    """PostgreSQL-backed patient database service"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize PostgreSQL connection
        
        Args:
            connection_string: PostgreSQL connection string (uses config if not provided)
        """
        self.connection_string = connection_string or config.DATABASE_URL
        self.pool = SimpleConnectionPool(1, 10, self.connection_string)
        logger.info("Initialized PostgreSQL patient database connection")
    
    def _get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)
    
    @with_timeout(seconds=10)
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Retrieve patient from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                "SELECT * FROM patients WHERE patient_id = %s",
                (patient_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            self._return_connection(conn)
            
            if row:
                return Patient(**row)
            return None
        except psycopg2.Error as e:
            logger.error(f"Database error retrieving patient: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving patient: {e}")
            return None
    
    @with_timeout(seconds=10)
    def create_patient(self, patient: Patient) -> Patient:
        """Create patient in PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, 
                   gender, email, phone, weight_kg, height_cm)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (patient.patient_id, patient.first_name, patient.last_name,
                 patient.date_of_birth, patient.gender, patient.email,
                 patient.phone, patient.weight_kg, patient.height_cm)
            )
            patient.id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            self._return_connection(conn)
            
            logger.info(f"Created patient in DB: {patient.patient_id}")
            return patient
        except psycopg2.Error as e:
            logger.error(f"Database error creating patient: {e}")
            raise
    
    @with_timeout(seconds=10)
    def update_patient(self, patient: Patient) -> Patient:
        """Update patient in PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """UPDATE patients SET first_name=%s, last_name=%s, 
                   gender=%s, email=%s, phone=%s, weight_kg=%s, height_cm=%s
                   WHERE patient_id=%s""",
                (patient.first_name, patient.last_name, patient.gender,
                 patient.email, patient.phone, patient.weight_kg,
                 patient.height_cm, patient.patient_id)
            )
            conn.commit()
            cursor.close()
            self._return_connection(conn)
            
            logger.info(f"Updated patient: {patient.patient_id}")
            return patient
        except psycopg2.Error as e:
            logger.error(f"Database error updating patient: {e}")
            raise
    
    @with_timeout(seconds=10)
    def get_patient_allergies(self, patient_id: str) -> List[Allergy]:
        """Get allergies from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                """SELECT * FROM patient_allergies 
                   WHERE patient_id = (SELECT id FROM patients WHERE patient_id=%s)
                   AND is_active = TRUE""",
                (patient_id,)
            )
            rows = cursor.fetchall()
            cursor.close()
            self._return_connection(conn)
            
            return [Allergy(**row) for row in rows]
        except psycopg2.Error as e:
            logger.error(f"Database error retrieving allergies: {e}")
            return []
    
    @with_timeout(seconds=10)
    def add_allergy(self, allergy: Allergy) -> Allergy:
        """Add allergy to PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO patient_allergies (patient_id, allergen, severity, reaction)
                   VALUES ((SELECT id FROM patients WHERE patient_id=%s),
                           %s, %s, %s)
                   RETURNING id""",
                (allergy.patient_id, allergy.allergen, allergy.severity, allergy.reaction)
            )
            allergy.id = str(cursor.fetchone()[0])
            conn.commit()
            cursor.close()
            self._return_connection(conn)
            
            logger.info(f"Added allergy: {allergy.allergen}")
            return allergy
        except psycopg2.Error as e:
            logger.error(f"Database error adding allergy: {e}")
            raise
    
    @with_timeout(seconds=10)
    def get_patient_conditions(self, patient_id: str) -> List[MedicalCondition]:
        """Get conditions from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                """SELECT * FROM patient_conditions
                   WHERE patient_id = (SELECT id FROM patients WHERE patient_id=%s)
                   AND is_active = TRUE""",
                (patient_id,)
            )
            rows = cursor.fetchall()
            cursor.close()
            self._return_connection(conn)
            
            return [MedicalCondition(**row) for row in rows]
        except psycopg2.Error as e:
            logger.error(f"Database error retrieving conditions: {e}")
            return []
    
    @with_timeout(seconds=10)
    def add_condition(self, condition: MedicalCondition) -> MedicalCondition:
        """Add condition to PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO patient_conditions (patient_id, condition_name, icd10_code, status, severity)
                   VALUES ((SELECT id FROM patients WHERE patient_id=%s),
                           %s, %s, %s, %s)
                   RETURNING id""",
                (condition.patient_id, condition.condition_name,
                 condition.icd10_code, condition.status, condition.severity)
            )
            condition.id = str(cursor.fetchone()[0])
            conn.commit()
            cursor.close()
            self._return_connection(conn)
            
            logger.info(f"Added condition: {condition.condition_name}")
            return condition
        except psycopg2.Error as e:
            logger.error(f"Database error adding condition: {e}")
            raise
    
    @with_timeout(seconds=10)
    def get_patient_medications(self, patient_id: str, active_only: bool = True) -> List[Medication]:
        """Get medications from PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """SELECT * FROM patient_medications
                       WHERE patient_id = (SELECT id FROM patients WHERE patient_id=%s)"""
            if active_only:
                query += " AND is_active = TRUE"
            
            cursor.execute(query, (patient_id,))
            rows = cursor.fetchall()
            cursor.close()
            self._return_connection(conn)
            
            return [Medication(**row) for row in rows]
        except psycopg2.Error as e:
            logger.error(f"Database error retrieving medications: {e}")
            return []
    
    @with_timeout(seconds=10)
    def add_medication(self, medication: Medication) -> Medication:
        """Add medication to PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO patient_medications (patient_id, drug_name, drug_code, 
                   dosage, frequency, route, start_date, status)
                   VALUES ((SELECT id FROM patients WHERE patient_id=%s),
                           %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (medication.patient_id, medication.drug_name, medication.drug_code,
                 medication.dosage, medication.frequency, medication.route,
                 medication.start_date, medication.status)
            )
            medication.id = str(cursor.fetchone()[0])
            conn.commit()
            cursor.close()
            self._return_connection(conn)
            
            logger.info(f"Added medication: {medication.drug_name}")
            return medication
        except psycopg2.Error as e:
            logger.error(f"Database error adding medication: {e}")
            raise
    
    @with_timeout(seconds=10)
    def record_encounter(self, encounter: Encounter) -> Encounter:
        """Record encounter in PostgreSQL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO patient_encounters (patient_id, encounter_type, encounter_date,
                   provider_name, notes)
                   VALUES ((SELECT id FROM patients WHERE patient_id=%s),
                           %s, %s, %s, %s)
                   RETURNING id""",
                (encounter.patient_id, encounter.encounter_type,
                 encounter.encounter_date, encounter.provider_name, encounter.notes)
            )
            encounter.id = str(cursor.fetchone()[0])
            conn.commit()
            cursor.close()
            self._return_connection(conn)
            
            logger.info(f"Recorded encounter for patient: {encounter.patient_id}")
            return encounter
        except psycopg2.Error as e:
            logger.error(f"Database error recording encounter: {e}")
            raise
    
    @with_timeout(seconds=10)
    def check_drug_allergy(self, patient_id: str, drug_name: str) -> bool:
        """Check if patient is allergic to drug"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT COUNT(*) FROM patient_allergies
                   WHERE patient_id = (SELECT id FROM patients WHERE patient_id=%s)
                   AND LOWER(allergen) = LOWER(%s)
                   AND is_active = TRUE""",
                (patient_id, drug_name)
            )
            count = cursor.fetchone()[0]
            cursor.close()
            self._return_connection(conn)
            
            return count > 0
        except psycopg2.Error as e:
            logger.error(f"Database error checking allergy: {e}")
            return False


# ============================================================================
# Factory and Singleton
# ============================================================================

_db_service: Optional[PatientDBService] = None


def get_patient_db() -> PatientDBService:
    """
    Get or initialize patient database service
    Returns PostgreSQL if DATABASE_URL configured, otherwise mock
    """
    global _db_service
    if _db_service is None:
        if config.DATABASE_URL and "postgresql" in config.DATABASE_URL:
            try:
                _db_service = PostgresPatientDB()
                logger.info("Using PostgreSQL patient database")
            except Exception as e:
                logger.warning(f"Failed to connect to PostgreSQL: {e}, falling back to mock")
                _db_service = MockPatientDB()
        else:
            _db_service = MockPatientDB()
            logger.info("Using mock patient database")
    return _db_service
