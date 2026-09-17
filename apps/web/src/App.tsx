import { useEffect, useMemo, useState } from 'react';

type Facility = {
  facility_id: string;
  facility_name: string;
  district: string;
  facility_type: string;
  services: string[];
  queue_minutes: number;
  specialist_availability: string[];
  diagnostics: string[];
  medicines: string[];
  operational_status: 'open' | 'limited' | 'closed';
  travel_minutes: number;
  readiness: number;
};

type Referral = {
  referral_id: string;
  patient_id: string;
  destination: string;
  state: ReferralState;
  created_at: string;
};

type ReferralEvent = {
  referral_id: string;
  state: ReferralState;
  timestamp: string;
  description: string;
};

type Appointment = {
  appointment_id: string;
  patient_id: string;
  facility_id: string;
  provider_id: string;
  service: string;
  starts_at: string;
  status: 'booked' | 'cancelled' | 'completed';
  estimated_wait_minutes: number;
};
type PatientRecord = { id: string; name: string; age: number; sex?: string; village: string; preferred_language: 'en' | 'hi'; risk_level: 'low' | 'medium' | 'high' };
type FollowUp = { follow_up_id: string; patient_id: string; referral_id?: string; due_date: string; reason: string; priority: 'low' | 'medium' | 'high'; status: string; next_action: string; completed_at?: string };

type ReferralState = 'created' | 'destination_identified' | 'accepted' | 'scheduled' | 'arrived' | 'care_completed' | 'closed' | 'follow_up';
type View = 'overview' | 'referrals' | 'appointments' | 'followups' | 'readiness';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const REFERRAL_STATES: ReferralState[] = ['created', 'destination_identified', 'accepted', 'scheduled', 'arrived', 'care_completed', 'closed', 'follow_up'];
const PATIENTS: Record<string, { name: string; age: number; village: string; need: string; urgency: string }> = {
  'pat-ravi': { name: 'Ravi Meena', age: 42, village: 'Ghatol', need: 'Cardiology review', urgency: 'Urgent' },
  'pat-sita': { name: 'Sita Devi', age: 29, village: 'Banswara', need: 'Maternal follow-up', urgency: 'Routine' },
  'pat-aman': { name: 'Aman Khan', age: 8, village: 'Ghatol', need: 'Fever assessment', urgency: 'Urgent' },
  'pat-meera': { name: 'Meera Sharma', age: 34, village: 'Dungarpur', need: 'Chronic-care review', urgency: 'Routine' },
};

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function patient(patientId: string) {
  return PATIENTS[patientId] ?? { name: patientId, age: 0, village: 'Demo record', need: 'Care coordination', urgency: 'Review' };
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

function SummaryCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return <div className="card"><span className="eyebrow">{title}</span><strong>{value}</strong><small>{detail}</small></div>;
}

