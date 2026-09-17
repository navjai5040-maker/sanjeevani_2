import type {
  Appointment,
  AppointmentSlot,
  CareMatch,
  CareRequest,
  FollowUp,
  Patient,
  Referral,
  ReferralEvent,
  TriageResult
} from '@sanjeevani/shared-types';

export type CareRequestInput = Omit<CareRequest, 'requestId' | 'status'>;
export type AppointmentInput = Pick<Appointment, 'patientId' | 'facilityId' | 'providerId' | 'service' | 'startsAt'>;
export type ApiMode = 'MOCK' | 'REAL';

const demoPatientsFallback: Patient[] = [
  { id: 'pat-ravi', name: 'Ravi Meena', age: 42, sex: 'male', village: 'Ghatol', preferredLanguage: 'hi', demoContact: 'demo-ravi', riskLevel: 'medium' },
  { id: 'pat-sita', name: 'Sita Devi', age: 29, sex: 'female', village: 'Banswara', preferredLanguage: 'hi', demoContact: 'demo-sita', riskLevel: 'high' },
  { id: 'pat-aman', name: 'Aman Khan', age: 8, sex: 'male', village: 'Ghatol', preferredLanguage: 'hi', demoContact: 'demo-aman', riskLevel: 'low' },
  { id: 'pat-meera', name: 'Meera Sharma', age: 34, sex: 'female', village: 'Dungarpur', preferredLanguage: 'en', demoContact: 'demo-meera', riskLevel: 'high' }
];

