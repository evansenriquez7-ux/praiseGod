import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { JSDOM } from 'jsdom';

import { renderVisualInner } from './utils/renderUtils.jsx';

function renderedTextLabels(document) {
  const labels = [];
  const seen = new Set();
  const walker = document.createTreeWalker(document.body, 4);
  while (walker.nextNode()) {
    const text = walker.currentNode.nodeValue.trim();
    if (text && !seen.has(text)) {
      seen.add(text);
      labels.push(text);
    }
  }
  return labels.slice(0, 80);
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
  if (sample.visual_type === 'NumberLine' && sample.visual_params.jump_count > 0) {
    const rendered = evidence.description.role_counts['number-line-jump'] || 0;
    if (rendered !== sample.visual_params.jump_count) {
      findings.push(
        `declared ${sample.visual_params.jump_count} equal jumps but rendered ${rendered}`,
      );
    }
  }
  return findings;
}
