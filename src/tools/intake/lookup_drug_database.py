"""
Drug DB lookup tool for Intake Agent
"""

def lookup_drug_database(drug_name: str) -> dict:
    """
    Normalize drug name and fetch canonical drug info.
    Args:
        drug_name (str): Name of the drug.
    Returns:
        dict: Drug information (generic, brand, etc).
    """
    """
    Simulated drug database lookup for testing.
    """
    return {
        "drug_name": drug_name,
        "generic_name": drug_name.lower(),
        "brand_names": [drug_name.capitalize() + " Brand"],
        "indications": ["Infection"]
    }
