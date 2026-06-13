import { useRef, useCallback, useEffect, useState } from 'react';
import * as Tone from 'tone';

/**
 * Custom hook for managing sound effects in CCMed
 * Uses Tone.js for synthesized audio feedback
 * 
 * @param {boolean} enabled - Whether sound effects are enabled
 * @returns {Object} Sound playback functions
 */
export function useSoundEffects(enabled) {
  const synthRef = useRef(null);
  const polySynthRef = useRef(null);
  const membraneRef = useRef(null);
  const isInitializedRef = useRef(false);

  // Initialize audio context on first user interaction
  const initAudio = useCallback(async () => {
    if (isInitializedRef.current) return;
    
    try {
      await Tone.start();
      
      // Membrane synth for click/select sounds (soft mechanical click)
      membraneRef.current = new Tone.MembraneSynth({
        pitchDecay: 0.05,
        octaves: 2,
        oscillator: { type: 'sine' },
        envelope: {
          attack: 0.001,
          decay: 0.1,
          sustain: 0,
          release: 0.1
        }
      }).toDestination();
      membraneRef.current.volume.value = -20;

      // PolySynth for correct answer - bright bell tone
      polySynthRef.current = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'sine' },
        envelope: {
          attack: 0.005,
          decay: 0.8,
          sustain: 0.0,
          release: 1.2
        }
      }).toDestination();
      
      // Add reverb for resonant bell ring
      const reverb = new Tone.Reverb({
        decay: 2.5,
        preDelay: 0.01
      }).toDestination();
      polySynthRef.current.connect(reverb);
      polySynthRef.current.volume.value = -6;

      // Mono synth for incorrect/error sounds (soft buzz)
      synthRef.current = new Tone.Synth({
        oscillator: { type: 'sawtooth' },
        envelope: {
          attack: 0.01,
          decay: 0.2,
          sustain: 0,
          release: 0.2
        }
      }).toDestination();
      
      // Low-pass filter to soften the buzz
      const filter = new Tone.Filter(800, 'lowpass').toDestination();
      synthRef.current.connect(filter);
      synthRef.current.volume.value = -12;

      isInitializedRef.current = true;
    } catch (error) {
      console.warn('Failed to initialize audio context:', error);
    }
  }, []);

  // Play select/click sound - soft mechanical click
  const playSelect = useCallback(() => {
    if (!enabled || !isInitializedRef.current) return;
    
    try {
      membraneRef.current?.triggerAttackRelease('C2', '32n');
    } catch (error) {
      console.warn('Failed to play select sound:', error);
    }
  }, [enabled]);

  // Play correct answer sound - clear, pleasant bell
  const playCorrect = useCallback(() => {
    if (!enabled || !isInitializedRef.current) return;
    
    try {
      // Bell-like ascending arpeggio: E5 → G5 → C6 (bright, celebratory)
      const now = Tone.now();
      polySynthRef.current?.triggerAttackRelease('E5', '8n', now);
      polySynthRef.current?.triggerAttackRelease('G5', '8n', now + 0.1);
      polySynthRef.current?.triggerAttackRelease('C6', '4n', now + 0.2);
    } catch (error) {
      console.warn('Failed to play correct sound:', error);
    }
  }, [enabled]);

  // Play incorrect answer sound - soft descending buzz (non-punitive)
  const playIncorrect = useCallback(() => {
    if (!enabled || !isInitializedRef.current) return;
    
    try {
      // Descending minor third - informative but not harsh
      const now = Tone.now();
      synthRef.current?.triggerAttackRelease('A3', '16n', now);
      synthRef.current?.triggerAttackRelease('F3', '16n', now + 0.1);
    } catch (error) {
      console.warn('Failed to play incorrect sound:', error);
    }
  }, [enabled]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (membraneRef.current) {
        membraneRef.current.dispose();
        membraneRef.current = null;
      }
      if (polySynthRef.current) {
        polySynthRef.current.dispose();
        polySynthRef.current = null;
      }
      if (synthRef.current) {
        synthRef.current.dispose();
        synthRef.current = null;
      }
    };
  }, []);

  return {
    playSelect,
    playCorrect,
    playIncorrect,
    initAudio
  };
}

export default useSoundEffects;
