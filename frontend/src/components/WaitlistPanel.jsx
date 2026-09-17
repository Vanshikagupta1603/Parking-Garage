import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

const GARAGE_ID = 1

export default function WaitlistPanel() {
  const [plate, setPlate] = useState('')
  const [vehicleType, setVehicleType] = useState('EV')
  const [status, setStatus] = useState(null)
  const [alert, setAlert] = useState(null) // set when THIS plate is notified
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(api.wsUrl())
    wsRef.current = ws
    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data)
      if (data.event === 'waitlist_spot_ready') {
        setAlert(data) // shown to whoever is watching this console right now
      }
    }
    return () => ws.close()
  }, [])

  async function handleJoin(e) {
    e.preventDefault()
    if (!plate.trim()) {
      setStatus({ type: 'error', message: 'Enter a plate number first.' })
      return
    }
    try {
      await api.joinWaitlist(plate.trim(), vehicleType, GARAGE_ID)
      setStatus({ type: 'success', message: `${plate.trim()} added to the ${vehicleType} waitlist.` })
      setPlate('')
    } catch (err) {
      setStatus({ type: 'error', message: err.message })
    }
  }

  return (
    <div className="card">
      <h2>Notify me when a spot frees up</h2>
      <p className="hint">
        For drivers waiting when a spot type is full. First in line gets the
        next matching spot automatically, the instant it's checked out.
      </p>
      <form onSubmit={handleJoin}>
        <label>
          Plate number
          <input
            value={plate}
            onChange={(e) => setPlate(e.target.value.toUpperCase())}
            placeholder="RJ14AB1234"
          />
        </label>
        <label>
          Waiting for
          <select value={vehicleType} onChange={(e) => setVehicleType(e.target.value)}>
            <option value="COMPACT">Compact</option>
            <option value="STANDARD">Standard</option>
            <option value="EV">EV</option>
          </select>
        </label>
        <button type="submit">Join waitlist</button>
      </form>
      {status && <p className={`status ${status.type}`}>{status.message}</p>}

      {alert && (
        <div className="waitlist-alert">
          A {alert.spot_type} spot just opened up for <strong>{alert.plate}</strong>.
        </div>
      )}
    </div>
  )
}