function Login({ onLogin }: { onLogin: (facilityId: string) => void }) {
  const [facilityId, setFacilityId] = useState('fac-udaipur-dh');
  const facilities = [
    ['fac-udaipur-dh', 'District Hospital, Udaipur'],
    ['fac-banswara-chc', 'CHC, Banswara'],
    ['fac-ghatol-phc', 'PHC, Ghatol'],
  ];
  return <main className="login-shell">
    <section className="login-card">
      <p className="eyebrow">Sanjeevani · Demo Provider Access</p>
      <h1>Facility coordination workspace</h1>
      <p className="muted">Review referrals, readiness, appointments and follow-up continuity from one place.</p>
      <label>Demo role<select><option>Doctor / Provider</option><option>Facility Staff</option></select></label>
      <label>Facility<select value={facilityId} onChange={(event) => setFacilityId(event.target.value)}>{facilities.map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></label>
      <button className="primary full-width" onClick={() => onLogin(facilityId)}>Enter facility workspace</button>
      <p className="demo-note">Demo authentication · Simulated facility state</p>
    </section>
  </main>;
}

export default function App() {
  const [facilityId, setFacilityId] = useState<string | null>(null);
  const [facility, setFacility] = useState<Facility | null>(null);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [view, setView] = useState<View>('overview');
  const [selectedReferral, setSelectedReferral] = useState<Referral | null>(null);
  const [events, setEvents] = useState<ReferralEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadWorkspace = async (id: string) => {
    setLoading(true);
    setError('');
    try {
      const [facilityData, referralData, appointmentData, patientData, followUpData] = await Promise.all([
        request<Facility>(`/api/v1/facilities/${id}`),
        request<Referral[]>('/api/v1/referrals'),
        request<Appointment[]>(`/api/v1/appointments?facility_id=${encodeURIComponent(id)}`),
        request<PatientRecord[]>('/api/v1/patients'),
        request<FollowUp[]>('/api/v1/followups'),
      ]);
      setFacility(facilityData);
      setReferrals(referralData.filter((referral) => referral.destination === facilityData.facility_name || referral.destination === id));
      setAppointments(appointmentData);
      setPatients(patientData);
      setFollowUps(followUpData);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load facility workspace.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (facilityId) void loadWorkspace(facilityId);
  }, [facilityId]);

  const openReferral = async (referral: Referral) => {
    setSelectedReferral(referral);
    setError('');
    try {
      setEvents(await request<ReferralEvent[]>(`/api/v1/referrals/${referral.referral_id}/events`));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load referral timeline.');
    }
  };

  const transition = async () => {
    if (!selectedReferral) return;
    const nextState = REFERRAL_STATES[REFERRAL_STATES.indexOf(selectedReferral.state) + 1];
    if (!nextState) return;
    try {
      const updated = await request<Referral>(`/api/v1/referrals/${selectedReferral.referral_id}/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: nextState, description: `Facility updated referral to ${label(nextState)}` }),
      });
      setSelectedReferral(updated);
      await loadWorkspace(facilityId!);
      setEvents(await request<ReferralEvent[]>(`/api/v1/referrals/${updated.referral_id}/events`));
    } catch (transitionError) {
      setError(transitionError instanceof Error ? transitionError.message : 'Unable to update referral.');
    }
  };

  const transitionAppointment = async (appointment: Appointment, status: 'completed' | 'cancelled') => {
    try {
      await request<Appointment>(`/api/v1/appointments/${appointment.appointment_id}/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      await loadWorkspace(facilityId!);
    } catch (transitionError) {
      setError(transitionError instanceof Error ? transitionError.message : 'Unable to update appointment.');
    }
  };

  const resetDemo = async () => {
    if (!window.confirm('Reset in-memory referral and appointment demo state?')) return;
    try {
      await request<{ status: string }>('/api/v1/demo/reset', { method: 'POST' });
      setSelectedReferral(null);
      await loadWorkspace(facilityId);
    } catch (resetError) {
      setError(resetError instanceof Error ? resetError.message : 'Unable to reset demo state.');
    }
  };

  const metrics = useMemo(() => {
    const accepted = referrals.filter((referral) => REFERRAL_STATES.indexOf(referral.state) >= REFERRAL_STATES.indexOf('accepted')).length;
    const completed = referrals.filter((referral) => ['care_completed', 'closed', 'follow_up'].includes(referral.state)).length;
    const pending = referrals.filter((referral) => !['closed', 'follow_up'].includes(referral.state)).length;
    return { accepted, completed, pending };
  }, [referrals]);

  if (!facilityId) return <Login onLogin={setFacilityId} />;
  if (!facility) return <main className="loading-shell"><p>{loading ? 'Loading facility workspace…' : 'Facility unavailable.'}</p>{error && <p className="error-text">{error}</p>}</main>;

  const patientCount = new Set(referrals.map((referral) => referral.patient_id)).size;
  const patientRecord = (patientId: string) => patients.find((item) => item.id === patientId) ?? patient(patientId);
  const nextAction = selectedReferral ? REFERRAL_STATES[REFERRAL_STATES.indexOf(selectedReferral.state) + 1] : null;

  return <div className="page-shell">
    <header className="topbar">
      <div><p className="eyebrow">Sanjeevani · Facility workspace</p><h1>{facility.facility_name}</h1><p className="muted">Information → Action → Continuity</p></div>
      <div className="topbar-actions"><span className="demo-badge">Demo Data · Simulated Facility State</span><button className="secondary" onClick={() => void resetDemo()}>Reset demo</button><button className="secondary" onClick={() => { setFacilityId(null); setSelectedReferral(null); }}>Switch role</button></div>
    </header>
    {error && <div className="error-banner">{error}</div>}
    <nav className="tabs">{(['overview', 'referrals', 'appointments', 'followups', 'readiness'] as View[]).map((item) => <button key={item} className={view === item ? 'tab active' : 'tab'} onClick={() => setView(item)}>{label(item)}</button>)}</nav>

    {view === 'overview' && <Overview facility={facility} referrals={referrals} appointments={appointments} metrics={metrics} patientCount={patientCount} patientRecord={patientRecord} onView={setView} />}
    {view === 'referrals' && <ReferralQueue referrals={referrals} patientRecord={patientRecord} onOpen={openReferral} />}
    {view === 'appointments' && <Appointments appointments={appointments} patientRecord={patientRecord} onTransition={transitionAppointment} />}
    {view === 'followups' && <Followups referrals={referrals} followUps={followUps} patientRecord={patientRecord} />}
    {view === 'readiness' && <Readiness facility={facility} />}

    {selectedReferral && <div className="modal-backdrop" onClick={() => setSelectedReferral(null)}>
      <section className="modal" onClick={(event) => event.stopPropagation()}>
        <div className="panel-header"><div><p className="eyebrow">Referral detail</p><h2>{patientRecord(selectedReferral.patient_id).name}</h2></div><button className="icon-button" onClick={() => setSelectedReferral(null)}>×</button></div>
        <div className="context-grid"><div><span className="muted">Patient</span><strong>{patientRecord(selectedReferral.patient_id).name}</strong></div><div><span className="muted">Village</span><strong>{patientRecord(selectedReferral.patient_id).village}</strong></div><div><span className="muted">Appointment</span><strong>{appointments.find((item) => item.patient_id === selectedReferral.patient_id) ? label(appointments.find((item) => item.patient_id === selectedReferral.patient_id)!.status) : 'Not booked'}</strong></div><div><span className="muted">Follow-up</span><strong>{followUps.find((item) => item.patient_id === selectedReferral.patient_id)?.status ?? 'Not scheduled'}</strong></div><div><span className="muted">Origin</span><strong>Patient / ASHA demo</strong></div><div><span className="muted">Destination</span><strong>{selectedReferral.destination}</strong></div></div>
        <span className="status-pill">{label(selectedReferral.state)}</span>
        <h3>Referral timeline</h3><div className="event-list">{events.map((event) => <div className="event" key={`${event.state}-${event.timestamp}`}><span className="event-dot" /><div><strong>{label(event.state)}</strong><p>{event.description}</p><small>{new Date(event.timestamp).toLocaleString()}</small></div></div>)}</div>
        {nextAction ? <button className="primary full-width" onClick={() => void transition()}>{label(nextAction)}</button> : <p className="success-note">Referral lifecycle complete. Follow-up coordination is next.</p>}
      </section>
    </div>}
  </div>;
}

function Overview({ facility, referrals, appointments, metrics, patientCount, patientRecord, onView }: { facility: Facility; referrals: Referral[]; appointments: Appointment[]; metrics: { accepted: number; completed: number; pending: number }; patientCount: number; patientRecord: (id: string) => PatientRecord | ReturnType<typeof patient>; onView: (view: View) => void }) {
  return <><section className="summary-grid">
    <SummaryCard title="Incoming referrals" value={String(referrals.length)} detail={`${metrics.pending} need attention`} />
    <SummaryCard title="Pending acceptance" value={String(referrals.filter((referral) => referral.state === 'created' || referral.state === 'destination_identified').length)} detail="Next action: review" />
    <SummaryCard title="Today's appointments" value={String(appointments.length)} detail={`${patientCount} coordinated patients`} />
    <SummaryCard title="Patients waiting" value={String(referrals.filter((referral) => referral.state === 'arrived').length)} detail="Based on referral arrivals" />
    <SummaryCard title="Follow-ups due" value="3" detail="Demo worklist · 1 overdue" />
    <SummaryCard title="Operational readiness" value={`${facility.readiness}%`} detail={`${label(facility.operational_status)} · simulated`} />
  </section><section className="layout-grid">
    <article className="panel"><div className="panel-header"><h2>What needs attention</h2><button className="link-button" onClick={() => onView('referrals')}>View referrals</button></div>{referrals.length === 0 ? <EmptyState text="No referrals are currently routed to this facility." /> : referrals.slice(0, 4).map((referral) => <button className="list-row" key={referral.referral_id} onClick={() => onView('referrals')}><span><strong>{patientRecord(referral.patient_id).name}</strong><small>Patient ID: {referral.patient_id}</small></span><span className="status-pill">{label(referral.state)}</span></button>)}</article>
    <article className="panel"><div className="panel-header"><h2>Coordination signals</h2><span className="demo-badge">Simulated</span></div><div className="signal"><strong>{metrics.accepted}</strong><span>referrals accepted</span></div><div className="signal"><strong>{metrics.completed}</strong><span>care journeys completed</span></div><div className="signal warning"><strong>{metrics.pending}</strong><span>referrals pending action</span></div><p className="muted">The dashboard highlights where coordination may be delayed, not live hospital telemetry.</p></article>
  </section></>;
}

function ReferralQueue({ referrals, patientRecord, onOpen }: { referrals: Referral[]; patientRecord: (id: string) => PatientRecord | ReturnType<typeof patient>; onOpen: (referral: Referral) => void }) {
  return <section className="panel"><div className="panel-header"><div><p className="eyebrow">Incoming work</p><h2>Referral queue</h2></div><span className="demo-badge">Existing lifecycle</span></div>{referrals.length === 0 ? <EmptyState text="Create a referral from the patient or ASHA workflow to see it here." /> : <div className="table">{referrals.map((referral) => <button className="table-row" key={referral.referral_id} onClick={() => void onOpen(referral)}><span><strong>{patientRecord(referral.patient_id).name}</strong><small>Patient ID: {referral.patient_id}</small></span><span>Review</span><span>Patient / ASHA</span><span className="status-pill">{label(referral.state)}</span><span>Open →</span></button>)}</div>}</section>;
}

function Appointments({ appointments, patientRecord, onTransition }: { appointments: Appointment[]; patientRecord: (id: string) => PatientRecord | ReturnType<typeof patient>; onTransition: (appointment: Appointment, status: 'completed' | 'cancelled') => void }) {
  return <section className="panel"><div className="panel-header"><div><p className="eyebrow">Facility schedule</p><h2>Appointments & queue</h2></div><span className="demo-badge">Backend appointments</span></div>{appointments.length === 0 ? <EmptyState text="No appointments are booked at this facility yet." /> : <div className="table">{appointments.map((appointment) => <div className="table-row" key={appointment.appointment_id}><span><strong>{patientRecord(appointment.patient_id).name}</strong><small>{appointment.service}</small></span><span>{new Date(appointment.starts_at).toLocaleString()}</span><span>{appointment.provider_id}</span><span className="status-pill">{label(appointment.status)}</span><span>{appointment.estimated_wait_minutes} min wait</span>{appointment.status === 'booked' && <span className="action-group"><button className="small-action" onClick={() => onTransition(appointment, 'completed')}>Mark completed</button><button className="small-action danger-action" onClick={() => onTransition(appointment, 'cancelled')}>Cancel</button></span>}</div>)}</div>}</section>;
}

function Followups({ referrals, followUps, patientRecord }: { referrals: Referral[]; followUps: FollowUp[]; patientRecord: (id: string) => PatientRecord | ReturnType<typeof patient> }) {
  const items = followUps.length ? followUps : referrals.slice(0, 1).map((referral) => ({ follow_up_id: 'demo', patient_id: referral.patient_id, due_date: '', reason: 'Post-referral check', priority: 'high', status: 'overdue', next_action: 'Check care completion' }));
  return <section className="panel"><div className="panel-header"><div><p className="eyebrow">Continuity worklist</p><h2>Follow-up</h2></div><span className="demo-badge">Backend follow-up state</span></div><div className="table">{items.map((item) => <div className="table-row" key={item.follow_up_id}><span><strong>{patientRecord(item.patient_id).name}</strong><small>{item.reason}</small></span><span className={['overdue', 'missed'].includes(item.status) ? 'danger-text' : ''}>{label(item.status)}</span><span>{label(item.priority)}</span><span>{item.next_action}</span></div>)}</div></section>;
}

function Readiness({ facility }: { facility: Facility }) {
  return <section className="layout-grid"><article className="panel"><div className="panel-header"><div><p className="eyebrow">Facility state</p><h2>Care readiness</h2></div><span className="readiness">{facility.readiness}% ready</span></div><p className="muted">This simulated state is the information used by the care-readiness matching engine.</p><h3>Services</h3><div className="chip-list">{facility.services.map((service) => <span className="chip" key={service}>{service}</span>)}</div><h3>Specialists</h3><div className="chip-list">{facility.specialist_availability.length ? facility.specialist_availability.map((item) => <span className="chip" key={item}>{item} · available</span>) : <span className="muted">No specialist availability recorded</span>}</div></article><article className="panel"><h2>Diagnostics & medicines</h2><h3>Diagnostics</h3><ul className="plain-list">{facility.diagnostics.map((item) => <li key={item}><span className="ok-dot" />{item} · available</li>)}</ul><h3>Medicines / service readiness</h3><ul className="plain-list">{facility.medicines.map((item) => <li key={item}><span className="ok-dot" />{item} · demo-ready</li>)}</ul><div className="readiness-bar"><span style={{ width: `${facility.readiness}%` }} /></div><p className="muted">Queue: {facility.queue_minutes} min · Travel reference: {facility.travel_minutes} min</p></article></section>;
}

function EmptyState({ text }: { text: string }) {
  return <div className="empty-state"><strong>{text}</strong><span>Actions will appear here when coordination data is available.</span></div>;
}
