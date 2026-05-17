/**
 * Brand hex values that the manifest and the browser-chrome theme need as
 * literal strings (they can't read CSS tokens). Mirror these to the values
 * in ``src/app/globals.css``; if the token changes there, change it here too.
 *
 * This file is allowlisted by ``scripts/lint-design.sh``.
 */
export const BRAND = {
  /** matches --primary / --route-bus */
  themeColor: "#fbbf24",
  /** matches --background */
  backgroundColor: "#09090b",
} as const;
