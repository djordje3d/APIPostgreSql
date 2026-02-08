import { api } from './client'
import type { Paginated } from './garages'

export interface Spot {
  id: number
  garage_id: number
  code: string
  is_rentable: boolean
  is_active: boolean
}

export function listSpots(params?: {
  garage_id?: number
  active_only?: boolean
  rentable_only?: boolean
  only_free?: boolean
  limit?: number
  offset?: number
}) {
  return api.get<Paginated<Spot>>('/spots', { params })
}

export function getSpot(id: number) {
  return api.get<Spot>(`/spots/${id}`)
}
