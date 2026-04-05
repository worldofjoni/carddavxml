import React, { useEffect, useState } from 'react';
import { 
  getGroups, createGroup, deleteGroup, 
  getContacts, getGroupContacts, addContactsToGroup, removeContactFromGroup,
  ContactGroup, Contact 
} from '../services/api';
import './GroupList.css';

const GroupList: React.FC = () => {
  const [groups, setGroups] = useState<ContactGroup[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [newGroup, setNewGroup] = useState<ContactGroup>({
    name: '',
    ringtones: '',
  });
  const [expandedGroups, setExpandedGroups] = useState<Set<number>>(new Set());
  const [groupContacts, setGroupContacts] = useState<Record<number, Contact[]>>({});
  const [showAddModal, setShowAddModal] = useState<number | null>(null);
  const [selectedContacts, setSelectedContacts] = useState<Set<number>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [groupsData, contactsData] = await Promise.all([
        getGroups(),
        getContacts()
      ]);
      setGroups(groupsData);
      setContacts(contactsData);

      const groupContactsData: Record<number, Contact[]> = {};
      for (const group of groupsData) {
        try {
          const members = await getGroupContacts(group.id!);
          groupContactsData[group.id!] = members;
        } catch (err) {
          groupContactsData[group.id!] = [];
        }
      }
      setGroupContacts(groupContactsData);

      setError(null);
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadGroupContacts = async (groupId: number) => {
    try {
      const members = await getGroupContacts(groupId);
      setGroupContacts(prev => ({ ...prev, [groupId]: members }));
    } catch (err) {
      console.error('Failed to load group contacts:', err);
    }
  };

  const toggleGroup = async (groupId: number) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId);
    } else {
      newExpanded.add(groupId);
      if (!groupContacts[groupId]) {
        await loadGroupContacts(groupId);
      }
    }
    setExpandedGroups(newExpanded);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await createGroup(newGroup);
      setNewGroup({ name: '', ringtones: '' });
      setShowForm(false);
      await loadData();
    } catch (err) {
      alert('Failed to create group');
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this group?')) {
      try {
        await deleteGroup(id);
        await loadData();
        setGroupContacts(prev => {
          const newContacts = { ...prev };
          delete newContacts[id];
          return newContacts;
        });
      } catch (err) {
        alert('Failed to delete group');
        console.error(err);
      }
    }
  };

  const handleRemoveFromGroup = async (groupId: number, contactId: number) => {
    try {
      await removeContactFromGroup(groupId, contactId);
      setGroupContacts(prev => ({
        ...prev,
        [groupId]: prev[groupId].filter(c => c.id !== contactId)
      }));
    } catch (err) {
      alert('Failed to remove contact from group');
      console.error(err);
    }
  };

  const openAddModal = (groupId: number) => {
    const groupMemberIds = new Set((groupContacts[groupId] || []).map(c => c.id));
    const availableContacts = contacts.filter(c => !groupMemberIds.has(c.id));
    setSelectedContacts(new Set());
    setSearchTerm('');
    setShowAddModal(groupId);
  };

  const toggleContactSelection = (contactId: number) => {
    const newSelected = new Set(selectedContacts);
    if (newSelected.has(contactId)) {
      newSelected.delete(contactId);
    } else {
      newSelected.add(contactId);
    }
    setSelectedContacts(newSelected);
  };

  const handleAddContacts = async () => {
    if (!showAddModal || selectedContacts.size === 0) return;

    try {
      await addContactsToGroup(showAddModal, Array.from(selectedContacts));
      await loadGroupContacts(showAddModal);
      setShowAddModal(null);
      setSelectedContacts(new Set());
    } catch (err) {
      alert('Failed to add contacts to group');
      console.error(err);
    }
  };

  const getContactDisplayName = (contact: Contact) => {
    return `${contact.first_name} ${contact.last_name}`.trim() || 'Unnamed Contact';
  };

  const getContactPhone = (contact: Contact) => {
    if (contact.phones && contact.phones.length > 0) {
      return contact.phones[0].number;
    }
    return '';
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
              <div className="group-header" onClick={() => toggleGroup(group.id!)}>
                <div className="group-info">
                  <h3 className="group-name">{group.name}</h3>
                  <span className="group-member-count">
                    {(groupContacts[group.id!] || []).length} member(s)
                  </span>
                </div>
                <span className="expand-icon">{expandedGroups.has(group.id!) ? '▼' : '▶'}</span>
              </div>

              {expandedGroups.has(group.id!) && (
                <div className="group-content">
                  {group.ringtones && (
                    <div className="group-detail">
                      <strong>Ringtone:</strong> {group.ringtones}
                    </div>
                  )}

                  <div className="group-members">
                    <div className="members-header">
                      <h4>Members</h4>
                      <button
                        onClick={() => openAddModal(group.id!)}
                        className="btn btn-small btn-primary"
                      >
                        + Add Members
                      </button>
                    </div>

                    {(groupContacts[group.id!] || []).length === 0 ? (
                      <div className="no-members">No members in this group</div>
                    ) : (
                      <div className="member-list">
                        {(groupContacts[group.id!] || []).map(contact => (
                          <div key={contact.id} className="member-item">
                            <div className="member-info">
                              <span className="member-name">{getContactDisplayName(contact)}</span>
                              {getContactPhone(contact) && (
                                <span className="member-phone">{getContactPhone(contact)}</span>
                              )}
                            </div>
                            <button
                              onClick={() => handleRemoveFromGroup(group.id!, contact.id!)}
                              className="btn btn-small btn-danger"
                            >
                              Remove
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="group-actions">
                    <button
                      onClick={() => handleDelete(group.id!)}
                      className="btn btn-danger btn-small"
                    >
                      Delete Group
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Members to Group</h3>
              <button onClick={() => setShowAddModal(null)} className="modal-close">&times;</button>
            </div>
            <div className="modal-body">
              <div className="modal-search">
                <input
                  type="text"
                  placeholder="Search contacts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="available-contacts">
                {(() => {
                  const groupMemberIds = new Set((groupContacts[showAddModal] || []).map(gc => gc.id));
                  const filteredContacts = contacts.filter(c => {
                    if (groupMemberIds.has(c.id)) return false;
                    if (!searchTerm) return true;
                    const search = searchTerm.toLowerCase();
                    const name = getContactDisplayName(c).toLowerCase();
                    const phone = getContactPhone(c).toLowerCase();
                    return name.includes(search) || phone.includes(search);
                  });
                  return filteredContacts.length === 0 ? (
                    <div className="no-contacts">
                      {searchTerm ? 'No contacts match your search' : 'All contacts are already in this group'}
                    </div>
                  ) : (
                    filteredContacts.map(contact => (
                      <div 
                        key={contact.id}
                        className={`contact-option ${selectedContacts.has(contact.id!) ? 'selected' : ''}`}
                        onClick={() => toggleContactSelection(contact.id!)}
                      >
                        <input
                          type="checkbox"
                          checked={selectedContacts.has(contact.id!)}
                          onChange={() => toggleContactSelection(contact.id!)}
                        />
                        <span className="contact-option-name">{getContactDisplayName(contact)}</span>
                        {getContactPhone(contact) && (
                          <span className="contact-option-phone">{getContactPhone(contact)}</span>
                        )}
                      </div>
                    ))
                  );
                })()}
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowAddModal(null)} className="btn btn-secondary">
                Cancel
              </button>
              <button 
                onClick={handleAddContacts} 
                className="btn btn-primary"
                disabled={selectedContacts.size === 0}
              >
                Add Selected ({selectedContacts.size})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupList;
