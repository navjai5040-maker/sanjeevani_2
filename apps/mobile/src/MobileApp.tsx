import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import type { Appointment, CareMatch, CareRequest, FollowUp, Patient, Referral, ReferralEvent, TriageResult } from '@sanjeevani/shared-types';
import { api } from './api/client';

type Role = 'patient' | 'frontline';
type Screen = 'login' | 'dashboard' | 'frontline' | 'patients' | 'patient-overview' | 'request' | 'triage' | 'matches' | 'facility' | 'appointment' | 'referral' | 'follow-up';

const lifecycle = ['created', 'destination_identified', 'accepted', 'scheduled', 'arrived', 'care_completed', 'closed', 'follow_up'];
const demoPatients: Patient[] = [
  { id: 'pat-ravi', name: 'Ravi Meena', age: 42, village: 'Ghatol', riskLevel: 'medium' },
  { id: 'pat-sita', name: 'Sita Devi', age: 29, village: 'Banswara', riskLevel: 'high' },
  { id: 'pat-aman', name: 'Aman Khan', age: 8, village: 'Ghatol', riskLevel: 'low' },
  { id: 'pat-meera', name: 'Meera Sharma', age: 34, village: 'Dungarpur', riskLevel: 'high' }
];
const demoFollowUps: FollowUp[] = [
  { followUpId: 'fu-ravi-demo', patientId: 'pat-ravi', dueDate: '2026-09-16', reason: 'Blood-pressure follow-up', priority: 'high', status: 'due', nextAction: 'Check blood-pressure follow-up' },
  { followUpId: 'fu-sita-demo', patientId: 'pat-sita', dueDate: '2026-09-14', reason: 'Maternal follow-up', priority: 'high', status: 'overdue', nextAction: 'Contact patient and reschedule maternal review' },
  { followUpId: 'fu-aman-demo', patientId: 'pat-aman', dueDate: '2026-09-22', reason: 'Child-health review', priority: 'medium', status: 'upcoming', nextAction: 'Confirm child-health review' }
];

