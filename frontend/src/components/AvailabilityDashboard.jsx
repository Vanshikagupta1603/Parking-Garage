import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

const GARAGE_ID = 1
const LABELS = { COMPACT: 'Compact', STANDARD: 'Standard', EV: 'EV' }

export default function AvailabilityDashboard() {
  const [counts, setCounts] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  async function refresh() {
    try {
      const res = await api.availability(GARAGE_ID)
      setCounts(res.counts)
    } catch {
      // availability polling failure is non-fatal; the WS will retry the connection
    }
  }

  useEffect(() => {
    refresh()

    const ws = new WebSocket(api.wsUrl())
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)
    // Any spot_occupied/spot_freed event means counts are stale — refetch.
    // (Keeping this simple; a busier garage could apply deltas client-side instead.)
    ws.onmessage = () => refresh()

    return () => ws.close()
  }, [])

  return (
    <div className="card">
      <div className="dashboard-header">
        <h2>Live availability</h2>
        <span className={`dot ${connected ? 'live' : 'offline'}`} title={connected ? 'Live' : 'Reconnecting…'} />
      </div>
      {!counts && <p>Loading…</p>}
      {counts && (
        <div className="availability-grid">
          {Object.entries(LABELS).map(([type, label]) => (
            <div key={type} className={`availability-tile ${counts[type] === 0 ? 'empty' : ''}`}>
              <div className="count">{counts[type] ?? '—'}</div>
              <div className="label">{label} free</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
