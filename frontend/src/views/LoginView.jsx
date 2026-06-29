import React from 'react';
import { Lock, Loader2 } from 'lucide-react';

export default function LoginView({
  isLoadingProfiles,
  students,
  handleSelectStudent,
  selectedStudent,
  pinInput, setPinInput,
  pinError,
  handleStudentLogin,
  handleRegister,
  regName, setRegName,
  regPin, setRegPin,
  regAge, setRegAge,
  regGrade, setRegGrade,
  regInterests, setRegInterests
}) {
  return (
          <>
            {/* Select Profile & PIN Entry */}
            <div className="glass-card">
              <h2 style={{ fontSize: '28px', marginBottom: '15px' }}>Enter Student Portal</h2>
              
              {isLoadingProfiles ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: '10px' }}>
                  <Loader2 className="w-8 h-8 spin" style={{ animation: 'spin 2s linear infinite', color: 'hsl(var(--text-muted))' }} />
                  <span style={{ color: 'hsl(var(--text-muted))', fontSize: '14px' }}>Loading student profiles...</span>
                </div>
              ) : students.length === 0 ? (
                <p style={{ color: 'hsl(var(--text-muted))', marginBottom: '20px' }}>No student profiles created yet. Create one below!</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginBottom: '25px' }}>
                  <label style={{ fontSize: '14px', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>Select Student</label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    {students.map(std => (
                      <button 
                        key={std.id}
                        onClick={() => handleSelectStudent(std)}
                        className={`option-btn ${selectedStudent?.id === std.id ? 'selected' : ''}`}
                        style={{ padding: '12px 18px', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '4px' }}
                      >
                        <span style={{ fontWeight: 700 }}>{std.name}</span>
                        <span style={{ fontSize: '12px', color: 'hsl(var(--text-muted))' }}>Grade {std.grade} • ELO: {std.elo_rating}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {selectedStudent && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', animation: 'slide-up 0.3s ease-out' }}>
                  <label style={{ fontSize: '14px', fontWeight: 600 }}>Enter 4-6 digit numeric PIN to unlock:</label>
                  <input 
                    type="password" 
                    className="premium-input" 
                    placeholder="••••"
                    value={pinInput}
                    onChange={(e) => setPinInput(e.target.value)}
                    maxLength={6}
                    style={{ letterSpacing: '8px', textAlign: 'center', fontSize: '20px' }}
                  />
                  {pinError && <p style={{ color: '#fca5a5', fontSize: '13px' }}>{pinError}</p>}
                  <button className="btn-primary" onClick={() => handleStudentLogin(selectedStudent.id)} style={{ marginTop: '10px' }}>
                    <Lock className="w-5 h-5" />
                    <span>Unlock Portal</span>
                  </button>
                </div>
              )}

              {/* Onboarding Register profile manual */}
              <div style={{ marginTop: '40px', paddingTop: '30px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <h3 style={{ fontSize: '20px', marginBottom: '15px' }}>Create New Profile</h3>
                <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <input 
                    type="text" 
                    className="premium-input" 
                    placeholder="Student Full Name"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                  />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <input 
                      type="password" 
                      className="premium-input" 
                      placeholder="PIN (4-6 digits)"
                      value={regPin}
                      onChange={(e) => setRegPin(e.target.value)}
                      maxLength={6}
                    />
                    <input 
                      type="number" 
                      className="premium-input" 
                      placeholder="Age"
                      value={regAge}
                      onChange={(e) => setRegAge(e.target.value)}
                    />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <select 
                      className="premium-input" 
                      value={regGrade}
                      onChange={(e) => setRegGrade(e.target.value)}
                      style={{ background: 'rgba(0,0,0,0.4)', color: '#f8fafc', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px', height: '42px', padding: '0 12px', fontSize: '14px' }}
                    >
                      <option value="0" style={{ background: '#0f172a' }}>Kindergarten (Grade 0)</option>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(g => (
                        <option key={g} value={g} style={{ background: '#0f172a' }}>Grade {g}</option>
                      ))}
                    </select>
                    <input 
                      type="text" 
                      className="premium-input" 
                      placeholder="Interests (comma separated)"
                      value={regInterests}
                      onChange={(e) => setRegInterests(e.target.value)}
                    />
                  </div>
                  <button type="submit" className="btn-secondary">Create Profile</button>
                </form>
              </div>
            </div>
        </>

  );
}
