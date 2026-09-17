const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export function genIdempotencyKey() {
  return crypto.randomUUID()
}

export const api = {
  checkIn: (plate, vehicleType, garageId, idempotencyKey) =>
    fetch(`${BASE_URL}/checkin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': idempotencyKey,
      },
      body: JSON.stringify({ plate, vehicle_type: vehicleType, garage_id: garageId }),
    }).then(handle),

  checkOut: (ticketId) =>
    fetch(`${BASE_URL}/checkout/${ticketId}`, { method: 'POST' }).then(handle),

  searchByPlate: (plate) =>
    fetch(`${BASE_URL}/tickets/search?plate=${encodeURIComponent(plate)}`).then(handle),

  availability: (garageId) =>
    fetch(`${BASE_URL}/availability?garage_id=${garageId}`).then(handle),

  listTickets: (status, page = 1) =>
    fetch(
      `${BASE_URL}/tickets?${status ? `status=${status}&` : ''}page=${page}`
    ).then(handle),

  joinWaitlist: (plate, vehicleType, garageId) =>
    fetch(`${BASE_URL}/waitlist/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plate, vehicle_type: vehicleType, garage_id: garageId }),
    }).then(handle),

  analyticsSummary: (garageId) =>
    fetch(`${BASE_URL}/analytics/summary?garage_id=${garageId}`).then(handle),

  wsUrl: () => BASE_URL.replace(/^http/, 'ws') + '/ws/occupancy',
}
