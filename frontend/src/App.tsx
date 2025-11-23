import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import ContactList from './components/ContactList';
import ContactForm from './components/ContactForm';
import GroupList from './components/GroupList';
import Settings from './components/Settings';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="navbar-container">
            <h1 className="navbar-title">CardDAV Phonebook</h1>
            <ul className="navbar-menu">
              <li><Link to="/">Contacts</Link></li>
              <li><Link to="/groups">Groups</Link></li>
              <li><Link to="/settings">Settings</Link></li>
              <li>
                <a href={`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/phonebook.xml`}
                   target="_blank"
                   rel="noopener noreferrer">
                  Download XML
                </a>
              </li>
            </ul>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<ContactList />} />
            <Route path="/contact/new" element={<ContactForm />} />
            <Route path="/contact/edit/:id" element={<ContactForm />} />
            <Route path="/groups" element={<GroupList />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
