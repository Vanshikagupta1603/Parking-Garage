import { useState } from 'react'
import { api, genIdempotencyKey } from '../api'

const GARAGE_ID = 1

export default function CheckInForm({ onCheckedIn }) {
  const [plate, setPlate] = useState('')
  const [vehicleType, setVehicleType] = useState('STANDARD')
  const [status, setStatus] = useState(null) // { type: 'success'|'error', message }
  const [submitting, setSubmitting] = useState(false)
  const [idempotencyKey, setIdempotencyKey] = useState(genIdempotencyKey())

  async function handleSubmit(e) {
    e.preventDefault()
    if (!plate.trim()) {
      setStatus({ type: 'error', message: 'Enter a plate number first.' })
      return
    }
    setSubmitting(true)
    setStatus(null)
    try {
      const ticket = await api.checkIn(plate.trim(), vehicleType, GARAGE_ID, idempotencyKey)
      setStatus({
        type: 'success',
        message: `Checked in. Ticket #${ticket.id}, spot #${ticket.spot_id}.`,
      })
      setPlate('')
      setIdempotencyKey(genIdempotencyKey()) // fresh key for the next request
      onCheckedIn?.(ticket)
    } catch (err) {
      setStatus({ type: 'error', message: err.message })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Check in</h2>
      <label>
        Plate number
        <input
          value={plate}
          onChange={(e) => setPlate(e.target.value.toUpperCase())}
          placeholder="RJ14AB1234"
        />
      </label>
      <label>
        Vehicle type
        <select value={vehicleType} onChange={(e) => setVehicleType(e.target.value)}>
          <option value="COMPACT">Compact</option>
          <option value="STANDARD">Standard</option>
          <option value="EV">EV (needs charger)</option>
        </select>
      </label>
      <button type="submit" disabled={submitting}>
        {submitting ? 'Checking in…' : 'Check in'}
      </button>
      {status && <p className={`status ${status.type}`}>{status.message}</p>}
    </form>
  )
}
