import { useEffect, useState } from 'react'
import { api } from '../api'

const PAGE_SIZE = 10

export default function TicketLog({ refreshKey }) {
  const [tickets, setTickets] = useState([])
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const data = await api.listTickets(statusFilter || undefined, page)
      setTickets(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter, refreshKey])

  return (
    <div className="card">
      <div className="dashboard-header">
        <h2>Ticket log</h2>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value)
            setPage(1)
          }}
        >
          <option value="">All</option>
          <option value="ACTIVE">Active</option>
          <option value="CLOSED">Closed</option>
        </select>
      </div>

      <table>
        <thead>
          <tr>
            <th>Ticket</th>
            <th>Plate</th>
            <th>Type</th>
            <th>Spot</th>
            <th>Entry</th>
            <th>Fee</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td>{t.plate}</td>
              <td>{t.vehicle_type}</td>
              <td>{t.spot_id}</td>
              <td>{new Date(t.entry_time).toLocaleString()}</td>
              <td>{t.fee != null ? `$${t.fee}` : '—'}</td>
              <td>{t.status}</td>
            </tr>
          ))}
          {tickets.length === 0 && !loading && (
            <tr>
              <td colSpan={7}>No tickets on this page.</td>
            </tr>
          )}
        </tbody>
      </table>

      <div className="pagination">
        <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
          Prev
        </button>
        <span>Page {page}</span>
        <button disabled={tickets.length < PAGE_SIZE} onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </div>
    </div>
  )
}