export default function MobileApp() {
  const [screen, setScreen] = useState<Screen>('login');
  const [role, setRole] = useState<Role>('patient');
  const [language, setLanguage] = useState<'en' | 'hi'>('en');
  const [offline, setOffline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [request, setRequest] = useState<CareRequest>();
  const [triage, setTriage] = useState<TriageResult>();
  const [matches, setMatches] = useState<CareMatch[]>([]);
  const [selected, setSelected] = useState<CareMatch>();
  const [appointment, setAppointment] = useState<Appointment>();
  const [referral, setReferral] = useState<Referral>();
  const [events, setEvents] = useState<ReferralEvent[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient>(demoPatients[0]);
  const [patients, setPatients] = useState<Patient[]>(demoPatients);
  const [followUps, setFollowUps] = useState(demoFollowUps);
  const [coordination, setCoordination] = useState<{
    careRequests: CareRequest[];
    referrals: Referral[];
    appointments: Appointment[];
    followUps: FollowUp[];
  }>({ careRequests: [], referrals: [], appointments: [], followUps: demoFollowUps });

  useEffect(() => {
    if (role !== 'frontline' || api.mode !== 'REAL') return;
    void run(async () => {
      const [patients, backendFollowUps] = await Promise.all([api.patients(), api.followUps()]);
      if (patients.length) {
        setPatients(patients);
        setSelectedPatient((current) => patients.find((item) => item.id === current.id) ?? patients[0]);
      }
      setFollowUps(backendFollowUps);
    });
  }, [role]);

  useEffect(() => {
    if (api.mode !== 'REAL' || role !== 'frontline') return;
    void run(async () => {
      const value = await api.patientCoordination(selectedPatient.id);
      setCoordination(value);
      setFollowUps(value.followUps);
      if (value.referrals[0]) {
        setReferral(value.referrals[0]);
        setEvents(await api.referralEvents(value.referrals[0].referralId));
      }
      if (value.appointments[0]) setAppointment(value.appointments[0]);
      if (value.careRequests[0]) setRequest(value.careRequests[0]);
    });
  }, [selectedPatient.id, role]);

  const run = async (action: () => Promise<void>) => {
    setLoading(true); setError('');
    try { await action(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Something went wrong'); } finally { setLoading(false); }
  };

  const startRequest = (input: Omit<CareRequest, 'requestId' | 'status'>) => run(async () => {
    const created = await api.createCareRequest(input);
    const result = await api.triage(created);
    const available = await api.matches(created);
    setRequest(created); setTriage(result); setMatches(available); setScreen('triage');
  });

  const selectFacility = (facility: CareMatch) => { setSelected(facility); setScreen('facility'); };
  const createReferral = () => run(async () => {
    if (!selected || !request) return;
    const created = await api.createReferral(request.patientId, selected.facilityName ?? selected.facilityId);
    setReferral(created); setEvents(await api.referralEvents(created.referralId)); setScreen('referral');
  });

  if (loading) return <Centered><ActivityIndicator size="large" color="#0f766e" /><Text style={styles.muted}>Connecting care services...</Text></Centered>;
  if (screen === 'login') return <Login language={language} onLanguageChange={setLanguage} onLogin={(selectedRole) => { setRole(selectedRole); setScreen(selectedRole === 'frontline' ? 'frontline' : 'dashboard'); }} />;
  if (screen === 'dashboard') return <Shell title="Namaste, Meera" error={error} onBack={() => setScreen('login')}><Dashboard onStart={() => { setError(''); setScreen('request'); }} appointment={appointment} referral={referral} /></Shell>;
  if (screen === 'frontline') return <Shell title={language === 'hi' ? 'फ्रंटलाइन डैशबोर्ड' : 'Frontline dashboard'} error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen('login')}><FrontlineDashboard language={language} patients={patients} onPatients={() => setScreen('patients')} onFollowUps={() => setScreen('follow-up')} onRequest={() => setScreen('patients')} referral={referral} followUps={followUps} /></Shell>;
  if (screen === 'patients') return <Shell title="Select patient" error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen('frontline')}><PatientSearch patients={patients} onSelect={(patient) => { setSelectedPatient(patient); setScreen('patient-overview'); }} /></Shell>;
  if (screen === 'patient-overview') return <Shell title="Patient overview" error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen('patients')}><PatientOverview patient={selectedPatient} coordination={coordination} followUp={followUps.find((item) => item.patientId === selectedPatient.id)} onRequest={() => setScreen('request')} /></Shell>;
  if (screen === 'follow-up') return <Shell title="Follow-up queue" error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen('frontline')}><FollowUpView patients={patients} followUps={followUps} onComplete={(patientId) => run(async () => {
    const item = followUps.find((followUp) => followUp.patientId === patientId && followUp.status !== 'completed');
    if (item && api.mode === 'REAL') {
      const completed = await api.completeFollowUp(item.followUpId);
      setFollowUps((items) => items.map((followUp) => followUp.followUpId === completed.followUpId ? completed : followUp));
    } else {
      setFollowUps((items) => items.map((followUp) => followUp.patientId === patientId ? { ...followUp, status: 'completed' } : followUp));
    }
  })} /></Shell>;
  if (screen === 'request') return <Shell title={role === 'frontline' ? 'Create care request' : 'Find care'} error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen(role === 'frontline' ? 'patient-overview' : 'dashboard')}><CareRequestForm patientId={role === 'frontline' ? selectedPatient.id : 'pat-ravi'} frontline={role === 'frontline'} onSubmit={startRequest} /></Shell>;
  if (screen === 'triage' && triage) return <Shell title="Care guidance" error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen('request')}><TriageView triage={triage} onContinue={() => setScreen('matches')} /></Shell>;
  if (screen === 'matches') return <Shell title="Care options" error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen('triage')}><Matches matches={matches} onSelect={selectFacility} /></Shell>;
  if (screen === 'facility' && selected) return <Shell title="Facility details" error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen('matches')}><FacilityDetails facility={selected} onAppointment={() => setScreen('appointment')} onReferral={createReferral} /></Shell>;
  if (screen === 'appointment' && selected && request) return <Shell title="Book appointment" error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen('facility')}><AppointmentView facility={selected} request={request} onBooked={(value) => { setAppointment(value); setScreen(role === 'frontline' ? 'patient-overview' : 'dashboard'); }} onError={setError} /></Shell>;
  if (screen === 'referral' && referral) return <Shell title="Referral status" error={error} offline={offline} onOfflineToggle={() => setOffline((value) => !value)} onBack={() => setScreen(role === 'frontline' ? 'patient-overview' : 'dashboard')}><ReferralTimeline referral={referral} events={events} /></Shell>;
  return null;
}

