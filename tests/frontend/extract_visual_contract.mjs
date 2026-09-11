/**
 * extract_visual_contract.mjs — derive the frontend visual contract from the SOURCE.
 *
 * Emits, as JSON on stdout:
 *   { "<visual_type>": { "component": "<Name>",
 *                        "required": [...], "optional": [...] }, ... }
 *
 * WHY THIS EXISTS, and why it parses rather than greps.
 *
 * `tests/frontend_contract_auditor.py` used to carry a hand-written REQUIRED_KEYS map,
 * described in its own comment as "derived from VisualSkeletons.jsx and
 * renderUtils.jsx". It was derived from them ONCE, by a person reading them. Measured
 * 2026-09-11 it had drifted in BOTH directions: 35 keys the components read only via
 * `const {...} = params` destructuring appeared in no list at all (hours, minutes, rows,
 * columns, whole, part1, part2, categories, counts ...), while `dot_value` was required
 * of NumberLine although the component reads it as
 * `params?.dot_value ?? params?.value ?? params?.correct_position` and needs none of
 * the three. A gate that models what it audits stops auditing the moment the real thing
 * moves, and says nothing.
 *
 * A regex would be the same mistake one level down: it sees `params.x` and misses
 * `const {x} = params`, which is how 35 keys went unseen. So this walks the real Babel
 * AST and understands every access form the language has:
 *
 *   params.x              params?.x            params["x"]
 *   const {x} = params    const {x = 1} = params   const {x: y} = params
 *
 * REQUIRED vs OPTIONAL is read off the AST, and the distinction that matters is NOT
 * "does this read have a fallback" -- that classification is wrong and would gut the
 * gate. `params?.dot_value ?? params?.value ?? params?.correct_position` has fallbacks
 * for every arm and still needs the payload to supply ONE of them; falling through to
 * undefined is Bug #58, "dot at 0 on number line", named in the auditor's own docstring.
 * A first pass of this extractor classified all three as optional and derived
 * `NumberLine: required = []`, i.e. a contract that checks nothing for the very
 * component whose silent-default bug motivated the auditor.
 *
 * So three classes, decided by what a fallback chain ENDS in:
 *
 *   required        a bare read (`params.emoji`). Missing -> undefined -> silent wrong render.
 *   required_group  a `??`/`||` chain whose arms are ALL params reads
 *                   (`a ?? b ?? c`). The payload must supply AT LEAST ONE.
 *   optional        a chain ending in a literal or non-params default (`params.x ?? 0`),
 *                   or a destructuring default (`const {x = 1} = params`). Only here does
 *                   the component genuinely carry its own default.
 *   conditional     read only inside a branch (`if (...) { ... params.values2 ... }`,
 *                   a ternary arm, the right of `&&`). Required WHEN that branch runs and
 *                   meaningless otherwise, so failing on its absence would cry wolf:
 *                   FractionModel reads a_numerator/b_denominator only on its compare
 *                   branch, BarChart reads values2 only for a second series. Measured
 *                   2026-09-11 over 320 real payloads, 17 such keys were absent by design.
 *
 * KNOWN LIMIT, named rather than papered over (Scaling Mandate 6): `conditional` keys are
 * REPORTED, not enforced. Enforcing them means evaluating the guard against the payload,
 * which is a second model of the component and free to drift from it -- the very thing
 * this file exists to stop. What is guaranteed is that the list of conditional keys is
 * derived, so it cannot silently grow stale the way a hand-written one did.
 *
 * SCALING (Mandate 4): nothing here is per-grade or per-component. A component added
 * for grade 7 is picked up the moment renderUtils' switch names it; a key it starts
 * reading is covered the moment it is written; a key that gains a fallback stops being
 * required automatically. There is no list to keep up to date, because there is no list.
 *
 * FAILS LOUDLY, never quietly: a parse error, a missing file, an unmapped component or
 * an empty result exits non-zero. A contract extractor that returns {} on error would
 * hand the auditor "nothing to check" and the auditor would pass.
 */
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [, , skeletonsPath, renderUtilsPath] = process.argv;
if (!skeletonsPath || !renderUtilsPath) {
  console.error("usage: extract_visual_contract.mjs <VisualSkeletons.jsx> <renderUtils.jsx>");
  process.exit(2);
}

