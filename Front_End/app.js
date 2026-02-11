// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyCEXJGsr_4UBE6w5mbudfPHR1KNCDh5thk",
    authDomain: "buddy-aeabf.firebaseapp.com",
    projectId: "buddy-aeabf",
    storageBucket: "buddy-aeabf.firebasestorage.app",
    messagingSenderId: "501753640467",
    appId: "1:501753640467:web:c2a3edbb3ee17fed5fb1e6",
    measurementId: "G-67JSL6RPEG"
};

// Initialize Firebase
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

// Auth state observer - show/hide login and React app
firebase.auth().onAuthStateChanged((user) => {
    const loginSection = document.getElementById('login-section');
    const reactApp = document.getElementById('root');

    if (user) {
        // User logged in - hide login, show React app
        console.log('User signed in:', user.email);
        if (loginSection) loginSection.style.display = 'none';
        if (reactApp) reactApp.style.display = 'block';
        localStorage.setItem('userEmail', user.email);
        localStorage.setItem('userId', user.uid);
        
        // Load React bundle
        if (!window.reactBundleLoaded) {
            window.reactBundleLoaded = true;
            const script = document.createElement('script');
            script.src = '/static/js/main.8f1ea2af.js?v=20260210';
            script.defer = true;
            document.head.appendChild(script);
        }
    } else {
        // User logged out - show login, hide React app
        console.log('User signed out');
        if (loginSection) loginSection.style.display = 'flex';
        if (reactApp) reactApp.style.display = 'none';
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userId');
    }
});

console.log('Firebase app initialized');
