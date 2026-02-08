import { api } from './client'
import type { Paginated } from './garages'

export interface Payment {
  id: number
  ticket_id: number | null
  amount: string
  method: string | null
  currency: string
  paid_at: string | null
}

export function listPayments(params?: {
  from?: string
  to?: string
  garage_id?: number
  limit?: number
  offset?: number
}) {
  return api.get<Paginated<Payment>>('/payments', { params })
}

export interface OutstandingResponse {
  total_outstanding: number
}

export function getOutstanding(garageId?: number | null) {
  return api.get<OutstandingResponse>('/payments/outstanding', {
    params: garageId != null ? { garage_id: garageId } : {},
  })
}

export function getPaymentsByTicket(ticketId: number, params?: { limit?: number; offset?: number }) {
  return api.get<Paginated<Payment>>(`/payments/by-ticket/${ticketId}`, { params })
}

export function createPayment(data: {
  ticket_id: number
  amount: string | number
  method: string
  currency?: string
  paid_at?: string
}) {
  return api.post<Payment>('/payments', {
    ...data,
    amount: String(data.amount),
    currency: data.currency ?? 'RSD',
  })
}
