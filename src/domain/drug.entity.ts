/**
 * Domain Entity: Drug Information
 * Represents validated drug data from openFDA
 */

export interface DrugEntity {
    /**
     * Generic drug name (e.g., "acetaminophen")
     */
    genericName: string;

    /**
     * Brand names associated with the drug
     */
    brandNames: string[];

    /**
     * Purpose or indications for use
     */
    purpose?: string;

    /**
     * Active ingredients and their strengths
     */
    activeIngredients?: string[];

    /**
     * Warnings and precautions
     */
    warnings?: string[];

    /**
     * Adverse reactions / side effects
     */
    adverseReactions?: string[];

    /**
     * Drug interactions
     */
    drugInteractions?: string[];

    /**
     * Dosage and administration (generic info only, no personalized dosing)
     */
    dosageInfo?: string[];

    /**
     * When not to use this drug
     */
    contraindications?: string[];

    /**
     * How the drug works (mechanism of action)
     */
    pharmacology?: string[];
}

/**
 * Raw openFDA Drug Label Response
 * Represents the actual structure returned by openFDA API
 */
export interface OpenFDADrugLabelResult {
    openfda?: {
        generic_name?: string[];
        brand_name?: string[];
        manufacturer_name?: string[];
    };
    purpose?: string[];
    active_ingredient?: string[];
    warnings?: string[];
    adverse_reactions?: string[];
    drug_interactions?: string[];
    dosage_and_administration?: string[];
    contraindications?: string[];
    indications_and_usage?: string[];
    clinical_pharmacology?: string[];
    description?: string[];
}

/**
 * OpenFDA API Response Wrapper
 */
export interface OpenFDAResponse {
    meta?: {
        disclaimer?: string;
        terms?: string;
        license?: string;
        last_updated?: string;
        results?: {
            skip: number;
            limit: number;
            total: number;
        };
    };
    results?: OpenFDADrugLabelResult[];
}
