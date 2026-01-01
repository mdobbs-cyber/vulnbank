import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [containers, setContainers] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [splunkComplete, setSplunkComplete] = useState(false)

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status')
      const data = await res.json()
      setContainers(data)
      setLastUpdated(new Date().toLocaleTimeString())

      // Check if splunk forwarder is done
      const forwarder = data.find(c => c.name.includes('splunk-forwarder'))
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
      <header style={{ marginBottom: '2rem', borderBottom: '1px solid #eee', paddingBottom: '1rem' }}>
        <h1 style={{ margin: 0 }}>White Team Status Dashboard</h1>
        <div style={{ marginTop: '0.5rem', color: '#666' }}>
          Last Updated: {lastUpdated}
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
