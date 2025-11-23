import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  getContact,
  createContact,
  updateContact,
  getGroups,
  Contact,
  ContactGroup,
  PhoneNumber,
  Email,
} from '../services/api';
import './ContactForm.css';

const ContactForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = !!id;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [groups, setGroups] = useState<ContactGroup[]>([]);

  const [formData, setFormData] = useState<Contact>({
    first_name: '',
    last_name: '',
    is_primary: false,
    primary: 0,
    frequent: 0,
    ringtone: '',
    photo_url: '',
    phones: [],
    emails: [],
    groups: '',
    organization: { company: '', title: '', department: '' },
    address: { street: '', city: '', state: '', postal_code: '', country: '' },
    website: '',
    notes: '',
    birthday: '',
  });

  useEffect(() => {
    loadGroups();
    if (isEditMode) {
      loadContact();
    }
  }, [id]);

  const loadGroups = async () => {
    try {
      const data = await getGroups();
      setGroups(data);
    } catch (err) {
      console.error('Failed to load groups:', err);
    }
  };

  const loadContact = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const data = await getContact(parseInt(id));
      setFormData(data);
    } catch (err) {
      setError('Failed to load contact');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      setLoading(true);

      if (isEditMode && id) {
        await updateContact(parseInt(id), formData);
        setSuccess('Contact updated successfully');
      } else {
        await createContact(formData);
        setSuccess('Contact created successfully');
      }

      setTimeout(() => navigate('/'), 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save contact');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleOrganizationChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      organization: {
        ...prev.organization,
        [field]: value,
      },
    }));
  };

  const handleAddressChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      address: {
        ...prev.address,
        [field]: value,
      },
    }));
  };

  const addPhone = () => {
    setFormData(prev => ({
      ...prev,
      phones: [...prev.phones, { type: 'Mobile', number: '', accountindex: -1 }],
    }));
  };

  const updatePhone = (index: number, field: keyof PhoneNumber, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      phones: prev.phones.map((phone, i) =>
        i === index ? { ...phone, [field]: value } : phone
      ),
    }));
  };

  const removePhone = (index: number) => {
    setFormData(prev => ({
      ...prev,
      phones: prev.phones.filter((_, i) => i !== index),
    }));
  };

  const addEmail = () => {
    setFormData(prev => ({
      ...prev,
      emails: [...prev.emails, { type: 'Home', email: '' }],
    }));
  };

  const updateEmail = (index: number, field: keyof Email, value: string) => {
    setFormData(prev => ({
      ...prev,
      emails: prev.emails.map((email, i) =>
        i === index ? { ...email, [field]: value } : email
      ),
    }));
  };

  const removeEmail = (index: number) => {
    setFormData(prev => ({
      ...prev,
      emails: prev.emails.filter((_, i) => i !== index),
    }));
  };

  if (loading && isEditMode) {
    return <div className="loading">Loading contact...</div>;
  }

  return (
    <div className="container">
      <div className="page-header">
        <h2 className="page-title">
          {isEditMode ? 'Edit Contact' : 'Add New Contact'}
        </h2>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit} className="contact-form">
        {/* Basic Information */}
        <div className="form-section">
          <h3 className="form-section-title">Basic Information</h3>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">First Name *</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Last Name</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="frequent">
                <input
                  type="checkbox"
                  id="frequent"
                  checked={formData.frequent > 0}
                  onChange={(e) =>
                    setFormData(prev => ({ ...prev, frequent: e.target.checked ? 1 : 0 }))
                  }
                />
                Mark as Frequent
              </label>
            </div>
          </div>
        </div>

        {/* Phone Numbers */}
        <div className="form-section">
          <div className="form-section-header">
            <h3 className="form-section-title">Phone Numbers</h3>
            <button type="button" onClick={addPhone} className="btn btn-secondary btn-small">
              + Add Phone
            </button>
          </div>

          {formData.phones.map((phone, index) => (
            <div key={index} className="dynamic-field">
              <div className="form-row">
                <div className="form-group">
                  <select
                    value={phone.type}
                    onChange={(e) => updatePhone(index, 'type', e.target.value)}
                  >
                    <option value="Mobile">Mobile</option>
                    <option value="Home">Home</option>
                    <option value="Work">Work</option>
                    <option value="Work Fax">Work Fax</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="form-group flex-grow">
                  <input
                    type="tel"
                    placeholder="Phone number"
                    value={phone.number}
                    onChange={(e) => updatePhone(index, 'number', e.target.value)}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => removePhone(index)}
                  className="btn btn-danger btn-small"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Email Addresses */}
        <div className="form-section">
          <div className="form-section-header">
            <h3 className="form-section-title">Email Addresses</h3>
            <button type="button" onClick={addEmail} className="btn btn-secondary btn-small">
              + Add Email
            </button>
          </div>

          {formData.emails.map((email, index) => (
            <div key={index} className="dynamic-field">
              <div className="form-row">
                <div className="form-group">
                  <select
                    value={email.type}
                    onChange={(e) => updateEmail(index, 'type', e.target.value)}
                  >
                    <option value="Home">Home</option>
                    <option value="Work">Work</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="form-group flex-grow">
                  <input
                    type="email"
                    placeholder="Email address"
                    value={email.email}
                    onChange={(e) => updateEmail(index, 'email', e.target.value)}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => removeEmail(index)}
                  className="btn btn-danger btn-small"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Organization */}
        <div className="form-section">
          <h3 className="form-section-title">Organization</h3>

          <div className="form-group">
            <label htmlFor="company">Company</label>
            <input
              type="text"
              id="company"
              value={formData.organization.company}
              onChange={(e) => handleOrganizationChange('company', e.target.value)}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="title">Title</label>
              <input
                type="text"
                id="title"
                value={formData.organization.title}
                onChange={(e) => handleOrganizationChange('title', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="department">Department</label>
              <input
                type="text"
                id="department"
                value={formData.organization.department}
                onChange={(e) => handleOrganizationChange('department', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Address */}
        <div className="form-section">
          <h3 className="form-section-title">Address</h3>

          <div className="form-group">
            <label htmlFor="street">Street</label>
            <input
              type="text"
              id="street"
              value={formData.address.street}
              onChange={(e) => handleAddressChange('street', e.target.value)}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="city">City</label>
              <input
                type="text"
                id="city"
                value={formData.address.city}
                onChange={(e) => handleAddressChange('city', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="state">State</label>
              <input
                type="text"
                id="state"
                value={formData.address.state}
                onChange={(e) => handleAddressChange('state', e.target.value)}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="postal_code">Postal Code</label>
              <input
                type="text"
                id="postal_code"
                value={formData.address.postal_code}
                onChange={(e) => handleAddressChange('postal_code', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="country">Country</label>
              <input
                type="text"
                id="country"
                value={formData.address.country}
                onChange={(e) => handleAddressChange('country', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Additional Information */}
        <div className="form-section">
          <h3 className="form-section-title">Additional Information</h3>

          <div className="form-group">
            <label htmlFor="website">Website</label>
            <input
              type="url"
              id="website"
              name="website"
              value={formData.website}
              onChange={handleChange}
              placeholder="https://example.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="birthday">Birthday</label>
            <input
              type="date"
              id="birthday"
              name="birthday"
              value={formData.birthday}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="groups">Groups (comma-separated IDs)</label>
            <input
              type="text"
              id="groups"
              name="groups"
              value={formData.groups}
              onChange={handleChange}
              placeholder="e.g., 1,2,3"
            />
            {groups.length > 0 && (
              <small className="form-help">
                Available groups: {groups.map(g => `${g.name} (${g.id})`).join(', ')}
              </small>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="ringtone">Ringtone Path</label>
            <input
              type="text"
              id="ringtone"
              name="ringtone"
              value={formData.ringtone}
              onChange={handleChange}
              placeholder="/system/media/audio/ringtones/..."
            />
          </div>

          <div className="form-group">
            <label htmlFor="photo_url">Photo URL</label>
            <input
              type="url"
              id="photo_url"
              name="photo_url"
              value={formData.photo_url}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Form Actions */}
        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : (isEditMode ? 'Update Contact' : 'Create Contact')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ContactForm;