function Login({ language, onLanguageChange, onLogin }: { language: 'en' | 'hi'; onLanguageChange: (value: 'en' | 'hi') => void; onLogin: (role: Role) => void }) {
  return <Centered><Text style={styles.brand}>SANJEEVANI</Text><Text style={styles.title}>{language === 'hi' ? 'स्वास्थ्य सेवा, आपके पास।' : 'Healthcare, closer to home.'}</Text><Text style={styles.muted}>{language === 'hi' ? 'डेमो लॉगिन — पहचान सत्यापन नहीं।' : 'Demo login — identity verification is not enabled.'}</Text><View style={styles.row}><Button label="English" secondary={language !== 'en'} onPress={() => onLanguageChange('en')} /><Button label="हिन्दी" secondary={language !== 'hi'} onPress={() => onLanguageChange('hi')} /></View><TextInput style={styles.input} placeholder="Mobile number" keyboardType="phone-pad" /><TextInput style={styles.input} placeholder={language === 'hi' ? 'डेमो आईडी' : 'Demo ID'} /><Button label={language === 'hi' ? 'रोगी के रूप में जारी रखें' : 'Continue as patient'} onPress={() => onLogin('patient')} /><Button label={language === 'hi' ? 'आशा/एएनएम के रूप में जारी रखें' : 'Continue as ASHA / ANM'} secondary onPress={() => onLogin('frontline')} /></Centered>;
}

function Dashboard({ onStart, appointment, referral }: { onStart: () => void; appointment?: Appointment; referral?: Referral }) {
  return <View><Text style={styles.eyebrow}>PATIENT DASHBOARD</Text><Text style={styles.title}>What do you need help with today?</Text><Button label="Find care" onPress={onStart} /><View style={styles.card}><Text style={styles.cardTitle}>Your care continuity</Text><Text style={styles.muted}>{appointment ? `Appointment booked for ${new Date(appointment.startsAt).toLocaleDateString()}` : referral ? `Referral at ${referral.destination}` : 'No active appointment or referral'}</Text></View><View style={styles.card}><Text style={styles.cardTitle}>Simple, supported access</Text><Text style={styles.muted}>Sanjeevani helps you find a suitable public facility. It does not replace a clinician.</Text></View></View>;
}

