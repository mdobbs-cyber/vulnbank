import React, { useState, useEffect } from 'react';

function Dashboard({ token, onLogout }) {
    const [transactions, setTransactions] = useState([]);
    const [search, setSearch] = useState('');
    const [balance, setBalance] = useState(0);

    const fetchTransactions = async (query = '') => {
        try {
            const response = await fetch(`/ledger/transactions/search?q=${query}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            if (Array.isArray(data)) setTransactions(data);
        } catch (err) { console.error(err); }
    };

    useEffect(() => {
        fetchTransactions();
        // Simulate fetching balance (Not essential strictly for the visual update but nice to have)
        // We don't have a "get my balance" endpoint easily accessible without ID.
        // Let's just mock it or assume user ID 1 for demo purposes? No, avoid confusion.
        // Just show a placeholder "Total Assets".
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('site_token');
        onLogout();
    };

    return (
        <div style={{ minHeight: '100vh', background: 'var(--primary)' }}>
            {/* Navbar */}
            <nav className="navbar">
                <div className="logo-container">
                    <img src="/logo.png" alt="Logo" className="logo-img" />
                    <span>VULNERABLE BANK</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span style={{ color: 'var(--text-dim)' }}>Welcome, Client</span>
                    <button onClick={handleLogout} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>LOGOUT</button>
                </div>
            </nav>

            <div className="dashboard-grid animate-fade-in">
                {/* Balance Card */}
                <div className="glass-card" style={{ gridColumn: 'span 2' }}>
                    <h3 style={{ color: 'var(--gold)', margin: '0 0 1rem 0' }}>Total Balance</h3>
                    <div style={{ fontSize: '3rem', fontWeight: 'bold' }}>$1,000,420.00</div>
                    <div style={{ color: 'var(--success)', marginTop: '0.5rem' }}>+2.4% this month</div>
                </div>

                {/* Quick Actions */}
                <div className="glass-card">
                    <h3 style={{ color: 'var(--text-dim)', margin: '0 0 1rem 0' }}>Quick Actions</h3>
                    <div style={{ display: 'flex', gap: '1rem', flexDirection: 'column' }}>
                        <button>New Transfer</button>
                        <button>Download Statements</button>
                    </div>
                </div>

                {/* Transactions */}
                <div className="glass-card" style={{ gridColumn: '1 / -1' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                        <h3 style={{ margin: 0 }}>Recent Transactions</h3>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <input
                                type="text"
                                placeholder="Search transactions..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                style={{ width: '300px', margin: 0 }}
                            />
                            <button onClick={() => fetchTransactions(search)}>Search</button>
                        </div>
                    </div>

                    <table>
                        <thead>
                            <tr>
                                <th>Reference ID</th>
                                <th>Description</th>
                                <th>Date</th>
                                <th style={{ textAlign: 'right' }}>Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            {transactions.map(txn => (
                                <tr key={txn.id}>
                                    <td style={{ color: 'var(--text-dim)' }}>#{txn.id}</td>
                                    <td>
                                        {/* VULNERABILITY: Stored XSS */}
                                        <div dangerouslySetInnerHTML={{ __html: txn.description }} />
                                    </td>
                                    <td style={{ color: 'var(--text-dim)' }}>{new Date(txn.timestamp).toLocaleDateString()}</td>
                                    <td style={{ textAlign: 'right', fontWeight: 'bold', color: txn.amount < 0 ? 'var(--error)' : 'var(--success)' }}>
                                        {txn.amount < 0 ? '-' : '+'}${Math.abs(txn.amount).toFixed(2)}
                                    </td>
                                </tr>
                            ))}
                            {transactions.length === 0 && (
                                <tr>
                                    <td colSpan="4" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)' }}>No transactions found.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <footer style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
                &copy; 2023 Vulnerable Bank Corp. All rights reserved. <br />
                Authorized Use Only. System Integrity Monitored.
            </footer>
        </div>
    );
}

export default Dashboard;
