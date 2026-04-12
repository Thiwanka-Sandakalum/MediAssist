"""
Counseling personalisation tool for Counseling Agent
"""

def personalise_counseling(template: dict, patient_profile: dict) -> str:
    """
    Personalise counseling content for a patient.
    Args:
        template (dict): Base counseling template.
        patient_profile (dict): Patient profile data.
    Returns:
        str: Personalised counseling text.
    """
    """
    Simulated counseling personalisation for testing.
    """
    # Handle both dict access and Pydantic attribute access
    if isinstance(template, dict):
        points = template.get('points', ['Take as directed'])
    else:
        points = getattr(template, 'points', ['Take as directed'])
    
    if isinstance(patient_profile, dict):
        age = patient_profile.get('age', 'adult')
    else:
        age = getattr(patient_profile, 'age', 'adult')
    
    points_text = points[0] if isinstance(points, list) and points else 'Take as directed'
    return f"{points_text} (Personalised for {age})"