// Resolve @babel from the FRONTEND's node_modules, not this script's directory.
// `createRequire(import.meta.url)` looks beside the script (tests/frontend/), which has
// no node_modules; resolving from the JSX file walks up into frontend/ where the parser
// actually lives. @babel/parser and @babel/traverse are already present there as
// transitive dependencies of vite and eslint, so deriving the contract needs no new
// dependency and no network install.
const require = createRequire(pathToFileURL(resolve(skeletonsPath)));
let parser, traverse;
try {
  parser = require("@babel/parser");
  traverse = require("@babel/traverse");
  traverse = traverse.default || traverse;
} catch (e) {
  console.error("FATAL: cannot load @babel/parser / @babel/traverse from the frontend's "
    + "node_modules (" + e.message + "). Run `npm install` in frontend/. Deriving the "
    + "visual contract from a regex instead is what this file exists to stop.");
  process.exit(6);
}

function parse(file) {
  const code = readFileSync(file, "utf8");
  return parser.parse(code, {
    sourceType: "module",
    plugins: ["jsx", "typescript", "classProperties", "optionalChaining", "nullishCoalescingOperator"],
  });
}

const PARAMS_READ = /^params\??\./;

/** The source text of a node, for recognising `params.x` arms of a fallback chain. */
function isParamsRead(node, code) {
  if (!node) return false;
  if (node.type === "MemberExpression" || node.type === "OptionalMemberExpression") {
    const obj = node.object;
    return obj.type === "Identifier" && obj.name === "params";
  }
  return false;
}

/** Flatten `a ?? b ?? c` (left-nested) into its arms. */
function chainArms(node) {
  if (node.type !== "LogicalExpression" || (node.operator !== "??" && node.operator !== "||")) {
    return [node];
  }
  return [...chainArms(node.left), node.right];
}

/**
 * Is this reference a PRESENCE CHECK -- `x ? a : b`, `x && ...`, `x ?? d`?
 *
 * Then the component has already decided what to do when the key is absent, so the key
 * is optional. BarChart reads `targetValues2 ? 24 : 44` eight times over; an earlier
 * version of this function excluded a ternary's own test (behind a clause that read
 * `consequent === consequent`, always true) and derived `values2` as REQUIRED, which no
 * real payload supplies. Testing for a key is the opposite of requiring it.
 */
function isPresenceCheck(path) {
  const p = path.parentPath;
  if (!p) return false;
  if (p.isConditionalExpression?.() && p.node.test === path.node) return true;
  if (p.isLogicalExpression?.()) return true;
  if (p.isUnaryExpression?.() && p.node.operator === "!") return true;
  return false;
}

/** Is this read inside a branch, so it only runs sometimes? */
function isGuarded(path) {
  let p = path.parentPath;
  while (p && !p.isFunction?.()) {
    if (p.isIfStatement?.() && p.node.test !== path.node) return true;
    if (p.isSwitchCase?.()) return true;
    if (p.isConditionalExpression?.() && p.node.test !== path.node) return true;
    if (p.isLogicalExpression?.() && p.node.operator === "&&" && p.node.left !== path.node) return true;
    p = p.parentPath;
  }
  return false;
}

/**
 * The outermost `??`/`||` chain this read belongs to, or null if it stands alone.
 */
function enclosingChain(path) {
  let p = path.parentPath, last = null;
  while (p && (p.isParenthesizedExpression?.() || p.isTSNonNullExpression?.())) p = p.parentPath;
  while (p && p.isLogicalExpression?.() &&
         (p.node.operator === "??" || p.node.operator === "||")) {
    last = p; p = p.parentPath;
    while (p && (p.isParenthesizedExpression?.() || p.isTSNonNullExpression?.())) p = p.parentPath;
  }
  return last;
}

