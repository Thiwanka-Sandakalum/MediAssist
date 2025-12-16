import { DrugEntity, OpenFDADrugLabelResult } from './drug.entity';
import { logger } from '../utils/logger';

/**
 * Drug Mapper
 * Converts raw openFDA API responses to clean, structured domain entities
 * 
 * CRITICAL RULES:
 * - NO hallucination: Only map data that exists in the FDA response
 * - NO interpretation: Keep FDA text as-is
 * - NO medical advice: Just structure the data
 */
export class DrugMapper {
    /**
     * Maps openFDA drug label result to DrugEntity
     * Safely extracts and cleans FDA data
     */
    static toDrugEntity(fdaResult: OpenFDADrugLabelResult): DrugEntity {
        try {
            // Extract generic name (primary identifier)
            const genericName = this.extractFirstValue(fdaResult.openfda?.generic_name) || 'Unknown';

            // Extract brand names
            const brandNames = fdaResult.openfda?.brand_name || [];

            // Map the drug entity with available data
            const drugEntity: DrugEntity = {
                genericName: genericName.toLowerCase(),
                brandNames: brandNames.map((name) => this.cleanText(name)),
                purpose: this.extractFirstValue(fdaResult.purpose),
                activeIngredients: this.cleanArray(fdaResult.active_ingredient),
                warnings: this.cleanArray(fdaResult.warnings),
                adverseReactions: this.cleanArray(fdaResult.adverse_reactions),
                drugInteractions: this.cleanArray(fdaResult.drug_interactions),
                dosageInfo: this.cleanArray(fdaResult.dosage_and_administration),
                contraindications: this.cleanArray(fdaResult.contraindications),
                pharmacology: this.cleanArray(fdaResult.clinical_pharmacology),
            };

            logger.info(`Mapped drug entity: ${genericName}`);
            return drugEntity;
        } catch (error) {
            logger.error('Error mapping FDA result to DrugEntity', error);
            throw new Error('Failed to map FDA data');
        }
    }

    /**
     * Maps multiple FDA results to an array of DrugEntities
     */
    static toDrugEntities(fdaResults: OpenFDADrugLabelResult[]): DrugEntity[] {
        return fdaResults.map((result) => this.toDrugEntity(result));
    }

    /**
     * Creates a summary of drug information suitable for Gemini synthesis
     * This is what gets sent back to Gemini as function result
     * 
     * IMPORTANT: Keep summaries CONCISE to minimize token usage
     * - Limit text fields to essential information only
     * - Truncate long sections
     */
    static toSummary(entity: DrugEntity): string {
        const sections: string[] = [];

        sections.push(`**Drug Name:** ${entity.genericName}`);

        if (entity.brandNames.length > 0) {
            sections.push(`**Brand Names:** ${entity.brandNames.slice(0, 3).join(', ')}`);
        }

        if (entity.purpose) {
            sections.push(`**Purpose:** ${this.truncate(entity.purpose, 200)}`);
        }

        if (entity.activeIngredients && entity.activeIngredients.length > 0) {
            sections.push(`**Active Ingredients:**\n${this.formatList(entity.activeIngredients.slice(0, 3))}`);
        }

        if (entity.warnings && entity.warnings.length > 0) {
            // Only include first warning, truncated
            sections.push(`**Warnings:**\n${this.truncate(entity.warnings[0], 300)}`);
        }

        if (entity.adverseReactions && entity.adverseReactions.length > 0) {
            // Only include first adverse reaction section, truncated
            sections.push(`**Side Effects/Adverse Reactions:**\n${this.truncate(entity.adverseReactions[0], 400)}`);
        }

        if (entity.drugInteractions && entity.drugInteractions.length > 0) {
            // Only include first interaction section, truncated
            sections.push(`**Drug Interactions:**\n${this.truncate(entity.drugInteractions[0], 300)}`);
        }

        if (entity.contraindications && entity.contraindications.length > 0) {
            // Only include first contraindication section, truncated
            sections.push(`**Contraindications (When NOT to use):**\n${this.truncate(entity.contraindications[0], 200)}`);
        }

        if (entity.dosageInfo && entity.dosageInfo.length > 0) {
            // Only include first dosage section, truncated
            sections.push(`**General Dosage Information:**\n${this.truncate(entity.dosageInfo[0], 300)}`);
        }

        return sections.join('\n\n');
    }

    /**
     * Helper: Extract first value from array or return undefined
     */
    private static extractFirstValue(arr?: string[]): string | undefined {
        if (!arr || arr.length === 0) return undefined;
        return this.cleanText(arr[0]);
    }

    /**
     * Helper: Clean and filter array of strings
     */
    private static cleanArray(arr?: string[]): string[] | undefined {
        if (!arr || arr.length === 0) return undefined;
        return arr.map((item) => this.cleanText(item)).filter((item) => item.length > 0);
    }

    /**
     * Helper: Clean text by removing extra whitespace and newlines
     */
    private static cleanText(text: string): string {
        return text
            .replace(/\s+/g, ' ') // Replace multiple spaces with single space
            .replace(/\n+/g, ' ') // Replace newlines with space
            .trim();
    }

    /**
     * Helper: Truncate text to a maximum character length
     * Adds "..." if truncated
     */
    private static truncate(text: string, maxLength: number): string {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength).trim() + '...';
    }

    /**
     * Helper: Format array as numbered list
     */
    private static formatList(items: string[]): string {
        return items.map((item, index) => `${index + 1}. ${item}`).join('\n');
    }
}
