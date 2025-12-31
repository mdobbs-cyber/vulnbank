import React, { useState, useEffect } from 'react';
import Login from './Login';
import Dashboard from './Dashboard';

function App() {
    const [token, setToken] = useState(localStorage.getItem('site_token'));

    return (
        <div>
            {token ? (
                <Dashboard token={token} onLogout={() => setToken(null)} />
            ) : (
                <Login onLogin={(t) => setToken(t)} />
            )}
        </div>
    );
}

export default App;
