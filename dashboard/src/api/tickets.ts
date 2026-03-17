import type { ApiRequestConfig } from './client'
import { api } from './client'
import type { Paginated } from './garages'

export interface TicketResponse {
  id: number
  entry_time: string | null
  exit_time: string | null
  fee: string | null
  ticket_state: string | null
  payment_status: string | null
  operational_status: string | null
  vehicle_id: number | null
  garage_id: number
  spot_id: number | null
  ticket_token: string
}

// get the tickets from the tickets dashboard endpoint
export interface TicketDashboardRow extends TicketResponse {
  licence_plate: string | null
  spot_code: string | null
  garage_name: string | null
  /** Optional image URL when provided by the backend (e.g. garage or ticket image). */
  image_url?: string | null
}

// get the tickets from the tickets endpoint
export function listTickets(
  params?: {
    state?: 'OPEN' | 'CLOSED'
    payment_status?: string
    garage_id?: number
    limit?: number
    offset?: number
  },
  config?: ApiRequestConfig
) {
  return api.get<Paginated<TicketResponse>>('/tickets', { params, ...config })
}

export function listTicketsDashboard(
  params?: {
    garage_id?: number
    limit?: number
    offset?: number
  },
  config?: ApiRequestConfig
) {
  return api.get<Paginated<TicketDashboardRow>>('/tickets/dashboard', {
    params,
    ...config,
  })
}

export function getTicket(id: number, config?: ApiRequestConfig) {
  return api.get<TicketResponse>(`/tickets/${id}`, config)
}

export function ticketExit(id: number, data?: { exit_time?: string }) { // post the data to the tickets/exit endpoint
  return api.post<TicketResponse>(`/tickets/${id}/exit`, data ?? {})
}

export function ticketEntry(data: {
  vehicle_id: number
  garage_id: number
  spot_id?: number | null
  rentable_only?: boolean
  entry_time?: string
  image_url?: string | null  // optional image URL when provided by the backend (e.g. garage or ticket image)
}) {
  return api.post<TicketResponse>('/tickets/entry', data) // post the data to the tickets/entry endpoint
}