/** Walk one component function body, collecting the params keys it reads. */
function keyOf(node) {
  const prop = node.property;
  if (!node.computed && prop.type === "Identifier") return prop.name;
  if (node.computed && prop.type === "StringLiteral") return prop.value;
  console.error(`FATAL: a computed params[...] access this extractor cannot resolve, at `
    + `line ${node.loc?.start?.line}. Reading a params key by a runtime expression makes `
    + `the contract underivable; name the key literally.`);
  process.exit(3);
}

function keysFor(fnPath) {
  const required = new Set();
  const optional = new Set();
  const conditional = new Set();
  const unused = new Set();
  const groups = [];            // arrays of names: at least one must be supplied
  const seenChains = new Set();

  const visitRead = (p) => {
    const obj = p.node.object;
    if (!(obj.type === "Identifier" && obj.name === "params")) return;
    const name = keyOf(p.node);
    if (!name) return;
    const chain = enclosingChain(p);
    if (!chain) { (isGuarded(p) ? conditional : required).add(name); return; }
    if (seenChains.has(chain.node.start)) return;      // handled via its chain
    seenChains.add(chain.node.start);
    const arms = chainArms(chain.node);
    const names = arms.filter((a) => isParamsRead(a, null)).map(keyOf).filter(Boolean);
    const endsInParams = isParamsRead(arms[arms.length - 1], null);
    if (endsInParams && names.length > 1) groups.push([...new Set(names)].sort());
    else if (endsInParams && names.length === 1) required.add(names[0]);
    else names.forEach((n) => optional.add(n));        // chain ends in a real default
  };

  fnPath.traverse({
    MemberExpression: visitRead,
    OptionalMemberExpression: visitRead,
    VariableDeclarator(p) {
      const { id, init } = p.node;
      if (!init) return;
      const fromParams =
        (init.type === "Identifier" && init.name === "params") ||
        (init.type === "LogicalExpression" && init.left.type === "Identifier" && init.left.name === "params");
      if (!fromParams || id.type !== "ObjectPattern") return;
      for (const prop of id.properties) {
        if (prop.type === "RestElement") continue;
        const key = prop.key?.type === "Identifier" ? prop.key.name
                  : prop.key?.type === "StringLiteral" ? prop.key.value : null;
        if (!key) continue;
        // `const {x = 1} = params` carries its own default -> genuinely optional
        if (prop.value?.type === "AssignmentPattern") { optional.add(key); continue; }
        // Otherwise follow the BINDING to its uses. Classifying at the destructuring
        // site alone is wrong: `const { max_coins } = params;` looks required, but the
        // component then writes `max_coins || 8` and carries its own default. Measured
        // 2026-09-11 against 320 real payloads, judging at the pattern produced 22
        // (type, key) pairs "required" that the pipeline never supplies -- 300+ false
        // findings, which is how a gate gets switched off.
        const local = prop.value?.type === "Identifier" ? prop.value.name : key;
        const binding = p.scope.getBinding(local);
        if (!binding) { required.add(key); continue; }
        // Destructured and NEVER READ. The component pulls the key out and ignores it,
        // so its absence cannot affect the render -- treating that as required is
        // backwards, and it was: `max_coins` and `show_minutes` are destructured once
        // and referenced nowhere, yet derived as required and absent from every real
        // payload. Recorded as `unused` rather than dropped, because a key a component
        // asks for and never reads is worth someone's attention.
        if (!binding.referencePaths.length) { unused.add(key); continue; }
        // A reference counts as shielded if, after walking up past any member access
        // on it, it sits in a `??`/`||` chain or inside a branch. Both steps matter:
        // NumberLine destructures `range` and then reads `range?.[0] ?? 0`, so the
        // chain is above a member access; BarChart destructures `values2` and reads it
        // only inside `targetValues2 && series_labels && (...)`, so it is guarded
        // rather than defaulted. Without walking past the member access, and without
        // the guard test, 9 keys derived as required that 320 real payloads never
        // supply -- false alarms, which is how a gate gets ignored.
        const shielded = (ref) => {
          let up = ref;
          while (up.parentPath &&
                 (up.parentPath.isMemberExpression?.() ||
                  up.parentPath.isOptionalMemberExpression?.()) &&
                 up.parentPath.node.object === up.node) {
            up = up.parentPath;
          }
          return Boolean(enclosingChain(up)) || isPresenceCheck(up) || isGuarded(up);
        };
        const allShielded = binding.referencePaths.every(shielded);
        // A key whose presence is TESTED anywhere is optional -- the component has
        // already decided what absence means. Only a key that is merely branch-guarded,
        // never tested, is conditional.
        const anyPresenceCheck = binding.referencePaths.some(isPresenceCheck);
        const anyGuarded = !anyPresenceCheck && binding.referencePaths.some(isGuarded);
        if (allShielded) (anyGuarded ? conditional : optional).add(key);
        else required.add(key);
      }
    },
  });
  // A key required anywhere outranks a softer classification elsewhere.
  for (const k of required) { optional.delete(k); conditional.delete(k); unused.delete(k); }
  const grouped = new Set(groups.flat());
  for (const k of grouped) { optional.delete(k); conditional.delete(k); unused.delete(k); }
  for (const k of conditional) unused.delete(k);
  for (const k of optional) unused.delete(k);
  return {
    required: [...required].sort(),
    required_groups: groups,
    conditional: [...conditional].sort(),
    unused: [...unused].sort(),
    optional: [...optional].filter((k) => !grouped.has(k)).sort(),
  };
}

