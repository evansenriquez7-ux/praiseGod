import fs from 'node:fs';
import { assertVisualEvidence, renderVisualEvidence } from './staticRenderEvidence.jsx';

const [, , inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  throw new Error('usage: node --import tsx staticRenderCli.jsx <corpus.json> <result.json>');
}

const corpus = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const outcomes = [];
const findings = [];
for (const sample of corpus.cases) {
  for (const disabled of [false, true]) {
    try {
      const evidence = renderVisualEvidence(sample, disabled);
      const problems = assertVisualEvidence(sample, evidence);
      for (const problem of problems) {
        findings.push(`${sample.case_id} seed ${sample.seed} ${disabled ? 'disabled' : 'active'}: ${problem}`);
      }
      outcomes.push({
        case_id: sample.case_id,
        visual_type: sample.visual_type,
        formatter: sample.formatter,
        node_id: sample.node_id,
        seed: sample.seed,
        interaction_mode: sample.interaction_mode,
        answer_collection: sample.answer_collection,
        mode: disabled ? 'disabled' : 'active',
        markup_bytes: evidence.markup_bytes,
        description: evidence.description,
      });
    } catch (error) {
      findings.push(
        `${sample.case_id} seed ${sample.seed} ${disabled ? 'disabled' : 'active'}: ` +
        `component threw ${error?.stack || error}`,
      );
    }
  }
}

const result = {
  schema_version: 1,
  assertion: 'frontend_static_render_12',
  cases_executed: corpus.cases.length,
  renders_executed: outcomes.length,
  production_visual_types: [...new Set(outcomes.map((o) => o.visual_type))].sort(),
  outcomes,
  findings,
  limitations: [
    'jsdom has no layout engine: NumberLine and BarChart pointer-drag geometry is unproven',
    'static markup cannot prove crowding, overlap, colour contrast, or touch-target size',
  ],
};
fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n');
if (findings.length) {
  console.error(`FAIL frontend_static_render_12: ${findings.length} finding(s)`);
  for (const finding of findings.slice(0, 20)) console.error(`  - ${finding}`);
  process.exit(1);
}
console.log(
  `PASS frontend_static_render_12: ${corpus.cases.length} payloads, ` +
  `${outcomes.length} active/disabled renders, ${result.production_visual_types.length} visual types`,
);
