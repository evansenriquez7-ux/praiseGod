import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { JSDOM } from 'jsdom';

import { renderVisualInner } from './utils/renderUtils.jsx';

// Every non-empty rendered text node, in document order, WITH repeats and with no cap.
// Until 2026-09-30 this kept only the first occurrence of each string and truncated at
// 80. A pictograph row whose symbols repeated an earlier row's (roses and sunflowers both
// five flowers) therefore vanished from the description every blind reviewer reads, and
// two reviewers from two model families failed mat_g1_dp_q3_3 for rows that were drawn.
// The 80 cap silently cut mat_g3_na_q2_0's 135-184 labels.
function renderedTextLabels(document) {
  const labels = [];
  const walker = document.createTreeWalker(document.body, 4);
  while (walker.nextNode()) {
    const text = walker.currentNode.nodeValue.trim();
    if (text) labels.push(text);
  }
  return labels;
}

// An independent recount (element childNodes, not a TreeWalker) of the same markup.
function markupTextMultiset(markup) {
  const { document } = new JSDOM(`<body>${markup}</body>`).window;
  const counts = new Map();
  const visit = (node) => {
    for (const child of node.childNodes) {
      if (child.nodeType === 3) {
        const text = child.nodeValue.trim();
        if (text) counts.set(text, (counts.get(text) || 0) + 1);
      } else {
        visit(child);
      }
    }
  };
  visit(document.body);
  return counts;
}

