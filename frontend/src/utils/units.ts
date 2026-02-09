/**
 * Unit conversion utilities.
 * Backend always stores weight in kg.
 * Frontend converts for display based on user preference.
 */

const KG_TO_LB = 2.20462;
const LB_TO_KG = 1 / KG_TO_LB;

/**
 * Convert kg to lb.
 */
export const kgToLb = (kg: number): number => {
  return Math.round(kg * KG_TO_LB * 100) / 100; // Round to 2 decimal places
};

/**
 * Convert lb to kg.
 */
export const lbToKg = (lb: number): number => {
  return Math.round(lb * LB_TO_KG * 100) / 100; // Round to 2 decimal places
};

/**
 * Convert weight for display based on user's preferred unit.
 * @param weightKg Weight in kg (from backend)
 * @param userUnit User's preferred unit ("kg" or "lb")
 * @returns Weight in user's preferred unit
 */
export const convertWeightForDisplay = (weightKg: number | null | undefined, userUnit: 'kg' | 'lb'): number | null => {
  if (weightKg === null || weightKg === undefined) return null;
  if (userUnit === 'lb') {
    return kgToLb(weightKg);
  }
  return weightKg;
};

/**
 * Convert weight from user input to kg (for backend).
 * @param weight Weight entered by user
 * @param userUnit User's preferred unit ("kg" or "lb")
 * @returns Weight in kg
 */
export const convertWeightToKg = (weight: number, userUnit: 'kg' | 'lb'): number => {
  if (userUnit === 'lb') {
    return lbToKg(weight);
  }
  return weight;
};

/**
 * Get unit label for display.
 */
export const getUnitLabel = (userUnit: 'kg' | 'lb'): string => {
  return userUnit === 'lb' ? 'lbs' : 'kg';
};
