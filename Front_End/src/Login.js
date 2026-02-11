import React, { useState } from 'react';
import './Login.css';

// eslint-disable-next-line no-undef
const Login = () => {
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [error, setError] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleEmailSignIn = async (e) => {
    e.preventDefault();
    setIsSigningIn(true);
    setError(null);

    try {
      // eslint-disable-next-line no-undef
      const auth = firebase.auth();
      await auth.signInWithEmailAndPassword(email, password);
      // Auth state change will be detected by App.js and redirect
    } catch (err) {
      console.error('Sign-In Error:', err);
      setError(err.message);
      setIsSigningIn(false);
    }
  };

  const handleSignOut = () => {
    // eslint-disable-next-line no-undef
    firebase.auth().signOut().catch(err => {
      console.error('Sign out error:', err);
    });
  };

  return (
    <div className="login-container">
      <img src="/Buddy.png" alt="Buddy" className="buddy-image-hero" />
      
      <div className="login-box">
        <h2>Sign in to Buddy</h2>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form onSubmit={handleEmailSignIn}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isSigningIn}
            required
            className="login-input"
          />
          
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isSigningIn}
            required
            className="login-input"
          />

          <button 
            type="submit"
            className="login-button"
            disabled={isSigningIn}
          >
            {isSigningIn ? (
              <>
                <span className="spinner"></span>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>
          
        <p className="login-note">
          Secure login powered by Firebase
        </p>
      </div>
    </div>
  );
};

export default Login;