export function describeStaticMarkup(visualType, markup) {
  const dom = new JSDOM(`<body>${markup}</body>`);
  const { document } = dom.window;
  const colors = [...new Set(
    [...document.querySelectorAll('[style]')]
      .flatMap((el) => (el.getAttribute('style') || '').match(/(?:#|rgb\(|hsl\()[^;,)]+[),]?/g) || []),
  )].slice(0, 40);
  const roleCounts = {};
  for (const el of document.querySelectorAll('[data-pgen-role]')) {
    const role = el.getAttribute('data-pgen-role');
    roleCounts[role] = (roleCounts[role] || 0) + 1;
  }
  const description = {
    source: 'rendered_static_markup',
    visual_type: visualType,
    element_count: document.body.querySelectorAll('*').length,
    svg_count: document.body.querySelectorAll('svg').length,
    table_row_count: document.body.querySelectorAll('tr').length,
    table_cell_count: document.body.querySelectorAll('td,th').length,
    button_count: document.body.querySelectorAll('button').length,
    input_count: document.body.querySelectorAll('input,select,textarea').length,
    text_labels: renderedTextLabels(document),
    distinct_colours: colors,
    role_counts: roleCounts,
  };
  if (visualType === 'ShapeBoard') {
    // Read the dimensions and rotation from the DOM that React actually emitted.
    // Reading the input payload here once hid a renderer that drew every figure
    // at the same 50px size even when the payload claimed variation.
    description.rendered_shapes = [...document.querySelectorAll('[data-pgen-shape-type]')]
      .map((el) => ({
        type: el.getAttribute('data-pgen-shape-type'),
        width_px: Number.parseInt(el.style.width, 10),
        height_px: Number.parseInt(el.style.height, 10),
        orientation_deg: Number.parseInt(
          /rotate\((-?\d+)deg\)/.exec(el.style.transform)?.[1] ?? '',
          10,
        ),
      }));
  }
  dom.window.close();
  return description;
}

export function renderVisualEvidence(sample, disabled = false) {
  const markup = renderToStaticMarkup(
    <section data-pgen-visual-type={sample.visual_type}>
      {renderVisualInner(
        sample.visual_type,
        sample.visual_params,
        () => {},
        disabled,
        `${sample.case_id}-${disabled ? 'disabled' : 'active'}`,
      )}
    </section>,
  );
  return {
    disabled,
    markup,
    markup_bytes: Buffer.byteLength(markup),
    description: describeStaticMarkup(sample.visual_type, markup),
  };
}

export function assertVisualEvidence(sample, evidence) {
  const findings = [];
  if (evidence.markup.includes('Unknown visual type:')) findings.push('unknown visual type fallback');
  if (/\b(?:undefined|NaN)\b/.test(evidence.markup)) findings.push('undefined/NaN reached markup');
  if (evidence.description.element_count <= 2) findings.push('degenerate empty box');
  if (sample.visual_type === 'ShapeBoard') {
    const expected = sample.visual_params.shapes || [];
    const rendered = evidence.description.rendered_shapes || [];
    if (rendered.length !== expected.length) {
      findings.push(`ShapeBoard drew ${rendered.length} shapes; payload names ${expected.length}`);
    }
    rendered.forEach((shape, i) => {
      const source = expected[i];
      if (!source) return;
      if (shape.type !== source.type) {
        findings.push(`ShapeBoard shape ${i} rendered ${shape.type} instead of ${source.type}`);
      }
      if (!Number.isFinite(shape.width_px) || !Number.isFinite(shape.height_px)) {
        findings.push(`ShapeBoard shape ${i} has no rendered dimensions`);
      }
      if (shape.orientation_deg !== (source.orientation_deg || 0)) {
        findings.push(`ShapeBoard shape ${i} lost orientation ${source.orientation_deg}`);
      }
    });
    if (sample.node_id === 'mat_g1_mg_q1_0') {
      if (new Set(rendered.map((shape) => shape.width_px)).size !== 3) {
        findings.push('Grade 1 shape identification lost its three rendered sizes');
      }
      if (new Set(rendered.map((shape) => shape.orientation_deg)).size !== 3) {
        findings.push('Grade 1 shape identification lost its three rendered orientations');
      }
      const rectangle = rendered.find((shape) => shape.type === 'rectangle');
      if (!rectangle || rectangle.width_px === rectangle.height_px) {
        findings.push('Grade 1 rectangle was drawn as a square');
      }
    }
  }
  if (sample.visual_type === 'NumberLine' && sample.visual_params.jump_count > 0) {
    const rendered = evidence.description.role_counts['number-line-jump'] || 0;
    if (rendered !== sample.visual_params.jump_count) {
      findings.push(
        `declared ${sample.visual_params.jump_count} equal jumps but rendered ${rendered}`,
      );
    }
  }
  // The description must carry every rendered text node, repeats included: a reviewer
  // shown a de-duplicated or truncated list judges rows as missing that were drawn.
  const described = new Map();
  for (const text of evidence.description.text_labels) {
    described.set(text, (described.get(text) || 0) + 1);
  }
  for (const [text, count] of markupTextMultiset(evidence.markup)) {
    const got = described.get(text) || 0;
    if (got !== count) {
      findings.push(
        `description text_labels carry ${JSON.stringify(text)} ${got} time(s) but the markup renders it ${count} time(s)`,
      );
    }
  }
  if (sample.visual_type === 'ClockSet' && sample.visual_params.period) {
    // Decide set vs read from the payload the component itself reads
    // (ClockSetInteractive keys on params.interaction_mode / params.is_read_only).
    // Packet-render corpora carry no top-level interaction_mode, so reading
    // sample.interaction_mode misclassified every set-mode clock there as read.
    const params = sample.visual_params;
    const setMode = params.interaction_mode === 'set' && !params.is_read_only;
    if (setMode) {
      if (!evidence.disabled && !evidence.markup.includes('title="Toggle AM PM"')) {
        findings.push('ClockSet period control is absent from set-mode markup');
      }
    } else {
      const expected = sample.visual_params.period === 'p.m.' ? 'PM' : 'AM';
      if (!evidence.description.text_labels.includes(expected)) {
        findings.push(`ClockSet period ${expected} is absent from rendered labels`);
      }
    }
  }
  return findings;
}
