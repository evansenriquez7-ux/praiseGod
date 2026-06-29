import React from 'react';
import { 
  NumberLineInteractive, 
  ClockSetInteractive, 
  PesoMoneyPicker,
  FillInTableInteractive,
  RuleDiscoveryInteractive,
  ConstraintSatisfactionInteractive,
  BarChartInteractive,
  SortOrderInteractive,
  GridAreaInteractive,
  CategorizeInteractive,
  CalendarInteractive,
  EmojiPictorialInteractive,
  PlaceValueBlocksInteractive,
  PatternSequenceInteractive,
  FractionModelInteractive,
  FractionShadeInteractive,
  TenFrameInteractive,
  RulerMeasureInteractive,
  BalanceScaleInteractive,
  ShapeBoardInteractive,
  NumberBondInteractive
} from '../components/VisualSkeletons.jsx';

export function renderVisualInner(vt, vp, onAnswer, disabled, uniqueKey) {
  switch (vt) {
    case 'SortOrder':
      return <SortOrderInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'NumberLine':
      return <NumberLineInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'PlaceValueBlocks':
      return <PlaceValueBlocksInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'EmojiPictorial':
      return <EmojiPictorialInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'ClockSet':
      return <ClockSetInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'PesoMoney':
      return <PesoMoneyPicker key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'GridArea':
      return <GridAreaInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'Calendar':
      return <CalendarInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'Categorize':
      return <CategorizeInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'FillInTable':
      return <FillInTableInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'RuleDiscovery':
      return <RuleDiscoveryInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'BarChart':
      return <BarChartInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'PatternSequence':
      return <PatternSequenceInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'FractionModel':
      return <FractionModelInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'FractionShade':
      return <FractionShadeInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'TenFrame':
      return <TenFrameInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'RulerMeasure':
      return <RulerMeasureInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'BalanceScale':
      return <BalanceScaleInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'ShapeBoard':
      return <ShapeBoardInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'NumberBond':
      return <NumberBondInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    default:
      return <div style={{ padding: '20px', background: 'rgba(239,68,68,0.1)', borderRadius: '8px', color: '#f87171' }}>Unknown visual type: {vt}</div>;
  }
}
