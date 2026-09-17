import { useState } from 'react'
import { api } from '../api'

export default function PlateSearch({ onCheckedOut }) {
  const [plate, setPlate] = useState('')
  const [ticket, setTicket] = useState(null)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSearch(e) {
    e.preventDefault()
    if (!plate.trim()) {
      setStatus({ type: 'error', message: 'Enter a plate number first.' })
      return
    }
    setLoading(true)
    setStatus(null)
    setTicket(null)
    try {
      const found = await api.searchByPlate(plate.trim())
      setTicket(found)
    } catch (err) {
      setStatus({ type: 'error', message: 'No active ticket found for that plate.' })
    } finally {
      setLoading(false)
    }
  }

  async function handleCheckOut() {
    if (!ticket) return
    setLoading(true)
    try {
      const closed = await api.checkOut(ticket.id)
      setStatus({
        type: 'success',
        message: `Checked out. Fee: $${closed.fee}. Spot #${closed.spot_id} is now free.`,
      })
      setTicket(null)
      setPlate('')
      onCheckedOut?.(closed)
    } catch (err) {
      setStatus({ type: 'error', message: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Find a car / check out</h2>
      <form onSubmit={handleSearch}>
        <label>
          Plate number
          <input
            value={plate}
            onChange={(e) => setPlate(e.target.value.toUpperCase())}
            placeholder="RJ14AB1234"
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {ticket && (
        <div className="ticket-preview">
          <p>
            Ticket #{ticket.id} — spot #{ticket.spot_id} — entered{' '}
            {new Date(ticket.entry_time).toLocaleString()}
          </p>
          <button onClick={handleCheckOut} disabled={loading} className="secondary">
            Check out & compute fee
          </button>
        </div>
      )}

      {status && <p className={`status ${status.type}`}>{status.message}</p>}
    </div>
  )
}
