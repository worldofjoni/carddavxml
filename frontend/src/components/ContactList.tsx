import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getContacts, deleteContact, Contact } from '../services/api';
import './ContactList.css';

const ContactList: React.FC = () => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadContacts();
  }, []);

  const loadContacts = async () => {
    try {
      setLoading(true);
      const data = await getContacts();
      setContacts(data);
      setError(null);
    } catch (err) {
      setError('Failed to load contacts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this contact?')) {
      try {
        await deleteContact(id);
        await loadContacts();
      } catch (err) {
        alert('Failed to delete contact');
        console.error(err);
      }
    }
  };

  const filteredContacts = contacts.filter(contact => {
    const searchLower = searchTerm.toLowerCase();
    return (
      contact.first_name.toLowerCase().includes(searchLower) ||
      contact.last_name.toLowerCase().includes(searchLower) ||
      contact.phones.some(phone => phone.number.includes(searchTerm)) ||
      contact.emails.some(email => email.email.toLowerCase().includes(searchLower))
    );
  });

  if (loading) {
    return <div className="loading">Loading contacts...</div>;
  }

  return (
    <div className="container">
      <div className="page-header">
        <h2 className="page-title">Contacts</h2>
        <Link to="/contact/new" className="btn btn-primary">
          + Add Contact
        </Link>
      </div>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      <div className="search-box">
        <input
          type="text"
          placeholder="Search contacts..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      {filteredContacts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📇</div>
          <div className="empty-state-text">
            {searchTerm ? 'No contacts found' : 'No contacts yet'}
          </div>
          {!searchTerm && (
            <Link to="/contact/new" className="btn btn-primary">
              Add Your First Contact
            </Link>
          )}
        </div>
      ) : (
        <div className="contact-grid">
          {filteredContacts.map(contact => (
            <div key={contact.id} className="contact-card">
              <div className="contact-header">
                <h3 className="contact-name">
                  {contact.first_name} {contact.last_name}
                </h3>
                {contact.frequent > 0 && (
                  <span className="badge badge-star">★</span>
                )}
              </div>

              {contact.organization?.company && (
                <div className="contact-detail">
                  <strong>Company:</strong> {contact.organization.company}
                </div>
              )}

              {contact.organization?.title && (
                <div className="contact-detail">
                  <strong>Title:</strong> {contact.organization.title}
                </div>
              )}

              {contact.phones.length > 0 && (
                <div className="contact-detail">
                  <strong>Phone:</strong>
                  {contact.phones.map((phone, idx) => (
                    <div key={idx} className="contact-phone">
                      <span className="phone-type">{phone.type}:</span> {phone.number}
                    </div>
                  ))}
                </div>
              )}

              {contact.emails.length > 0 && (
                <div className="contact-detail">
                  <strong>Email:</strong>
                  {contact.emails.map((email, idx) => (
                    <div key={idx} className="contact-email">
                      <span className="email-type">{email.type}:</span> {email.email}
                    </div>
                  ))}
                </div>
              )}

              <div className="contact-actions">
                <Link
                  to={`/contact/edit/${contact.id}`}
                  className="btn btn-secondary btn-small"
                >
                  Edit
                </Link>
                <button
                  onClick={() => handleDelete(contact.id!)}
                  className="btn btn-danger btn-small"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContactList;
