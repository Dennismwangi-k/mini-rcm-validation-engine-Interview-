import React, { useState, useEffect } from 'react';
import { rulesetsAPI, RuleSet, CreateRuleSetData } from '../api/rulesets';
import './RuleSetManager.css';

interface RuleSetManagerProps {
  onClose?: () => void;
}

const RuleSetManager: React.FC<RuleSetManagerProps> = ({ onClose }) => {
  const [rulesets, setRulesets] = useState<RuleSet[]>([]);
  const [activeRuleset, setActiveRuleset] = useState<RuleSet | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<CreateRuleSetData & { technical_rules_file?: File | null; medical_rules_file?: File | null }>({
    name: '',
    description: '',
    is_active: false,
    paid_amount_threshold: 250.00,
    technical_rules_file: null,
    medical_rules_file: null,
  });
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadRuleSets();
    loadActiveRuleSet();
  }, []);

  const loadRuleSets = async () => {
    try {
      const data = await rulesetsAPI.getRuleSets();
      setRulesets(data.results || data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load rule sets:', error);
      setMessage({ type: 'error', text: 'Failed to load rule sets' });
      setLoading(false);
    }
  };

  const loadActiveRuleSet = async () => {
    try {
      const active = await rulesetsAPI.getActiveRuleSet();
      setActiveRuleset(active);
    } catch (error) {
      console.error('Failed to load active rule set:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    try {
      if (editingId) {
        await rulesetsAPI.updateRuleSet(editingId, {
          ...formData,
          technical_rules_file: formData.technical_rules_file || undefined,
          medical_rules_file: formData.medical_rules_file || undefined,
        });
        setMessage({ type: 'success', text: 'Rule set updated successfully!' });
      } else {
        await rulesetsAPI.createRuleSet({
          name: formData.name,
          description: formData.description,
          is_active: formData.is_active,
          paid_amount_threshold: formData.paid_amount_threshold,
        });
        setMessage({ type: 'success', text: 'Rule set created successfully!' });
      }

      resetForm();
      loadRuleSets();
      loadActiveRuleSet();
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || error.message || 'Failed to save rule set' 
      });
    }
  };

  const handleSetActive = async (id: number) => {
    try {
      await rulesetsAPI.setActiveRuleSet(id);
      setMessage({ type: 'success', text: 'Active rule set updated!' });
      loadRuleSets();
      loadActiveRuleSet();
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || error.message || 'Failed to set active rule set' 
      });
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this rule set?')) {
      return;
    }

    try {
      await rulesetsAPI.deleteRuleSet(id);
      setMessage({ type: 'success', text: 'Rule set deleted successfully!' });
      loadRuleSets();
      loadActiveRuleSet();
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || error.message || 'Failed to delete rule set' 
      });
    }
  };

  const handleEdit = (ruleset: RuleSet) => {
    setEditingId(ruleset.id);
    setFormData({
      name: ruleset.name,
      description: ruleset.description || '',
      is_active: ruleset.is_active,
      paid_amount_threshold: ruleset.paid_amount_threshold,
      technical_rules_file: null,
      medical_rules_file: null,
    });
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      is_active: false,
      paid_amount_threshold: 250.00,
      technical_rules_file: null,
      medical_rules_file: null,
    });
    setEditingId(null);
    setShowForm(false);
  };

  if (loading) {
    return <div className="loading">Loading rule sets...</div>;
  }

  return (
    <div className="ruleset-manager">
      <div className="ruleset-header">
        <h2>📋 Rule Set Configuration</h2>
        <div className="ruleset-header-actions">
          {!showForm && (
            <button className="btn-primary" onClick={() => setShowForm(true)}>
              ➕ Create Rule Set
            </button>
          )}
          {onClose && (
            <button className="btn-secondary" onClick={onClose}>
              ✕ Close
            </button>
          )}
        </div>
      </div>

      {message && (
        <div className={`alert-message ${message.type === 'success' ? 'success' : 'error'}`}>
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)}>✕</button>
        </div>
      )}

      {activeRuleset && (
        <div className="active-ruleset-banner">
          <span className="active-badge">ACTIVE</span>
          <span className="active-name">{activeRuleset.name}</span>
          <span className="active-threshold">Threshold: AED {activeRuleset.paid_amount_threshold.toFixed(2)}</span>
        </div>
      )}

      {showForm && (
        <div className="ruleset-form">
          <h3>{editingId ? 'Edit' : 'Create'} Rule Set</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                placeholder="e.g., Default Rules, Tenant A Rules"
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional description for this rule set"
                rows={3}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Paid Amount Threshold (AED) *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.paid_amount_threshold}
                  onChange={(e) => setFormData({ ...formData, paid_amount_threshold: parseFloat(e.target.value) || 250.00 })}
                  required
                />
                <small>Claims exceeding this amount require prior approval</small>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  Set as Active Rule Set
                </label>
                <small>Only one rule set can be active at a time</small>
              </div>
            </div>

            {editingId && (
              <>
                <div className="form-group">
                  <label>Technical Rules File (PDF)</label>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setFormData({ ...formData, technical_rules_file: e.target.files?.[0] || null })}
                  />
                  <small>Upload new technical rules file to replace existing</small>
                </div>

                <div className="form-group">
                  <label>Medical Rules File (PDF)</label>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setFormData({ ...formData, medical_rules_file: e.target.files?.[0] || null })}
                  />
                  <small>Upload new medical rules file to replace existing</small>
                </div>
              </>
            )}

            <div className="form-actions">
              <button type="submit" className="btn-primary">
                {editingId ? '💾 Update' : '✅ Create'}
              </button>
              <button type="button" className="btn-secondary" onClick={resetForm}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="rulesets-list">
        <h3>Rule Sets</h3>
        {rulesets.length === 0 ? (
          <div className="no-data">
            <p>No rule sets found. Create one to get started.</p>
          </div>
        ) : (
          <table className="rulesets-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Threshold (AED)</th>
                <th>Status</th>
                <th>Files</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rulesets.map((ruleset) => (
                <tr key={ruleset.id} className={ruleset.is_active ? 'active-row' : ''}>
                  <td><strong>{ruleset.name}</strong></td>
                  <td>{ruleset.description || '-'}</td>
                  <td>{ruleset.paid_amount_threshold.toFixed(2)}</td>
                  <td>
                    {ruleset.is_active ? (
                      <span className="badge-active">● Active</span>
                    ) : (
                      <button
                        className="btn-set-active"
                        onClick={() => handleSetActive(ruleset.id)}
                        title="Set as active rule set"
                      >
                        Set Active
                      </button>
                    )}
                  </td>
                  <td>
                    <div className="file-indicators">
                      {ruleset.technical_rules_file_url && <span className="file-badge">📄 Tech</span>}
                      {ruleset.medical_rules_file_url && <span className="file-badge">📄 Med</span>}
                      {!ruleset.technical_rules_file_url && !ruleset.medical_rules_file_url && <span>-</span>}
                    </div>
                  </td>
                  <td>
                    <div className="table-actions">
                      <button
                        className="btn-edit"
                        onClick={() => handleEdit(ruleset)}
                        title="Edit rule set"
                      >
                        ✏️
                      </button>
                      <button
                        className="btn-delete"
                        onClick={() => handleDelete(ruleset.id)}
                        title="Delete rule set"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default RuleSetManager;

