/**
 * Drug Name Normalization Utility
 * Handles common drug name variations and brand-to-generic mapping
 * 
 * WHY THIS MATTERS:
 * Users say "paracetamol" or "Panadol", but FDA uses "acetaminophen"
 * This normalizer ensures we search FDA with the correct generic name
 */

/**
 * Brand name to generic name mapping
 * Extend this as needed for common brand names
 */
const BRAND_TO_GENERIC: Record<string, string> = {
    // Acetaminophen (Paracetamol)
    paracetamol: 'acetaminophen',
    panadol: 'acetaminophen',
    tylenol: 'acetaminophen',
    calpol: 'acetaminophen',

    // Ibuprofen
    advil: 'ibuprofen',
    motrin: 'ibuprofen',
    nurofen: 'ibuprofen',

    // Aspirin
    aspro: 'aspirin',
    disprin: 'aspirin',

    // Diclofenac
    voltaren: 'diclofenac',

    // Omeprazole
    prilosec: 'omeprazole',
    losec: 'omeprazole',

    // Metformin
    glucophage: 'metformin',

    // Atorvastatin
    lipitor: 'atorvastatin',

    // Simvastatin
    zocor: 'simvastatin',

    // Amlodipine
    norvasc: 'amlodipine',

    // Lisinopril
    prinivil: 'lisinopril',
    zestril: 'lisinopril',
};

/**
 * Normalize drug name to generic name for FDA API search
 * 
 * @param drugName - User-provided drug name (can be brand or generic)
 * @returns Normalized generic drug name
 */
export function normalizeDrugName(drugName: string): string {
    // Convert to lowercase and trim whitespace
    const cleaned = drugName.toLowerCase().trim();

    // Remove common suffixes (e.g., "500mg", "tablets")
    const withoutSuffix = cleaned
        .replace(/\s+(tablet|capsule|pill|mg|mcg|ml|cream|gel|ointment|syrup)s?$/i, '')
        .trim();

    // Check if it's a known brand name
    if (BRAND_TO_GENERIC[withoutSuffix]) {
        return BRAND_TO_GENERIC[withoutSuffix];
    }

    // Return as-is (assuming it's already generic or will be handled by FDA search)
    return withoutSuffix;
}

/**
 * Check if a drug name is a known brand name
 */
export function isBrandName(drugName: string): boolean {
    const cleaned = drugName.toLowerCase().trim();
    return cleaned in BRAND_TO_GENERIC;
}

/**
 * Get generic name from brand name
 * Returns undefined if not a known brand
 */
export function getGenericName(brandName: string): string | undefined {
    const cleaned = brandName.toLowerCase().trim();
    return BRAND_TO_GENERIC[cleaned];
}

/**
 * Extract drug name from user query
 * Handles queries like "What are the side effects of paracetamol?"
 */
export function extractDrugNameFromQuery(query: string): string | null {
    // Common patterns to extract drug names
    const patterns = [
        /(?:side effects? of|information about|tell me about|what is)\s+([a-z]+)/i,
        /([a-z]+)\s+side effects?/i,
        /(?:drug|medicine|medication)\s+([a-z]+)/i,
    ];

    for (const pattern of patterns) {
        const match = query.match(pattern);
        if (match && match[1]) {
            return normalizeDrugName(match[1]);
        }
    }

    return null;
}
