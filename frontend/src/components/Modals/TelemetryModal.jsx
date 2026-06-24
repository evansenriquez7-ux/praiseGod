import React from 'react';
import { Shield, User, RefreshCw, Zap, AlertTriangle } from 'lucide-react';

export default function TelemetryModal({ showTelemetryModal, setShowTelemetryModal }) {
  if (!showTelemetryModal) return null;
  return (
    <>
<div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(5, 8, 22, 0.85)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            animation: 'fade-in 0.3s ease-out'
          }}
          onClick={() => setShowTelemetryModal(false)}
        >
          <div 
            className="glass-card animate-scale-up" 
            style={{
              maxWidth: '550px',
              width: '90%',
              padding: '40px',
              position: 'relative',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
              border: '1px solid rgba(16, 185, 129, 0.25)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button 
              onClick={() => setShowTelemetryModal(false)}
              style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                background: 'none',
                border: 'none',
                color: 'hsl(var(--text-muted))',
                fontSize: '24px',
                cursor: 'pointer',
                transition: 'var(--transition-smooth)'
              }}
              onMouseEnter={(e) => e.target.style.color = '#f8fafc'}
              onMouseLeave={(e) => e.target.style.color = 'hsl(var(--text-muted))'}
            >
              &times;
            </button>

            {/* Modal Header */}
            <div style={{ textAlign: 'center', marginBottom: '30px' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 15px', boxShadow: '0 8px 24px rgba(16, 185, 129, 0.3)' }}>
                <Shield className="w-8 h-8 text-white" />
              </div>
              <h3 style={{ fontSize: '24px', fontWeight: 800, color: '#f8fafc' }}>Active Telemetry Shield</h3>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '13px', marginTop: '6px' }}>
                CCMed integrates advanced real-time psychometric pacing controls to guarantee an authentic, distraction-free environment.
              </p>
            </div>

            {/* Rules list */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '30px' }}>
              
              {/* Rule 1: Tab Focus */}
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <User className="w-5 h-5 text-emerald-400" style={{ color: '#34d399' }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>Anti-Distraction Focus Guard</h4>
                  <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                    Pauses academic timers and increments a "tab-out" counter if a student switches tabs or minimizes the CCMed window.
                  </p>
                </div>
              </div>

              {/* Rule 2: Idle Pacing */}
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <RefreshCw className="w-5 h-5 text-amber-400" style={{ color: '#fbbf24' }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>120-Second Idle Pacing Sensor</h4>
                  <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                    Pauses progress and increments the student's background idle duration if no keyboard or mouse actions are recorded for 2 minutes.
                  </p>
                </div>
              </div>

              {/* Rule 3: Guessing Prevention */}
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Zap className="w-5 h-5 text-blue-400" style={{ color: '#60a5fa' }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>Rapid-Guess Defense Filter</h4>
                  <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                    Flags submissions made under 3s (Math) or 1.5s (ELA) as potential guesses. Guessed answers won't increment streaks or advance mastery.
                  </p>
                </div>
              </div>

              {/* Rule 4: Spam Protection */}
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <AlertTriangle className="w-5 h-5 text-red-400" style={{ color: '#f87171' }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>Multi-Click Spam Lockout</h4>
                  <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                    Temporarily blocks choices and displays a calming caution alert if the student performs 4 or more rapid clicks within 1.5 seconds.
                  </p>
                </div>
              </div>

            </div>

            {/* Close Button */}
            <button className="btn-primary" onClick={() => setShowTelemetryModal(false)} style={{ width: '100%', padding: '14px', background: '#10b981', borderColor: '#10b981' }}>
              <span>Acknowledge & Close</span>
            </button>
          </div>
        </div>
    </>
  );
}
