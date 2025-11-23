import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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
  carddav_password: string;
  sync_enabled: boolean;
  auto_sync_interval: number;
}

export interface CardDAVSync {
  carddav_url: string;
  carddav_username: string;
  carddav_password: string;
  clear_existing: boolean;
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

export const testCardDAVConnection = async (syncData: CardDAVSync): Promise<{ message: string; status: string }> => {
  const response = await api.post('/api/sync/test', syncData);
  return response.data;
};

export default api;
