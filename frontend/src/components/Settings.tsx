import React, { useEffect, useState } from 'react';
import {
  getSettings,
  updateSettings,
  syncCardDAV,
  testCardDAVConnection,
  debugCardDAVConnection,
  Settings as SettingsType,
} from '../services/api';
import './Settings.css';

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SettingsType>({
    carddav_url: '',
    carddav_username: '',
    has_password: false,
    sync_enabled: false,
    bidirectional_sync: false,
    auto_sync_interval: 3600,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [debugging, setDebugging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [clearExisting, setClearExisting] = useState(false);
  const [bidirectionalSync, setBidirectionalSync] = useState(false);
  const [verifySSL, setVerifySSL] = useState(true);
  const [debugResults, setDebugResults] = useState<any>(null);
  const [passwordInput, setPasswordInput] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await getSettings();
      setSettings(data);
      setPasswordInput('');
      setError(null);
    } catch (err) {
      setError('Failed to load settings');
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
      setSaving(true);
      const updatedSettings = {
        ...settings,
        ...(passwordInput ? { carddav_password: passwordInput } : {})
      };
      await updateSettings(updatedSettings as SettingsType);
      setPasswordInput('');
      setSuccess('Settings saved successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save settings');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setError(null);
    setSuccess(null);

    try {
      setTesting(true);
      const result = await testCardDAVConnection();
      setSuccess(result.message);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Connection test failed');
      console.error(err);
    } finally {
      setTesting(false);
    }
  };

  const handleDebug = async () => {
    setError(null);
    setSuccess(null);
    setDebugResults(null);

    try {
      setDebugging(true);
      const result = await debugCardDAVConnection();
      setDebugResults(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Debug failed');
      console.error(err);
    } finally {
      setDebugging(false);
    }
  };

  const handleSync = async () => {
    if (clearExisting && !window.confirm('This will delete all existing contacts. Are you sure?')) {
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      setSyncing(true);
      const result = await syncCardDAV({
        clear_existing: clearExisting,
        bidirectional: bidirectionalSync,
      });
      setSuccess(result.message);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Sync failed');
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    let finalValue: any = value;

    if (type === 'checkbox') {
      finalValue = checked;
    } else if (name === 'auto_sync_interval') {
      finalValue = parseInt(value);
    } else if (type === 'number') {
      finalValue = parseInt(value);
    }

    setSettings(prev => ({
      ...prev,
      [name]: finalValue,
    }));
  };

  if (loading) {
    return <div className="loading">Loading settings...</div>;
  }

  // Use current window location for phonebook URL (works with IP addresses and remote access)
  const phonebookUrl = `${window.location.origin}/phonebook.xml`;

  return (
    <div className="container">
      <div className="page-header">
        <h2 className="page-title">Settings</h2>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* XML Phonebook Info */}
      <div className="settings-section">
        <h3 className="settings-section-title">XML Phonebook URL</h3>
        <div className="phonebook-url-card">
          <p>Configure your Grandstream phone to use this URL for the phonebook:</p>
          <div className="url-display">
            <code>{phonebookUrl}</code>
            <button
              className="btn btn-secondary btn-small"
              onClick={() => {
                navigator.clipboard.writeText(phonebookUrl);
                setSuccess('URL copied to clipboard!');
                setTimeout(() => setSuccess(null), 3000);
              }}
            >
              Copy
            </button>
          </div>
          <p className="url-help">
            <a href={phonebookUrl} target="_blank" rel="noopener noreferrer">
              Open XML Phonebook
            </a>
          </p>
        </div>
      </div>

      {/* CardDAV Settings */}
      <div className="settings-section">
        <h3 className="settings-section-title">CardDAV Server Configuration</h3>

        <form onSubmit={handleSubmit} className="settings-form">
          <div className="form-group">
            <label htmlFor="carddav_url">CardDAV Server URL</label>
            <input
              type="url"
              id="carddav_url"
              name="carddav_url"
              value={settings.carddav_url}
              onChange={handleChange}
              placeholder="https://carddav.example.com/addressbooks/user/"
            />
            <small className="form-help">
              Enter the full CardDAV URL including the path to your address book
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="carddav_username">Username</label>
            <input
              type="text"
              id="carddav_username"
              name="carddav_username"
              value={settings.carddav_username}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="carddav_password">Password</label>
            <input
              type="password"
              id="carddav_password"
              value={passwordInput}
              onChange={(e) => setPasswordInput(e.target.value)}
              autoComplete="new-password"
              placeholder={settings.has_password ? "••••••••" : "Enter password"}
            />
            <small className="form-help">
              {settings.has_password ? 'Enter new password to update, or leave blank to keep current.' : 'Enter your CardDAV password.'}
            </small>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={verifySSL}
                onChange={(e) => setVerifySSL(e.target.checked)}
              />
              Verify SSL/TLS certificates
            </label>
            <small className="form-help">
              Uncheck this if your server uses self-signed certificates
            </small>
          </div>

          <div className="form-actions">
            <button
              type="button"
              onClick={handleDebug}
              className="btn btn-secondary"
              disabled={debugging || !settings.carddav_url}
            >
              {debugging ? 'Debugging...' : 'Debug Connection'}
            </button>
            <button
              type="button"
              onClick={handleTestConnection}
              className="btn btn-secondary"
              disabled={testing || !settings.carddav_url}
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>

        {/* Debug Results */}
        {debugResults && (
          <div className="debug-results">
            <h4>Debug Results</h4>

            {debugResults.tests.map((test: any, index: number) => (
              <div key={index} className={`debug-test ${test.status === 'success' ? 'success' : 'failed'}`}>
                <h5>
                  {test.status === 'success' ? '✓' : '✗'} {test.name}
                </h5>
                {test.status === 'success' && test.details && (
                  <pre>{typeof test.details === 'string' ? test.details : JSON.stringify(test.details, null, 2)}</pre>
                )}
                {test.status === 'failed' && test.error && (
                  <div className="error-message">{test.error}</div>
                )}
              </div>
            ))}

            {debugResults.suggestions && debugResults.suggestions.length > 0 && (
              <div className="debug-suggestions">
                <h5>Suggested URLs to try:</h5>
                <ul>
                  {debugResults.suggestions.map((url: string, index: number) => (
                    <li key={index}>
                      <code>{url}</code>
                      <button
                        className="btn btn-secondary btn-small"
                        onClick={() => {
                          setSettings(prev => ({ ...prev, carddav_url: url }));
                          setDebugResults(null);
                        }}
                      >
                        Use This
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Auto-Sync Configuration */}
      <div className="settings-section">
        <h3 className="settings-section-title">Automatic Synchronization</h3>

        <div className="auto-sync-controls">
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                name="sync_enabled"
                checked={settings.sync_enabled}
                onChange={handleChange}
              />
              Enable automatic synchronization
            </label>
            <small className="form-help">
              Automatically sync contacts from CardDAV server at regular intervals
            </small>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                name="bidirectional_sync"
                checked={settings.bidirectional_sync}
                onChange={handleChange}
              />
              Enable bidirectional sync (push changes to CardDAV)
            </label>
            <small className="form-help">
              When enabled, contacts created/edited/deleted in the web UI will automatically sync back to your CardDAV server. Disable to only retrieve contacts from CardDAV.
            </small>
          </div>

          {settings.sync_enabled && (
            <div className="form-group">
              <label htmlFor="auto_sync_interval">Sync Interval (seconds)</label>
              <select
                id="auto_sync_interval"
                name="auto_sync_interval"
                value={settings.auto_sync_interval}
                onChange={handleChange}
              >
                <option value="300">5 minutes (300 seconds)</option>
                <option value="600">10 minutes (600 seconds)</option>
                <option value="900">15 minutes (900 seconds)</option>
                <option value="1800">30 minutes (1800 seconds)</option>
                <option value="3600">1 hour (3600 seconds)</option>
                <option value="7200">2 hours (7200 seconds)</option>
                <option value="14400">4 hours (14400 seconds)</option>
                <option value="21600">6 hours (21600 seconds)</option>
                <option value="43200">12 hours (43200 seconds)</option>
                <option value="86400">24 hours (86400 seconds)</option>
              </select>
              <small className="form-help">
                How often to automatically sync contacts from your CardDAV server
              </small>
            </div>
          )}

          {settings.last_sync && (
            <div className="sync-status">
              <h4>Last Sync Status</h4>
              <div className={`sync-status-card ${settings.last_sync_status}`}>
                <div className="sync-status-row">
                  <strong>Time:</strong>
                  <span>{new Date(settings.last_sync).toLocaleString()}</span>
                </div>
                <div className="sync-status-row">
                  <strong>Status:</strong>
                  <span className={`status-badge ${settings.last_sync_status}`}>
                    {settings.last_sync_status === 'success' && '✓ Success'}
                    {settings.last_sync_status === 'failed' && '✗ Failed'}
                    {settings.last_sync_status === 'running' && '⟳ Running'}
                  </span>
                </div>
                {settings.last_sync_message && (
                  <div className="sync-status-row">
                    <strong>Message:</strong>
                    <span>{settings.last_sync_message}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          <button
            onClick={handleSubmit}
            className="btn btn-primary"
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Auto-Sync Settings'}
          </button>
        </div>
      </div>

      {/* Manual Sync Controls */}
      <div className="settings-section">
        <h3 className="settings-section-title">Manual Synchronization</h3>

        <div className="sync-controls">
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={clearExisting}
                onChange={(e) => setClearExisting(e.target.checked)}
              />
              Clear existing contacts before sync
            </label>
            <small className="form-help warning">
              Warning: This will delete all current contacts in the database
            </small>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={bidirectionalSync}
                onChange={(e) => setBidirectionalSync(e.target.checked)}
              />
              Bidirectional sync (push local changes to server)
            </label>
          </div>

          <button
            onClick={handleSync}
            className="btn btn-success"
            disabled={syncing || !settings.carddav_url}
          >
            {syncing ? 'Syncing...' : 'Sync Now'}
          </button>
        </div>
      </div>

      {/* Instructions */}
      <div className="settings-section">
        <h3 className="settings-section-title">Setup Instructions</h3>
        <div className="instructions">
          <ol>
            <li>
              <strong>Configure CardDAV Server:</strong> Enter your CardDAV server URL,
              username, and password above. Click "Test Connection" to verify the settings.
            </li>
            <li>
              <strong>Sync Contacts:</strong> Click "Sync Now" to import contacts from your
              CardDAV server. You can choose to clear existing contacts first.
            </li>
            <li>
              <strong>Configure Grandstream Phone:</strong> Go to your phone's web interface,
              navigate to Phonebook settings, and add a new XML phonebook entry using the URL shown above.
            </li>
            <li>
              <strong>Manual Entry:</strong> You can also manually add, edit, and delete contacts
              using the Contacts page.
            </li>
          </ol>

          <div className="info-box">
            <h4>Supported CardDAV Servers:</h4>
            <ul>
              <li>Nextcloud</li>
              <li>iCloud</li>
              <li>Google Contacts (via CardDAV)</li>
              <li>Synology CardDAV Server</li>
              <li>Radicale</li>
              <li>Baïkal</li>
              <li>Any standard CardDAV-compliant server</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
