/**
 * Agent System Prompt
 * Defines the agent's role, rules, and behavior
 * 
 * CRITICAL: This prompt is the first line of defense for safety
 */

export const SYSTEM_PROMPT = `You are a pharmacy information assistant. Only answer with FDA drug label data. Never provide personal medical advice, diagnosis, or dosing. Refuse questions about children, pregnancy, or organ conditions. If unsafe, reply: "I cannot provide personal medical advice. Please consult a healthcare professional." For drug info, use generic names (e.g., paracetamol → acetaminophen). Summarize key points, use bullet lists, and always end with: \n"⚠️ This is FDA label info for education only. Not medical advice. Consult your healthcare provider."`;

/**
 * Safety keywords that trigger automatic refusal
 */
export const SAFETY_KEYWORDS = {
    // Personal dosing
    dosing: [
        'how much should i take',
        'what dose',
        'dosage for me',
        'how many pills',
        'how often should i',
    ],

    // Children
    children: [
        'child',
        'baby',
        'infant',
        'toddler',
        'kid',
        'pediatric',
        'for my son',
        'for my daughter',
    ],

    // Pregnancy
    pregnancy: [
        'pregnant',
        'pregnancy',
        'breastfeeding',
        'nursing',
        'expecting',
    ],

    // Organ conditions
    conditions: [
        'liver disease',
        'kidney disease',
        'renal',
        'hepatic',
        'liver failure',
        'kidney failure',
    ],

    // Medical advice
    advice: [
        'should i take',
        'can i take',
        'is it safe for me',
        'recommend',
        'what should i do',
    ],
};

/**
 * Refusal templates for different scenarios
 */
export const REFUSAL_TEMPLATES = {
    dosing: `I cannot provide personal dosage recommendations. Medication dosing must be determined by a healthcare professional based on your individual medical history, current medications, and health conditions. Please consult your doctor or pharmacist.`,

    children: `I cannot provide medication information for children. Pediatric medication use requires professional medical guidance based on the child's age, weight, and health status. Please consult your pediatrician or pharmacist.`,

    pregnancy: `I cannot provide medication safety information for pregnancy or breastfeeding. This requires professional medical evaluation. Please consult your obstetrician, midwife, or pharmacist immediately.`,

    conditions: `I cannot advise on medication use with liver or kidney conditions. These conditions significantly affect how medications are processed and require professional medical evaluation. Please consult your doctor or specialist.`,

    advice: `I cannot provide personal medical advice or recommendations. I can only share general educational information from FDA drug labels. Please consult a healthcare professional for advice specific to your situation.`,
};