const mode: ApiMode = process.env.EXPO_PUBLIC_API_MODE === 'REAL' ? 'REAL' : 'MOCK';
const baseUrl = (process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

const mockMatches: CareMatch[] = [
  {
    facilityId: 'fac-udaipur-dh',
    facilityName: 'District Hospital, Udaipur',
    matchScore: 94,
    matchedServices: ['cardiology'],
    specialists: ['cardiology'],
    diagnostics: ['ECG', 'laboratory'],
    medicines: ['antihypertensives'],
    suitabilityIndicators: ['capability_match', 'specialist_available', 'diagnostic_available'],
    explanation: ['Requested service is available', 'Relevant specialist coverage is available', 'Supporting diagnostics are available'],
    reason: ['Requested service is available', 'Relevant specialist coverage is available'],
    queueMinutes: 28,
    travelMinutes: 45,
    readiness: 92
  },
  {
    facilityId: 'fac-banswara-chc',
    facilityName: 'CHC, Banswara',
    matchScore: 77,
    matchedServices: ['general medicine'],
    specialists: ['general medicine'],
    diagnostics: ['X-Ray'],
    medicines: ['basic care'],
    suitabilityIndicators: ['capability_match', 'service_available'],
    explanation: ['General medicine service is available', 'Moderate waiting time'],
    reason: ['General medicine service is available'],
    queueMinutes: 14,
    travelMinutes: 20,
    readiness: 81
  }
];

const mockReferral: Referral = {
  referralId: 'ref-demo-001',
  patientId: 'pat-ravi',
  destination: 'District Hospital, Udaipur',
  state: 'created',
  createdAt: new Date().toISOString()
};

const mockEvents: ReferralEvent[] = [{
  referralId: mockReferral.referralId,
  state: 'created',
  timestamp: mockReferral.createdAt,
  description: 'Referral created'
}];

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

function mapCareRequest(value: Record<string, unknown>): CareRequest {
  return {
    requestId: String(value.request_id ?? value.requestId ?? ''),
    patientId: String(value.patient_id ?? value.patientId ?? ''),
    requesterId: String(value.requester_id ?? value.requesterId ?? ''),
    symptoms: String(value.symptoms ?? ''),
    duration: String(value.duration ?? ''),
    urgencyIndicators: (value.urgency_indicators ?? value.urgencyIndicators ?? []) as string[],
    location: String(value.location ?? ''),
    preferredLanguage: (value.preferred_language ?? value.preferredLanguage ?? 'en') as 'en' | 'hi',
    status: (value.status ?? 'open') as CareRequest['status']
  };
}

function mapMatch(value: Record<string, unknown>): CareMatch {
  return {
    facilityId: String(value.facility_id ?? value.facilityId ?? ''),
    facilityName: String(value.facility_name ?? value.facilityName ?? ''),
    matchScore: Number(value.match_score ?? value.matchScore ?? 0),
    matchedServices: (value.matched_services ?? value.matchedServices ?? []) as string[],
    specialists: (value.specialists ?? []) as string[],
    diagnostics: (value.diagnostics ?? []) as string[],
    medicines: (value.medicines ?? []) as string[],
    suitabilityIndicators: (value.suitability_indicators ?? value.suitabilityIndicators ?? []) as string[],
    explanation: (value.explanation ?? []) as string[],
    reason: (value.reason ?? []) as string[],
    queueMinutes: Number(value.queue_minutes ?? value.queueMinutes ?? 0),
    travelMinutes: Number(value.travel_minutes ?? value.travelMinutes ?? 0),
    readiness: Number(value.readiness ?? 0)
  };
}

function mapSlot(value: Record<string, unknown>): AppointmentSlot {
  return {
    slotId: String(value.slot_id ?? value.slotId ?? ''),
    facilityId: String(value.facility_id ?? value.facilityId ?? ''),
    providerId: String(value.provider_id ?? value.providerId ?? ''),
    service: String(value.service ?? ''),
    startsAt: String(value.starts_at ?? value.startsAt ?? ''),
    estimatedWaitMinutes: Number(value.estimated_wait_minutes ?? value.estimatedWaitMinutes ?? 0),
    status: (value.status ?? 'available') as AppointmentSlot['status']
  };
}

function mapAppointment(value: Record<string, unknown>): Appointment {
  return {
    appointmentId: String(value.appointment_id ?? value.appointmentId ?? ''),
    patientId: String(value.patient_id ?? value.patientId ?? ''),
    facilityId: String(value.facility_id ?? value.facilityId ?? ''),
    providerId: String(value.provider_id ?? value.providerId ?? ''),
    service: String(value.service ?? ''),
    startsAt: String(value.starts_at ?? value.startsAt ?? ''),
    estimatedWaitMinutes: Number(value.estimated_wait_minutes ?? value.estimatedWaitMinutes ?? 0),
    status: (value.status ?? 'booked') as Appointment['status']
  };
}

function mapReferral(value: Record<string, unknown>): Referral {
  return {
    referralId: String(value.referral_id ?? value.referralId ?? ''),
    patientId: String(value.patient_id ?? value.patientId ?? ''),
    destination: String(value.destination ?? ''),
    state: (value.state ?? 'created') as Referral['state'],
    createdAt: String(value.created_at ?? value.createdAt ?? '')
  };
}

function mapReferralEvent(value: Record<string, unknown>): ReferralEvent {
  return {
    referralId: String(value.referral_id ?? value.referralId ?? ''),
    state: (value.state ?? 'created') as ReferralEvent['state'],
    timestamp: String(value.timestamp ?? ''),
    description: String(value.description ?? '')
  };
}

function mapPatient(value: Record<string, unknown>): Patient {
  return {
    id: String(value.id ?? ''),
    name: String(value.name ?? ''),
    age: Number(value.age ?? 0),
    sex: value.sex ? String(value.sex) : undefined,
    village: String(value.village ?? ''),
    preferredLanguage: (value.preferred_language ?? value.preferredLanguage ?? 'en') as 'en' | 'hi',
    demoContact: value.demo_contact ? String(value.demo_contact) : undefined,
    riskLevel: (value.risk_level ?? value.riskLevel ?? 'low') as Patient['riskLevel']
  };
}

function mapFollowUp(value: Record<string, unknown>): FollowUp {
  return {
    followUpId: String(value.follow_up_id ?? value.followUpId ?? ''),
    patientId: String(value.patient_id ?? value.patientId ?? ''),
    referralId: value.referral_id ? String(value.referral_id) : undefined,
    dueDate: String(value.due_date ?? value.dueDate ?? ''),
    reason: String(value.reason ?? 'Care follow-up'),
    priority: (value.priority ?? 'medium') as FollowUp['priority'],
    status: (value.status ?? 'upcoming') as FollowUp['status'],
    nextAction: String(value.next_action ?? value.nextAction ?? ''),
    completedAt: value.completed_at ? String(value.completed_at) : undefined
  };
}

function toApiCareRequest(value: CareRequestInput | CareRequest): Record<string, unknown> {
  return {
    ...('requestId' in value && value.requestId ? { request_id: value.requestId } : {}),
    patient_id: value.patientId,
    requester_id: value.requesterId,
    symptoms: value.symptoms,
    duration: value.duration,
    urgency_indicators: value.urgencyIndicators,
    location: value.location,
    preferred_language: value.preferredLanguage,
    ...('status' in value && value.status ? { status: value.status } : {})
  };
}

export const api = {
  mode,
  async careRequests(patientId: string): Promise<CareRequest[]> {
    if (mode === 'MOCK') return [];
    const values = await request<Record<string, unknown>[]>(`/api/v1/care-requests?patient_id=${encodeURIComponent(patientId)}`);
    return values.map(mapCareRequest);
  },
  async referrals(patientId?: string): Promise<Referral[]> {
    if (mode === 'MOCK') return mockReferral.patientId === patientId ? [mockReferral] : [];
    const values = await request<Record<string, unknown>[]>('/api/v1/referrals');
    return values.map(mapReferral).filter((value) => !patientId || value.patientId === patientId);
  },
  async appointments(patientId?: string): Promise<Appointment[]> {
    if (mode === 'MOCK') return [];
    const values = await request<Record<string, unknown>[]>('/api/v1/appointments');
    return values.map(mapAppointment).filter((value) => !patientId || value.patientId === patientId);
  },
  async patientCoordination(patientId: string) {
    const [careRequests, referrals, appointments, followUps] = await Promise.all([
      api.careRequests(patientId),
      api.referrals(patientId),
      api.appointments(patientId),
      api.followUps(patientId)
    ]);
    return { careRequests, referrals, appointments, followUps };
  },
  async patients(query?: string): Promise<Patient[]> {
    if (mode === 'MOCK') return demoPatientsFallback;
    const values = await request<Record<string, unknown>[]>(`/api/v1/patients${query ? `?query=${encodeURIComponent(query)}` : ''}`);
    return values.map(mapPatient);
  },
  async patient(patientId: string): Promise<Patient> {
    if (mode === 'MOCK') {
      const value = demoPatientsFallback.find((item) => item.id === patientId);
      if (!value) throw new Error('Patient not found');
      return value;
    }
    return mapPatient(await request<Record<string, unknown>>(`/api/v1/patients/${encodeURIComponent(patientId)}`));
  },
  async followUps(patientId?: string): Promise<FollowUp[]> {
    if (mode === 'MOCK') return [];
    const values = await request<Record<string, unknown>[]>(`/api/v1/followups${patientId ? `?patient_id=${encodeURIComponent(patientId)}` : ''}`);
    return values.map(mapFollowUp);
  },
  async completeFollowUp(followUpId: string): Promise<FollowUp> {
    if (mode === 'MOCK') throw new Error('Follow-up completion is unavailable in mock mode');
    return mapFollowUp(await request<Record<string, unknown>>(`/api/v1/followups/${encodeURIComponent(followUpId)}/complete`, { method: 'POST' }));
  },
  async createCareRequest(input: CareRequestInput): Promise<CareRequest> {
    if (mode === 'MOCK') return { ...input, requestId: 'req-demo-001', status: 'open' };
    const value = await request<Record<string, unknown>>('/api/v1/care-requests', { method: 'POST', body: JSON.stringify(toApiCareRequest(input)) });
    return mapCareRequest(value);
  },
  async triage(input: CareRequest): Promise<TriageResult> {
    if (mode === 'MOCK') {
      const emergency = input.urgencyIndicators.some((item) => ['unconscious', 'heavy bleeding'].includes(item.toLowerCase()));
      const urgent = emergency || input.urgencyIndicators.some((item) => ['chest pain', 'high fever', 'severe pain'].includes(item.toLowerCase()));
      return {
        requestId: input.requestId,
        level: emergency ? 'emergency' : urgent ? 'urgent' : 'routine',
        rationale: [emergency ? 'Emergency indicator requires immediate escalation' : urgent ? 'Urgency indicator requires prompt clinical review' : 'No configured emergency or urgent indicator was provided'],
        requiresEmergencyEscalation: emergency
      };
    }
    const value = await request<Record<string, unknown>>('/api/v1/triage', { method: 'POST', body: JSON.stringify(toApiCareRequest(input)) });
    return {
      requestId: String(value.request_id ?? value.requestId ?? ''),
      level: value.level as TriageResult['level'],
      rationale: value.rationale as string[],
      requiresEmergencyEscalation: Boolean(value.requires_emergency_escalation ?? value.requiresEmergencyEscalation)
    };
  },
  async matches(input: CareRequest): Promise<CareMatch[]> {
    if (mode === 'MOCK') return mockMatches;
    const params = new URLSearchParams({
      patient_id: input.patientId,
      requester_id: input.requesterId,
      symptoms: input.symptoms,
      duration: input.duration,
      location: input.location,
      preferred_language: input.preferredLanguage
    });
    const values = await request<Record<string, unknown>[]>(`/api/v1/facilities/matches?${params.toString()}`);
    return values.map(mapMatch);
  },
  async slots(facilityId: string, service: string): Promise<AppointmentSlot[]> {
    if (mode === 'MOCK') {
      return ['09:00', '11:00', '14:00'].map((time, index) => ({
        slotId: `slot-${index}`,
        facilityId,
        providerId: `provider-${index + 1}`,
        service,
        startsAt: `2026-09-17T${time}:00.000Z`,
        estimatedWaitMinutes: mockMatches[0].queueMinutes,
        status: 'available'
      }));
    }
    const values = await request<Record<string, unknown>[]>(`/api/v1/appointments/slots?facility_id=${encodeURIComponent(facilityId)}&service=${encodeURIComponent(service)}`);
    return values.map(mapSlot);
  },
  async bookAppointment(input: AppointmentInput): Promise<Appointment> {
    if (mode === 'MOCK') return { ...input, appointmentId: 'appt-demo-001', status: 'booked', estimatedWaitMinutes: 14 };
    const value = await request<Record<string, unknown>>('/api/v1/appointments', { method: 'POST', body: JSON.stringify({
      patient_id: input.patientId,
      facility_id: input.facilityId,
      provider_id: input.providerId,
      service: input.service,
      starts_at: input.startsAt
    }) });
    return mapAppointment(value);
  },
  async createReferral(patientId: string, destination: string): Promise<Referral> {
    if (mode === 'MOCK') return { ...mockReferral, patientId, destination };
    const value = await request<Record<string, unknown>>('/api/v1/referrals', { method: 'POST', body: JSON.stringify({ patient_id: patientId, destination }) });
    return mapReferral(value);
  },
  async referralEvents(referralId: string): Promise<ReferralEvent[]> {
    if (mode === 'MOCK') return mockEvents.map((event) => ({ ...event, referralId }));
    const values = await request<Record<string, unknown>[]>(`/api/v1/referrals/${encodeURIComponent(referralId)}/events`);
    return values.map(mapReferralEvent);
  }
};
