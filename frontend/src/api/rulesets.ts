import api from './axios';

export interface RuleSet {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  technical_rules_file?: string | null;
  medical_rules_file?: string | null;
  technical_rules_file_url?: string | null;
  medical_rules_file_url?: string | null;
  paid_amount_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface CreateRuleSetData {
  name: string;
  description?: string;
  is_active?: boolean;
  paid_amount_threshold?: number;
}

export interface UpdateRuleSetData extends Partial<CreateRuleSetData> {
  technical_rules_file?: File;
  medical_rules_file?: File;
}

export const rulesetsAPI = {
  getRuleSets: async () => {
    const response = await api.get('/rulesets/');
    return response.data;
  },

  getRuleSet: async (id: number) => {
    const response = await api.get(`/rulesets/${id}/`);
    return response.data;
  },

  getActiveRuleSet: async (): Promise<RuleSet | null> => {
    try {
      const response = await api.get('/rulesets/active/');
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  createRuleSet: async (data: CreateRuleSetData) => {
    const response = await api.post('/rulesets/', data);
    return response.data;
  },

  updateRuleSet: async (id: number, data: UpdateRuleSetData) => {
    const formData = new FormData();
    
    if (data.name !== undefined) formData.append('name', data.name);
    if (data.description !== undefined) formData.append('description', data.description || '');
    if (data.is_active !== undefined) formData.append('is_active', data.is_active.toString());
    if (data.paid_amount_threshold !== undefined) {
      formData.append('paid_amount_threshold', data.paid_amount_threshold.toString());
    }
    if (data.technical_rules_file) {
      formData.append('technical_rules_file', data.technical_rules_file);
    }
    if (data.medical_rules_file) {
      formData.append('medical_rules_file', data.medical_rules_file);
    }

    const response = await api.patch(`/rulesets/${id}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  deleteRuleSet: async (id: number) => {
    const response = await api.delete(`/rulesets/${id}/`);
    return response.data;
  },

  setActiveRuleSet: async (id: number) => {
    const response = await api.post(`/rulesets/${id}/set_active/`);
    return response.data;
  },
};

