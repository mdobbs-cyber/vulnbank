import React, { useState } from 'react';

function Login({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: params,
            });

            if (!response.ok) throw new Error('Invalid credentials');

            const data = await response.json();
            localStorage.setItem('site_token', data.access_token); // VULNERABLE
            onLogin(data.access_token);
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div style={{
            height: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'radial-gradient(circle at 50% 50%, #172a45 0%, #0a192f 100%)'
        }}>
            <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '400px' }}>
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <img src="/logo.png" alt="Vulnerable Bank" className="logo-img" style={{ height: '60px', marginBottom: '1rem' }} />
                    <h2 style={{ color: 'var(--text)', margin: 0 }}>Welcome Back</h2>
                    <p style={{ color: 'var(--text-dim)', marginTop: '0.5rem' }}>Secure Login to Vulnerable Bank</p>
                </div>

                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', color: 'var(--gold)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter your username"
                        />
                    </div>
                    <div style={{ marginBottom: '2rem' }}>
                        <label style={{ display: 'block', color: 'var(--gold)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                        />
                    </div>
                    <button type="submit" style={{ width: '100%' }}>LOGIN SECURELY</button>
                </form>
                {error && (
                    <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(255, 95, 95, 0.1)', border: '1px solid var(--error)', borderRadius: '4px', color: 'var(--error)', textAlign: 'center' }}>
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Login;
