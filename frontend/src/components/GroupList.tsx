import React, { useEffect, useState } from 'react';
import { getGroups, createGroup, deleteGroup, ContactGroup } from '../services/api';
import './GroupList.css';

const GroupList: React.FC = () => {
  const [groups, setGroups] = useState<ContactGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [newGroup, setNewGroup] = useState<ContactGroup>({
    name: '',
    ringtones: '',
  });

  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    try {
      setLoading(true);
      const data = await getGroups();
      setGroups(data);
      setError(null);
    } catch (err) {
      setError('Failed to load groups');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await createGroup(newGroup);
      setNewGroup({ name: '', ringtones: '' });
      setShowForm(false);
      await loadGroups();
    } catch (err) {
      alert('Failed to create group');
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this group?')) {
      try {
        await deleteGroup(id);
        await loadGroups();
      } catch (err) {
        alert('Failed to delete group');
        console.error(err);
      }
    }
  };

  if (loading) {
    return <div className="loading">Loading groups...</div>;
  }

  return (
    <div className="container">
      <div className="page-header">
        <h2 className="page-title">Contact Groups</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-primary"
        >
          {showForm ? 'Cancel' : '+ Add Group'}
        </button>
      </div>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      {showForm && (
        <div className="group-form-card">
          <h3>New Group</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="name">Group Name *</label>
              <input
                type="text"
                id="name"
                value={newGroup.name}
                onChange={(e) => setNewGroup({ ...newGroup, name: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="ringtones">Ringtones Path</label>
              <input
                type="text"
                id="ringtones"
                value={newGroup.ringtones}
                onChange={(e) => setNewGroup({ ...newGroup, ringtones: e.target.value })}
                placeholder="/system/media/audio/ringtones/..."
              />
            </div>

            <button type="submit" className="btn btn-success">
              Create Group
            </button>
          </form>
        </div>
      )}

      {groups.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📁</div>
          <div className="empty-state-text">No groups yet</div>
          <button
            onClick={() => setShowForm(true)}
            className="btn btn-primary"
          >
            Create Your First Group
          </button>
        </div>
      ) : (
        <div className="group-list">
          {groups.map(group => (
            <div key={group.id} className="group-card">
              <div className="group-header">
                <h3 className="group-name">{group.name}</h3>
                <span className="group-id">ID: {group.id}</span>
              </div>

              {group.ringtones && (
                <div className="group-detail">
                  <strong>Ringtone:</strong> {group.ringtones}
                </div>
              )}

              <div className="group-actions">
                <button
                  onClick={() => handleDelete(group.id!)}
                  className="btn btn-danger btn-small"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="group-info">
        <h3>About Groups</h3>
        <p>
          Groups allow you to organize your contacts. When creating or editing a contact,
          you can assign them to one or more groups by entering comma-separated group IDs.
        </p>
        <p>
          <strong>Example:</strong> If you have groups with IDs 1, 2, and 3, you can assign
          a contact to multiple groups by entering "1,2,3" in the contact's Groups field.
        </p>
      </div>
    </div>
  );
};

export default GroupList;
