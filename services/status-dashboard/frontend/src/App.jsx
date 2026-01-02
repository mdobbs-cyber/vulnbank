import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [containers, setContainers] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [splunkComplete, setSplunkComplete] = useState(false)

  // Game Time State
  const [gameStartTime, setGameStartTime] = useState(null)
  const [timeElapsed, setTimeElapsed] = useState("00:00:00")

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status')
      const data = await res.json()

      // Update state based on new response structure
      setContainers(data.containers || [])
      if (data.game_start_time) {
        setGameStartTime(data.game_start_time)
      }

      setLastUpdated(new Date().toLocaleTimeString())

      // Check if splunk forwarder is done
      const forwarder = (data.containers || []).find(c => c.name.includes('splunk-forwarder'))
      if (forwarder && forwarder.provisioning_complete) {
        setSplunkComplete(true)
      } else {
        setSplunkComplete(false)
      }
    } catch (err) {
      console.error("Failed to fetch status", err)
    } finally {
      setLoading(false)
    }
  }

  // Ticking Clock Effect
  useEffect(() => {
    if (!gameStartTime) return

    const tick = () => {
      const start = new Date(gameStartTime).getTime()
      const now = new Date().getTime()
      const diff = now - start

      if (diff < 0) {
        setTimeElapsed("00:00:00")
        return
      }

      const hours = Math.floor(diff / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      const seconds = Math.floor((diff % (1000 * 60)) / 1000)

      const pad = (n) => n.toString().padStart(2, '0')
      setTimeElapsed(`${pad(hours)}:${pad(minutes)}:${pad(seconds)}`)
    }

    tick() // Initial call
    const timer = setInterval(tick, 1000)
    return () => clearInterval(timer)
  }, [gameStartTime])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (state, health) => {
    if (state !== 'running') return 'red'
    if (health === 'unhealthy') return 'red'
    if (health === 'starting') return 'orange'
    return 'green'
  }

  return (
    <div className="container" style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
      <header style={{
        marginBottom: '2rem',
        borderBottom: '1px solid #eee',
        paddingBottom: '1rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{ margin: 0 }}>White Team Status Dashboard</h1>
          <div style={{ marginTop: '0.5rem', color: '#666' }}>
            Last Updated: {lastUpdated}
          </div>
        </div>

        <div style={{
          textAlign: 'right',
          backgroundColor: '#333',
          color: '#0f0',
          padding: '0.5rem 1rem',
          borderRadius: '4px',
          fontFamily: 'monospace',
          fontSize: '1.5rem',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}>
          <div>GAME TIME</div>
          <div>{timeElapsed}</div>
        </div>
      </header>

      {/* Splunk Provisioning Banner */}
      <div style={{
        padding: '1rem',
        marginBottom: '2rem',
        borderRadius: '8px',
        backgroundColor: splunkComplete ? '#d4edda' : '#fff3cd',
        border: `1px solid ${splunkComplete ? '#c3e6cb' : '#ffeeba'}`,
        color: splunkComplete ? '#155724' : '#856404'
      }}>
        <h2 style={{ marginTop: 0 }}>
          Environment Status: {splunkComplete ? 'READY' : 'PROVISIONING'}
        </h2>
        <p style={{ margin: 0 }}>
          {splunkComplete
            ? "All services are up and Splunk Forwarder configuration is complete."
            : "Splunk Forwarder is still applying Ansible configurations..."}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
        {containers.map(c => {
          const color = getStatusColor(c.state, c.health)
          return (
            <div key={c.name} style={{
              border: '1px solid #ddd',
              borderRadius: '8px',
              padding: '1rem',
              borderLeft: `5px solid ${color}`
            }}>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.2rem' }}>{c.name}</h3>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                  backgroundColor: '#f8f9fa',
                  fontSize: '0.9rem',
                  fontWeight: 'bold'
                }}>
                  {c.status}
                </span>
                {c.health && (
                  <span style={{ fontSize: '0.8rem', color: '#666' }}>
                    Health: {c.health}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default App
