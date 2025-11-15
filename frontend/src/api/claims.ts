import api from './axios';

export interface Claim {
  id: number;
  claim_id: string;
  encounter_type: string;
  service_date: string;
  national_id: string;
  member_id: string;
  facility_id: string;
  unique_id: string;
  diagnosis_codes: string;
  service_code: string;
  paid_amount_aed: number;
  approval_number: string | null;
  status: 'validated' | 'not_validated';
  error_type: 'no_error' | 'medical_error' | 'technical_error' | 'both';
  error_explanation: string;
  recommended_action: string;
  created_at: string;
  updated_at: string;
}

export interface ValidationJob {
  id: number;
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  claims_file: string;
  technical_rules_file?: string;
  medical_rules_file?: string;
  total_claims: number;
  processed_claims: number;
  validated_count: number;
  error_count: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface Statistics {
  total_claims: number;
  validated: number;
  not_validated: number;
  error_type_counts: {
    no_error: number;
    medical_error: number;
    technical_error: number;
    both: number;
  };
  paid_amount_by_error: {
    no_error: number;
    medical_error: number;
    technical_error: number;
    both: number;
  };
}

export const claimsAPI = {
  getClaims: async (params?: any) => {
    const response = await api.get('/claims/', { params });
    return response.data;
  },
  
  getClaim: async (id: number) => {
    const response = await api.get(`/claims/${id}/`);
    return response.data;
  },
  
  getStatistics: async (): Promise<Statistics> => {
    const response = await api.get('/claims/statistics/');
    return response.data;
  },
  
  uploadFile: async (formData: FormData) => {
    const response = await api.post('/jobs/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  getJob: async (id: number) => {
    const response = await api.get(`/jobs/${id}/`);
    return response.data;
  },
  
  getJobStatus: async (id: number) => {
    const response = await api.get(`/jobs/${id}/status/`);
    return response.data;
  },
  
  getJobs: async () => {
    const response = await api.get('/jobs/');
    return response.data;
  },
};

