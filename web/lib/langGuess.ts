// Devanagari present -> speak with the Hindi voice, else English.
// Sanskrit is never spoken aloud (product rule), so this only ever
// selects between the two configured Kokoro voices.

const DEVANAGARI = /[ऀ-ॿ]/;

export function langGuess(text: string): "en" | "hi" {
  return DEVANAGARI.test(text) ? "hi" : "en";
}