function FrontlineDashboard({ language, patients, onPatients, onFollowUps, onRequest, referral, followUps }: { language: 'en' | 'hi'; patients: Patient[]; onPatients: () => void; onFollowUps: () => void; onRequest: () => void; referral?: Referral; followUps: FollowUp[] }) {
  const due = followUps.filter((item) => item.status === 'due' || item.status === 'missed').length;
  return <View><Text style={styles.eyebrow}>{language === 'hi' ? 'आज' : 'TODAY'}</Text><Text style={styles.title}>{language === 'hi' ? 'मरीजों की देखभाल में सहायता करें' : 'Help patients reach the right care'}</Text><View style={styles.statsRow}><View style={styles.stat}><Text style={styles.statValue}>{patients.length}</Text><Text style={styles.muted}>Patients</Text></View><View style={styles.stat}><Text style={styles.statValue}>{referral ? 1 : 0}</Text><Text style={styles.muted}>Active referrals</Text></View><View style={styles.stat}><Text style={styles.statValue}>{due}</Text><Text style={styles.muted}>Due follow-ups</Text></View></View><Button label={language === 'hi' ? 'मरीज चुनें' : 'Find / select patient'} onPress={onPatients} /><Button label={language === 'hi' ? 'फॉलो-अप सूची' : 'Follow-up queue'} secondary onPress={onFollowUps} /><View style={styles.card}><Text style={styles.cardTitle}>Field-ready demo mode</Text><Text style={styles.muted}>Patient and facility information is shared through the SANJEEVANI registry in REAL mode.</Text></View></View>;
}

function PatientSearch({ patients, onSelect }: { patients: Patient[]; onSelect: (patient: Patient) => void }) {
  const [query, setQuery] = useState('');
  const visible = patients.filter((patient) => patient.name.toLowerCase().includes(query.toLowerCase()));
  return <View><Text style={styles.muted}>Search by patient name. Keep the conversation simple and focused.</Text><TextInput style={styles.input} placeholder="Search patient" value={query} onChangeText={setQuery} />{visible.map((patient) => <Pressable style={styles.card} key={patient.id} onPress={() => onSelect(patient)}><View style={styles.row}><Text style={styles.cardTitle}>{patient.name}</Text><Text style={styles.score}>{patient.riskLevel} risk</Text></View><Text style={styles.muted}>{patient.age} years · {patient.village}</Text></Pressable>)}{visible.length === 0 && <Text style={styles.muted}>No demo patient matched that name.</Text>}</View>;
}

function PatientOverview({ patient, coordination, followUp, onRequest }: { patient: Patient; coordination: { careRequests: CareRequest[]; referrals: Referral[]; appointments: Appointment[]; followUps: FollowUp[] }; followUp?: FollowUp; onRequest: () => void }) {
  const request = coordination.careRequests[coordination.careRequests.length - 1];
  const referral = coordination.referrals[0];
  const appointment = coordination.appointments[0];
  return <View><Text style={styles.eyebrow}>PATIENT CONTINUITY</Text><Text style={styles.title}>{patient.name}</Text><View style={styles.card}><Text style={styles.cardTitle}>Basic details</Text><Text style={styles.muted}>{patient.age} years · {patient.village} · {patient.riskLevel} risk</Text></View><View style={styles.card}><Text style={styles.cardTitle}>Current care stage</Text><Text style={styles.muted}>{request ? `${request.status}: ${request.symptoms}` : 'No active care request'}</Text><Text style={styles.muted}>Referral: {referral ? `${referral.destination} · ${referral.state}` : 'Not recorded'}</Text><Text style={styles.muted}>Appointment: {appointment ? `${appointment.service} · ${appointment.status}` : 'Not booked'}</Text></View><View style={styles.card}><Text style={styles.cardTitle}>Next follow-up</Text><Text style={styles.muted}>{followUp ? `${followUp.status}: ${followUp.nextAction}` : 'No follow-up recorded'}</Text></View><Button label="Create care request" onPress={onRequest} /></View>;
}

function FollowUpView({ patients, followUps, onComplete }: { patients: Patient[]; followUps: FollowUp[]; onComplete: (patientId: string) => void }) {
  return <View><Text style={styles.muted}>Prioritize who needs attention and the next action expected.</Text>{followUps.map((followUp) => { const patient = patients.find((item) => item.id === followUp.patientId); return <View style={styles.card} key={followUp.followUpId}><View style={styles.row}><Text style={styles.cardTitle}>{patient?.name ?? followUp.patientId}</Text><Text style={styles.score}>{followUp.status}</Text></View><Text style={styles.muted}>Due {followUp.dueDate}</Text><Text style={styles.muted}>{followUp.reason} · {followUp.nextAction}</Text>{followUp.status !== 'completed' && <Button label="Mark completed" secondary onPress={() => onComplete(followUp.patientId)} />}</View>; })}</View>;
}

