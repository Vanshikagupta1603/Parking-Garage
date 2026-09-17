import { useState } from 'react'
import CheckInForm from './components/CheckInForm.jsx'
import PlateSearch from './components/PlateSearch.jsx'
import AvailabilityDashboard from './components/AvailabilityDashboard.jsx'
import WaitlistPanel from './components/WaitlistPanel.jsx'
import AnalyticsPanel from './components/AnalyticsPanel.jsx'
import TicketLog from './components/TicketLog.jsx'

export default function App() {
  // Bumping this forces the ticket log to refetch after a check-in/out,
  // without the log needing to know about the forms directly.
  const [refreshKey, setRefreshKey] = useState(0)
  const bump = () => setRefreshKey((k) => k + 1)

  return (
    <div className="app">
      <header>
        <h1>Downtown Garage — Attendant Console</h1>
      </header>

      <div className="grid">
        <CheckInForm onCheckedIn={bump} />
        <PlateSearch onCheckedOut={bump} />
        <AvailabilityDashboard />
      </div>

      <div className="grid">
        <WaitlistPanel />
        <AnalyticsPanel refreshKey={refreshKey} />
      </div>

      <TicketLog refreshKey={refreshKey} />
    </div>
  )
}
