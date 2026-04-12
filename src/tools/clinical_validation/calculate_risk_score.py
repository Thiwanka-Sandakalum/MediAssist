"""
Risk score calculator for Clinical Validation Agent
"""

def calculate_risk_score(reports: list[dict]) -> float:
    """
    Calculate weighted risk score from reports.
    Args:
        reports (list): List of safety/interaction reports with interactions, contraindications, etc.
    Returns:
        float: Risk score (0.0 - 1.0).
    """
    """
    Calculate risk score based on severity of findings.
    """
    risk_score = 0.0
    
    # Evaluate each report
    for report in reports:
        if isinstance(report, dict):
            # Check interactions
            interactions = report.get("interactions", [])
            for interaction in interactions:
                severity = interaction.get("severity", "").upper()
                if severity == "SEVERE":
                    risk_score = max(risk_score, 0.9)
                elif severity == "MODERATE":
                    risk_score = max(risk_score, 0.6)
                elif severity == "MILD":
                    risk_score = max(risk_score, 0.3)
            
            # Check contraindications
            contraindications = report.get("contraindications", [])
            if contraindications:
                risk_score = max(risk_score, 0.85)
            
            # Check allergies
            allergies = report.get("allergies", [])
            if allergies:
                risk_score = max(risk_score, 0.9)
            
            # Check dosage safety
            if not report.get("dosage_safe", True):
                risk_score = max(risk_score, 0.7)
    
    return min(risk_score, 1.0)  # Cap at 1.0