function CareRequestForm({ patientId, frontline = false, onSubmit }: { patientId: string; frontline?: boolean; onSubmit: (input: Omit<CareRequest, 'requestId' | 'status'>) => void }) {
  const [symptoms, setSymptoms] = useState('chest pain'); const [duration, setDuration] = useState('2 hours'); const [location, setLocation] = useState('Ghatol'); const [indicator, setIndicator] = useState('chest pain');
  return <View>{frontline && <View style={styles.info}><Text style={styles.infoText}>Request created by frontline worker</Text></View>}<Text style={styles.muted}>Tell us about the concern. This is decision support, not a diagnosis.</Text><Text style={styles.label}>Symptoms or care need</Text><TextInput style={styles.input} value={symptoms} onChangeText={setSymptoms} multiline /><Text style={styles.label}>How long?</Text><TextInput style={styles.input} value={duration} onChangeText={setDuration} /><Text style={styles.label}>Location</Text><TextInput style={styles.input} value={location} onChangeText={setLocation} /><Text style={styles.label}>Urgency indicator (optional)</Text><TextInput style={styles.input} value={indicator} onChangeText={setIndicator} /><Button label="Get care guidance" onPress={() => onSubmit({ patientId, requesterId: frontline ? 'asha-demo' : patientId, symptoms, duration, urgencyIndicators: indicator ? [indicator] : [], location, preferredLanguage: 'en' })} /></View>;
}

function TriageView({ triage, onContinue }: { triage: TriageResult; onContinue: () => void }) {
  const emergency = triage.level === 'emergency';
  return <View><View style={[styles.alert, emergency && styles.danger]}><Text style={styles.alertTitle}>{triage.level.toUpperCase()}</Text><Text>{emergency ? 'Please contact emergency services immediately.' : 'This is care guidance, not a diagnosis.'}</Text></View><Text style={styles.cardTitle}>Why this guidance?</Text>{triage.rationale.map((item) => <Text style={styles.bullet} key={item}>• {item}</Text>)}{!emergency && <Button label="See suitable facilities" onPress={onContinue} />}</View>;
}

function Matches({ matches, onSelect }: { matches: CareMatch[]; onSelect: (match: CareMatch) => void }) {
  return <View>{matches.length === 0 && <Text style={styles.muted}>No suitable facility was found for this request. Try a different care concern or location.</Text>}{matches.map((match) => <Pressable style={styles.card} key={match.facilityId} onPress={() => onSelect(match)}><View style={styles.row}><Text style={styles.cardTitle}>{match.facilityName ?? match.facilityId}</Text><Text style={styles.score}>{Math.round(match.matchScore)}%</Text></View><Text style={styles.muted}>Queue {match.queueMinutes} min · Travel {match.travelMinutes} min · Readiness {match.readiness}%</Text><Text style={styles.link}>Why this facility?</Text></Pressable>)}</View>;
}

function FacilityDetails({ facility, onAppointment, onReferral }: { facility: CareMatch; onAppointment: () => void; onReferral: () => void }) {
  const lines = [...(facility.explanation ?? facility.reason), `Specialists: ${(facility.specialists ?? []).join(', ') || 'Not listed'}`, `Diagnostics: ${(facility.diagnostics ?? []).join(', ') || 'Not listed'}`, `Medicines/services: ${(facility.medicines ?? []).join(', ') || 'Not listed'}`];
  return <View><Text style={styles.title}>{facility.facilityName}</Text><Text style={styles.muted}>Queue {facility.queueMinutes} minutes · Travel {facility.travelMinutes} minutes</Text><Text style={styles.sectionTitle}>Why this facility?</Text>{lines.map((line) => <Text style={styles.bullet} key={line}>• {line}</Text>)}<Button label="Book appointment" onPress={onAppointment} /><Button label="Create referral" secondary onPress={onReferral} /></View>;
}

