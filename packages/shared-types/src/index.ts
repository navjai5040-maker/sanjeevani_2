export type UserRole =
  | 'patient'
  | 'asha'
  | 'anm'
  | 'provider'
  | 'administrator';

export type TriageLevel = 'ROUTINE' | 'URGENT' | 'EMERGENCY';
export type TriageOutcome = 'routine' | 'urgent' | 'emergency';

export type ReferralState =
  | 'created'
  | 'destination_identified'
  | 'accepted'
  | 'scheduled'
  | 'arrived'
  | 'care_completed'
  | 'closed'
  | 'follow_up';

export interface User {
  id: string;
  name: string;
  role: UserRole;
  language: 'en' | 'hi';
}

export interface Patient {
  id: string;
  name: string;
  age: number;
  sex?: string;
  village: string;
  preferredLanguage?: 'en' | 'hi';
  demoContact?: string;
  riskLevel: 'low' | 'medium' | 'high';
}

export interface Facility {
  id: string;
  name: string;
  district: string;
  type: 'PHC' | 'CHC' | 'Rural Hospital' | 'District Hospital';
  readiness: number;
}

export interface CareRequirement {
  patientId: string;
  requiredService: string;
  urgency: TriageLevel;
  notes?: string;
}

export interface CareRequest {
  requestId: string;
  patientId: string;
  requesterId: string;
  symptoms: string;
  duration: string;
  urgencyIndicators: string[];
  location: string;
  preferredLanguage: 'en' | 'hi';
  status: 'open' | 'triaged' | 'matched' | 'scheduled' | 'referred' | 'closed';
}

export interface TriageResult {
  requestId: string;
  level: TriageOutcome;
  rationale: string[];
  requiresEmergencyEscalation: boolean;
}

export interface FacilityState {
  facilityId: string;
  queueMinutes: number;
  specialistAvailability: string[];
  diagnostics: string[];
  medicines: string[];
  operationalStatus: 'open' | 'limited' | 'closed';
  travelMinutes: number;
}

export interface CareMatch {
  facilityId: string;
  facilityName?: string;
  matchScore: number;
  matchedServices?: string[];
  specialists?: string[];
  diagnostics?: string[];
  medicines?: string[];
  suitabilityIndicators?: string[];
  explanation?: string[];
  reason: string[];
  queueMinutes: number;
  travelMinutes: number;
  readiness: number;
}

export interface AppointmentSlot {
  slotId: string;
  facilityId: string;
  providerId: string;
  service: string;
  startsAt: string;
  estimatedWaitMinutes: number;
  status: 'available' | 'booked' | 'cancelled' | 'completed';
}

export interface Appointment {
  appointmentId: string;
  patientId: string;
  facilityId: string;
  providerId: string;
  service: string;
  startsAt: string;
  estimatedWaitMinutes: number;
  status: 'available' | 'booked' | 'cancelled' | 'completed';
}

export interface ReferralEvent {
  referralId: string;
  state: ReferralState;
  timestamp: string;
  description: string;
}

export interface Referral {
  referralId: string;
  patientId: string;
  destination: string;
  state: ReferralState;
  createdAt: string;
}

export interface FollowUp {
  followUpId: string;
  patientId: string;
  referralId?: string;
  dueDate: string;
  reason: string;
  priority: 'low' | 'medium' | 'high';
  status: 'upcoming' | 'pending' | 'due' | 'overdue' | 'completed' | 'missed';
  nextAction: string;
  completedAt?: string;
}

export interface NotificationPayload {
  userId: string;
  type: 'appointment' | 'referral' | 'emergency' | 'follow-up' | 'system';
  title: string;
  message: string;
  read: boolean;
}

import { z } from 'zod';

export const userSchema = z.object({
  id: z.string(),
  name: z.string().min(1),
  role: z.enum(['patient', 'asha', 'anm', 'provider', 'administrator']),
  language: z.enum(['en', 'hi'])
});

export const careRequirementSchema = z.object({
  patientId: z.string(),
  requiredService: z.string().min(1),
  urgency: z.enum(['ROUTINE', 'URGENT', 'EMERGENCY']),
  notes: z.string().optional()
});

export const careRequestSchema = z.object({
  requestId: z.string().optional(),
  patientId: z.string().min(1),
  requesterId: z.string().min(1),
  symptoms: z.string().min(2),
  duration: z.string().min(1),
  urgencyIndicators: z.array(z.string()),
  location: z.string().min(2),
  preferredLanguage: z.enum(['en', 'hi']),
  status: z.enum(['open', 'triaged', 'matched', 'scheduled', 'referred', 'closed'])
});

export const referralEventSchema = z.object({
  referralId: z.string(),
  state: z.enum(['created', 'destination_identified', 'accepted', 'scheduled', 'arrived', 'care_completed', 'closed', 'follow_up']),
  timestamp: z.string().datetime(),
  description: z.string().min(1)
});
