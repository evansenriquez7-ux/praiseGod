/** Component emission checks on real interactive student-path payloads. */
import fs from 'node:fs';
import { afterAll, afterEach, describe, expect, test } from 'vitest';
import { cleanup, fireEvent, render, waitFor } from '@testing-library/react';

import { renderVisualInner } from './utils/renderUtils.jsx';

const corpusPath = process.env.PGEN_STATIC_RENDER_CORPUS;
const resultPath = process.env.PGEN_ANSWER_ROUNDTRIP_RESULT;
if (!corpusPath || !resultPath) throw new Error('frontend_suite.py must supply round-trip paths');

const corpus = JSON.parse(fs.readFileSync(corpusPath, 'utf8'));
const cases = corpus.cases.filter(
  (sample) => sample.interaction_mode === 'set' || sample.answer_collection !== 'mcq',
);
const emissions = [];

function fakeCanvasContext() {
  return new Proxy({}, {
    get: (_target, key) => key === 'measureText' ? (() => ({ width: 10 })) : (() => {}),
  });
}
HTMLCanvasElement.prototype.getContext = fakeCanvasContext;

afterEach(() => cleanup());
afterAll(() => fs.writeFileSync(resultPath, JSON.stringify({ emissions }, null, 2) + '\n'));

async function driveCorrect(sample, root) {
  const correct = sample.correct_answer;
  if (sample.visual_type === 'GridArea') {
    const cells = root.querySelectorAll('[data-pgen-role="grid-cell"]');
    for (let i = 0; i < Number(correct); i += 1) fireEvent.click(cells[i]);
  } else if (sample.visual_type === 'BarChart') {
    const plus = [...root.querySelectorAll('button')].filter((b) => b.textContent.trim() === '+');
    const values = Array.isArray(correct[0]) ? correct.flat() : correct;
    const scale = sample.visual_params.scale || 1;
    values.forEach((value, idx) => {
      for (let n = 0; n < value / scale; n += 1) fireEvent.click(plus[idx]);
    });
  } else if (sample.visual_type === 'ClockSet') {
    const [hours, minutes] = String(correct).split(':').map(Number);
    const hourDelta = ((hours - 12) % 12 + 12) % 12;
    for (let i = 0; i < hourDelta; i += 1) {
      fireEvent.click(root.querySelector('[title="Increase hours"]'));
    }
    for (let i = 0; i < minutes; i += 1) {
      fireEvent.click(root.querySelector('[title="Increase 1 minute"]'));
    }
  } else if (sample.visual_type === 'FillInTable') {
    const inputs = root.querySelectorAll('input');
    correct.forEach((value, idx) => {
      fireEvent.change(inputs[idx], { target: { value: String(value) } });
    });
  } else if (sample.visual_type === 'FractionShade') {
    const numerator = Number(String(correct).split('/')[0]);
    fireEvent.click(root.querySelectorAll('[data-pgen-role="fraction-part"]')[numerator - 1]);
  } else if (sample.visual_type === 'NumberLine') {
    const line = root.querySelector('.number-line-container');
    fireEvent.keyDown(line, { key: 'Home' });
    const steps = Math.round(
      (Number(correct) - sample.visual_params.start) /
      (sample.visual_params.minor_interval || sample.visual_params.interval || 1),
    );
    for (let i = 0; i < steps; i += 1) fireEvent.keyDown(line, { key: 'ArrowRight' });
  } else if (sample.visual_type === 'PesoMoney') {
    const target = Number(sample.visual_params.target_amount);
    const controls = [...root.querySelectorAll('button')]
      .map((button) => ({ button, value: Number(button.textContent.trim().replace('₱', '')) }))
      .filter((entry) => Number.isFinite(entry.value) && entry.value > 0)
      .sort((a, b) => b.value - a.value);
    let remaining = target;
    for (const { button, value } of controls) {
      while (remaining >= value) {
        fireEvent.click(button);
        remaining -= value;
      }
    }
    if (remaining !== 0) throw new Error(`controls cannot compose target ${target}`);
  } else if (sample.visual_type === 'PlaceValueBlocks') {
    const targets = [
      ['1000s', sample.visual_params.thousands || 0],
      ['100s', sample.visual_params.hundreds || 0],
      ['10s', sample.visual_params.tens || 0],
      ['1s', sample.visual_params.ones || 0],
    ];
    targets.forEach(([label, digit]) => {
      const heading = [...root.querySelectorAll('span')].find((span) => span.textContent === label);
      if (!heading) {
        if (digit) throw new Error(`no visible ${label} control for non-zero target ${digit}`);
        return;
      }
      const plus = [...heading.parentElement.querySelectorAll('button')].find(
        (button) => button.textContent.trim() === '+',
      );
      for (let i = 0; i < digit; i += 1) fireEvent.click(plus);
    });
  } else if (sample.visual_type === 'NumberBond') {
    fireEvent.change(root.querySelector('input'), { target: { value: String(correct) } });
  } else {
    throw new Error(`no correct-answer driver for ${sample.visual_type}`);
  }
}

describe('component onAnswer round trip', () => {
  test.each(cases)('$case_id emits a value for the keyed correct interaction', async (sample) => {
    let emitted;
    const view = render(renderVisualInner(
      sample.visual_type,
      sample.visual_params,
      (value) => { emitted = value; },
      false,
      `${sample.case_id}-roundtrip`,
    ));
    await driveCorrect(sample, view.container);
    await waitFor(() => expect(emitted).not.toBeUndefined());
    emissions.push({
      case_id: sample.case_id,
      node_id: sample.node_id,
      seed: sample.seed,
      visual_type: sample.visual_type,
      formatter: sample.formatter,
      correct_answer: sample.correct_answer,
      emitted_answer: emitted,
    });
  });
});