function AppointmentView({ facility, request, onBooked, onError }: { facility: CareMatch; request: CareRequest; onBooked: (appointment: Appointment) => void; onError: (message: string) => void }) {
  const [slots, setSlots] = useState<Awaited<ReturnType<typeof api.slots>>>([]);
  const [selected, setSelected] = useState<string>();
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    setLoading(true);
    api.slots(facility.facilityId, request.symptoms)
      .then((value) => { if (active) setSlots(value); })
      .catch((cause) => { if (active) onError(cause instanceof Error ? cause.message : 'Unable to load appointment slots'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [facility.facilityId, request.symptoms, onError]);
  const selectedSlot = slots.find((item) => item.slotId === selected);
  const book = () => {
    if (!selectedSlot) { onError('Select an available appointment slot first'); return; }
    api.bookAppointment({ patientId: request.patientId, facilityId: selectedSlot.facilityId, providerId: selectedSlot.providerId, service: selectedSlot.service, startsAt: selectedSlot.startsAt })
      .then(onBooked)
      .catch((cause) => onError(cause instanceof Error ? cause.message : 'Unable to book appointment'));
  };
  return <View><Text style={styles.muted}>Choose an available time at {facility.facilityName}.</Text>{loading && <Text style={styles.muted}>Loading available slots...</Text>}{!loading && slots.length === 0 && <Text style={styles.muted}>No appointment slots are currently available.</Text>}{slots.map((slot) => <Pressable key={slot.slotId} style={[styles.slot, selected === slot.slotId && styles.slotSelected]} onPress={() => { onError(''); setSelected(slot.slotId); }}><Text>{new Date(slot.startsAt).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</Text><Text style={styles.muted}>Wait ~{slot.estimatedWaitMinutes} min</Text></Pressable>)}<Button label="Confirm appointment" onPress={book} /></View>;
}

function ReferralTimeline({ referral, events }: { referral: Referral; events: ReferralEvent[] }) {
  const current = lifecycle.indexOf(referral.state);
  return <View><Text style={styles.title}>{referral.destination}</Text><Text style={styles.muted}>Referral {referral.referralId}</Text>{lifecycle.map((state, index) => <View style={styles.timelineRow} key={state}><View style={[styles.dot, index <= current && styles.dotActive]} /><View><Text style={styles.cardTitle}>{state.replace('_', ' ')}</Text>{events.find((event) => event.state === state) && <Text style={styles.muted}>{events.find((event) => event.state === state)?.description}</Text>}</View></View>)}</View>;
}

function Shell({ title, error, offline, onOfflineToggle, onBack, children }: { title: string; error?: string; offline?: boolean; onOfflineToggle?: () => void; onBack: () => void; children: React.ReactNode }) {
  return <SafeAreaView style={styles.safe}><View style={styles.header}><Pressable onPress={onBack}><Text style={styles.back}>‹</Text></Pressable><Text style={styles.headerTitle}>{title}</Text><Text style={styles.mode}>{api.mode}</Text></View>{onOfflineToggle && <Pressable style={styles.network} onPress={onOfflineToggle}><Text style={styles.networkText}>{offline ? 'OFFLINE · cached demo data' : 'ONLINE · tap to simulate offline'}</Text></Pressable>}<ScrollView contentContainerStyle={styles.content}>{error && <View style={styles.error}><Text style={styles.errorText}>{error}</Text></View>}{children}</ScrollView></SafeAreaView>;
}
function Centered({ children }: { children: React.ReactNode }) { return <SafeAreaView style={styles.safe}><View style={styles.centered}>{children}</View></SafeAreaView>; }
function Button({ label, onPress, secondary = false }: { label: string; onPress: () => void; secondary?: boolean }) { return <Pressable style={[styles.button, secondary && styles.buttonSecondary]} onPress={onPress}><Text style={[styles.buttonText, secondary && styles.buttonTextSecondary]}>{label}</Text></Pressable>; }

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#f3faf8' }, content: { padding: 22, gap: 16 }, centered: { flex: 1, padding: 28, justifyContent: 'center', gap: 14 }, brand: { color: '#0f766e', fontWeight: '800', letterSpacing: 2 }, title: { fontSize: 28, fontWeight: '800', color: '#12312f', marginBottom: 12 }, header: { height: 64, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: 1, borderBottomColor: '#d8eee9' }, back: { fontSize: 36, color: '#0f766e' }, headerTitle: { flex: 1, fontSize: 18, fontWeight: '700', color: '#12312f' }, mode: { fontSize: 10, color: '#0f766e', fontWeight: '800' }, network: { backgroundColor: '#e5f5f1', paddingVertical: 6, alignItems: 'center' }, networkText: { color: '#0f766e', fontSize: 11, fontWeight: '800' }, eyebrow: { color: '#0f766e', letterSpacing: 1.5, fontSize: 12, fontWeight: '800' }, muted: { color: '#56706d', lineHeight: 21 }, error: { backgroundColor: '#fee2e2', borderRadius: 12, padding: 12 }, errorText: { color: '#991b1b', fontWeight: '700' }, info: { backgroundColor: '#e5f5f1', borderRadius: 12, padding: 12 }, infoText: { color: '#0f766e', fontWeight: '800' }, input: { backgroundColor: '#fff', borderColor: '#cce5df', borderWidth: 1, borderRadius: 12, padding: 14, fontSize: 16 }, label: { color: '#254541', fontWeight: '700', marginTop: 6 }, button: { backgroundColor: '#0f766e', padding: 15, alignItems: 'center', borderRadius: 12, marginTop: 10 }, buttonSecondary: { backgroundColor: '#e5f5f1' }, buttonText: { color: '#fff', fontWeight: '800' }, buttonTextSecondary: { color: '#0f766e' }, card: { backgroundColor: '#fff', padding: 17, borderRadius: 16, borderWidth: 1, borderColor: '#dceeea', gap: 8 }, cardTitle: { color: '#163d39', fontSize: 16, fontWeight: '800', textTransform: 'capitalize' }, row: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 }, statsRow: { flexDirection: 'row', gap: 8 }, stat: { flex: 1, backgroundColor: '#fff', padding: 12, borderRadius: 12, borderWidth: 1, borderColor: '#dceeea' }, statValue: { color: '#0f766e', fontSize: 24, fontWeight: '900' }, score: { color: '#0f766e', fontWeight: '800' }, link: { color: '#0f766e', fontWeight: '800', marginTop: 5 }, sectionTitle: { color: '#163d39', fontWeight: '800', fontSize: 18, marginTop: 12 }, bullet: { color: '#375c57', lineHeight: 24 }, alert: { backgroundColor: '#fff4ce', borderRadius: 16, padding: 18, gap: 6 }, danger: { backgroundColor: '#fee2e2' }, alertTitle: { color: '#a16207', fontSize: 20, fontWeight: '900' }, slot: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#dceeea', padding: 16, borderRadius: 12, flexDirection: 'row', justifyContent: 'space-between' }, slotSelected: { borderColor: '#0f766e', backgroundColor: '#e5f5f1' }, timelineRow: { flexDirection: 'row', gap: 14, paddingVertical: 10, alignItems: 'flex-start' }, dot: { width: 14, height: 14, borderRadius: 7, backgroundColor: '#cbded9', marginTop: 3 }, dotActive: { backgroundColor: '#0f766e' }
});
