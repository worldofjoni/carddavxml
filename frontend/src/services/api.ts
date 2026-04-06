import axios from 'axios';

// Use empty string to make requests to same origin (nginx will proxy to backend)
// Falls back to localhost:8000 for local development without Docker
const API_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000, // 5 second timeout for all requests
});

export interface PhoneNumber {
  type: string;
  number: string;
  accountindex: number;
}

export interface Email {
  type: string;
  email: string;
}

export interface Organization {
  company: string;
  title: string;
  department: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

export interface Contact {
  id?: number;
  first_name: string;
  last_name: string;
  is_primary: boolean;
  primary: number;
  frequent: number;
  ringtone: string;
  photo_url: string;
  phones: PhoneNumber[];
  emails: Email[];
  groups: string;
  organization: Organization;
  address: Address;
  website: string;
  notes: string;
  birthday: string;
  carddav_uid?: string;
  carddav_etag?: string;
}

export interface ContactGroup {
  id?: number;
  name: string;
  ringtones: string;
}

export interface Settings {
  id?: number;
  carddav_url: string;
  carddav_username: string;
  has_password: boolean;
  sync_enabled: boolean;
  bidirectional_sync: boolean;
  auto_sync_interval: number;
  last_sync?: string;
  last_sync_status?: string;
  last_sync_message?: string;
}

export interface CardDAVSync {
  clear_existing: boolean;
  bidirectional: boolean;
}

// Contact API
export const getContacts = async (): Promise<Contact[]> => {
  const response = await api.get('/api/contacts');
  return response.data;
};

export const getContact = async (id: number): Promise<Contact> => {
  const response = await api.get(`/api/contacts/${id}`);
  return response.data;
};

export const createContact = async (contact: Contact): Promise<Contact> => {
  const response = await api.post('/api/contacts', contact);
  return response.data;
};

export const updateContact = async (id: number, contact: Partial<Contact>): Promise<Contact> => {
  const response = await api.put(`/api/contacts/${id}`, contact);
  return response.data;
};

export const deleteContact = async (id: number): Promise<void> => {
  await api.delete(`/api/contacts/${id}`);
};

// Group API
export const getGroups = async (): Promise<ContactGroup[]> => {
  const response = await api.get('/api/groups');
  return response.data;
};

export const createGroup = async (group: ContactGroup): Promise<ContactGroup> => {
  const response = await api.post('/api/groups', group);
  return response.data;
};

export const deleteGroup = async (id: number): Promise<void> => {
  await api.delete(`/api/groups/${id}`);
};

export const getGroupContacts = async (groupId: number): Promise<Contact[]> => {
  const response = await api.get(`/api/groups/${groupId}/contacts`);
  return response.data;
};

export const addContactsToGroup = async (groupId: number, contactIds: number[]): Promise<{ message: string; added: number[] }> => {
  const response = await api.post(`/api/groups/${groupId}/contacts`, contactIds);
  return response.data;
};

export const removeContactFromGroup = async (groupId: number, contactId: number): Promise<{ message: string }> => {
  const response = await api.delete(`/api/groups/${groupId}/contacts/${contactId}`);
  return response.data;
};

// Settings API
export const getSettings = async (): Promise<Settings> => {
  const response = await api.get('/api/settings');
  return response.data;
};

export const updateSettings = async (settings: Settings): Promise<Settings> => {
  const response = await api.put('/api/settings', settings);
  return response.data;
};

// CardDAV Sync API
export const syncCardDAV = async (syncData: CardDAVSync): Promise<{ message: string; count: number }> => {
  const response = await api.post('/api/sync/carddav', syncData);
  return response.data;
};

export const testCardDAVConnection = async (): Promise<{ message: string; status: string }> => {
  const response = await api.post('/api/sync/test', {});
  return response.data;
};

export const debugCardDAVConnection = async (): Promise<any> => {
  const response = await api.post('/api/sync/debug', {});
  return response.data;
};

export default api;