// ── 1. component name -> keys, from VisualSkeletons ──────────────────────────
const byComponent = {};
const skelAst = parse(skeletonsPath);
traverse(skelAst, {
  "FunctionDeclaration|FunctionExpression|ArrowFunctionExpression"(p) {
    let name = p.node.id?.name;
    if (!name && p.parentPath.isVariableDeclarator()) name = p.parentPath.node.id?.name;
    if (!name) return;
    const takesParams = (p.node.params || []).some(
      (a) => a.type === "ObjectPattern" &&
             a.properties.some((q) => q.key?.name === "params"));
    if (!takesParams) return;
    byComponent[name] = keysFor(p);
  },
});

// ── 2. visual_type -> component, from renderUtils' switch ────────────────────
const mapping = {};
const utilAst = parse(renderUtilsPath);
traverse(utilAst, {
  SwitchCase(p) {
    const test = p.node.test;
    if (!test || test.type !== "StringLiteral") return;
    let component = null;
    p.traverse({
      JSXOpeningElement(j) {
        if (component) return;
        const n = j.node.name;
        if (n.type === "JSXIdentifier") component = n.name;
      },
    });
    if (component) mapping[test.value] = component;
  },
});

// ── 3. join, and refuse to emit a contract that audits nothing ───────────────
const out = {};
const unmapped = [];
for (const [visualType, component] of Object.entries(mapping)) {
  const keys = byComponent[component];
  if (!keys) { unmapped.push(`${visualType} -> ${component}`); continue; }
  out[visualType] = { component, ...keys };
}
if (unmapped.length) {
  console.error("FATAL: renderUtils maps these visual types to components that take no "
    + "`params` prop, so their contract cannot be derived:\n  " + unmapped.join("\n  "));
  process.exit(4);
}
if (!Object.keys(out).length) {
  console.error("FATAL: derived an EMPTY visual contract. Handing that to the auditor "
    + "would make it pass by having nothing to check.");
  process.exit(5);
}
process.stdout.write(JSON.stringify(out, null, 2));
