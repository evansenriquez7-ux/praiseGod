/**
 * Convert LaTeX-encoded math to plain readable text.
 * Handles the most common patterns produced by the testy agent.
 *
 * Examples:
 *   \(\frac{3}{4}\)            → 3/4
 *   \(5 \times [3 + (8-2)]\)   → 5 × [3 + (8-2)]
 *   \(2^{-3}\)                 → 2^(-3)
 *   $\sqrt{16}$                → √16
 */
export function renderMath(text) {
  if (!text || typeof text !== 'string') return text;

  return text
    // Strip display-math delimiters \[ ... \] and \( ... \)
    .replace(/\\\[/g, '').replace(/\\\]/g, '')
    .replace(/\\\(/g, '').replace(/\\\)/g, '')
    // Strip inline $ delimiters (single and double)
    .replace(/\$\$/g, '').replace(/\$/g, '')
    // Common operators
    .replace(/\\times/g, '×')
    .replace(/\\div/g, '÷')
    .replace(/\\cdot/g, '·')
    .replace(/\\pm/g, '±')
    .replace(/\\neq/g, '≠')
    .replace(/\\leq/g, '≤')
    .replace(/\\geq/g, '≥')
    .replace(/\\approx/g, '≈')
    .replace(/\\infty/g, '∞')
    .replace(/\\pi/g, 'π')
    .replace(/\\sqrt\{([^}]+)\}/g, '√($1)')
    // Fractions: \frac{num}{den} → num/den
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '$1/$2')
    // Superscripts: ^{expr} → ^(expr)
    .replace(/\^\{([^}]+)\}/g, '^($1)')
    // Subscripts: _{expr} → _expr
    .replace(/\_\{([^}]+)\}/g, '_$1')
    // Escaped braces
    .replace(/\\\{/g, '{').replace(/\\\}/g, '}')
    // Remove remaining LaTeX commands (e.g. \text{...} → content)
    .replace(/\\text\{([^}]*)\}/g, '$1')
    .replace(/\\mathrm\{([^}]*)\}/g, '$1')
    .replace(/\\mathbf\{([^}]*)\}/g, '$1')
    .replace(/\\left/g, '').replace(/\\right/g, '')
    // Remove any remaining lone backslash-commands
    .replace(/\\[a-zA-Z]+/g, '')
    // Normalize multiple spaces
    .replace(/\s{2,}/g, ' ')
    .trim();
}
