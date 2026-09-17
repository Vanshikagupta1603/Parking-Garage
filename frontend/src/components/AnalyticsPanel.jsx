import { useEffect, useState } from 'react'
import { api } from '../api'

const GARAGE_ID = 1
const POLL_MS = 15000

export default function AnalyticsPanel({ refreshKey }) {
  const [data, setData] = useState(null)

  async function load() {
    try {
      const summary = await api.analyticsSummary(GARAGE_ID)
      setData(summary)
    } catch {
      // non-fatal — analytics is a nice-to-have, don't disrupt the console
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, POLL_MS)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey])

  return (
    <div className="card">
      <h2>Today at a glance</h2>
      {!data && <p>Loading…</p>}
      {data && (
        <div className="analytics-grid">
          <div className="analytics-tile">
            <div className="count">${data.revenue_today.toFixed(2)}</div>
            <div className="label">Revenue today</div>
          </div>
          <div className="analytics-tile">
            <div className="count">{data.avg_dwell_minutes}m</div>
            <div className="label">Avg. stay today</div>
          </div>
          <div className="analytics-tile">
            <div className="count">
              {Object.values(data.occupancy_by_floor).reduce((a, b) => a + b, 0)}
            </div>
            <div className="label">Occupied now</div>
          </div>
        </div>
      )}
      {data && Object.keys(data.occupancy_by_floor).length > 0 && (
        <div className="floor-breakdown">
          {Object.entries(data.occupancy_by_floor)
            .sort(([a], [b]) => a - b)
            .map(([floor, count]) => (
              <div key={floor} className="floor-row">
                <span>Floor {floor}</span>
                <span>{count} occupied</span>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}
