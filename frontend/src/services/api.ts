import axios, { AxiosError } from 'axios';
import {
  User,
  LoginCredentials,
  AuthTokens,
  Stage,
  Etudiant,
  Service,
  Etablissement,
  Document,
  Presence,
  StatistiquesAnnuelles,
  StatutStage,
  RapportService,
  RapportPrevisionnel,
  StageAccepte,
  StageRefuse,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh', null, {
            params: { refresh_token: refreshToken },
          });
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          if (error.config) {
            error.config.headers.Authorization = `Bearer ${access_token}`;
            return axios.request(error.config);
          }
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } else {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },
};

export const etudiantsApi = {
  list: async (params?: {
    search?: string;
    etablissement_id?: number;
    formation?: string;
    page?: number;
    page_size?: number;
  }): Promise<Etudiant[]> => {
    const response = await api.get('/etudiants', { params });
    return response.data;
  },

  get: async (id: number): Promise<Etudiant> => {
    const response = await api.get(`/etudiants/${id}`);
    return response.data;
  },

  getByCode: async (code: string): Promise<Etudiant> => {
    const response = await api.get(`/etudiants/code/${code}`);
    return response.data;
  },

  create: async (data: Partial<Etudiant>): Promise<Etudiant> => {
    const response = await api.post('/etudiants', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Etudiant>): Promise<Etudiant> => {
    const response = await api.patch(`/etudiants/${id}`, data);
    return response.data;
  },

  delete: async (id: number, motif: string): Promise<void> => {
    await api.delete(`/etudiants/${id}`, { params: { motif } });
  },
};

export const stagesApi = {
  list: async (params?: {
    search?: string;
    service_id?: number;
    etablissement_id?: number;
    statut?: StatutStage;
    date_debut?: string;
    date_fin?: string;
    annee?: number;
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }): Promise<Stage[]> => {
    const response = await api.get('/stages', { params });
    return response.data;
  },

  get: async (id: number): Promise<Stage> => {
    const response = await api.get(`/stages/${id}`);
    return response.data;
  },

  create: async (data: Partial<Stage>): Promise<Stage> => {
    const response = await api.post('/stages', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Stage>): Promise<Stage> => {
    const response = await api.patch(`/stages/${id}`, data);
    return response.data;
  },

  delete: async (id: number, motif: string): Promise<void> => {
    await api.delete(`/stages/${id}`, { params: { motif } });
  },

  getCalendrier: async (serviceId: number, params?: { mois?: number; annee?: number }) => {
    const response = await api.get(`/stages/calendrier/service/${serviceId}`, { params });
    return response.data;
  },
};

export const servicesApi = {
  list: async (actif_only = true): Promise<Service[]> => {
    const response = await api.get('/services', { params: { actif_only } });
    return response.data;
  },

  get: async (id: number): Promise<Service> => {
    const response = await api.get(`/services/${id}`);
    return response.data;
  },

  create: async (data: Partial<Service>): Promise<Service> => {
    const response = await api.post('/services', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Service>): Promise<Service> => {
    const response = await api.patch(`/services/${id}`, data);
    return response.data;
  },
};

export const etablissementsApi = {
  list: async (actif_only = true): Promise<Etablissement[]> => {
    const response = await api.get('/etablissements', { params: { actif_only } });
    return response.data;
  },

  get: async (id: number): Promise<Etablissement> => {
    const response = await api.get(`/etablissements/${id}`);
    return response.data;
  },

  create: async (data: Partial<Etablissement>): Promise<Etablissement> => {
    const response = await api.post('/etablissements', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Etablissement>): Promise<Etablissement> => {
    const response = await api.patch(`/etablissements/${id}`, data);
    return response.data;
  },
};

export const documentsApi = {
  listByStage: async (stageId: number): Promise<Document[]> => {
    const response = await api.get(`/documents/stage/${stageId}`);
    return response.data;
  },

  upload: async (stageId: number, typeDocument: string, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('stage_id', stageId.toString());
    formData.append('type_document', typeDocument);
    formData.append('file', file);

    const response = await api.post('/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  download: async (documentId: number): Promise<Blob> => {
    const response = await api.get(`/documents/${documentId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  validate: async (documentId: number, valide: boolean): Promise<Document> => {
    const response = await api.patch(`/documents/${documentId}/validate`, null, {
      params: { valide },
    });
    return response.data;
  },

  delete: async (documentId: number): Promise<void> => {
    await api.delete(`/documents/${documentId}`);
  },
};

export const presencesApi = {
  listByStage: async (
    stageId: number,
    params?: { date_debut?: string; date_fin?: string }
  ): Promise<Presence[]> => {
    const response = await api.get(`/presences/stage/${stageId}`, { params });
    return response.data;
  },

  create: async (data: Partial<Presence>): Promise<Presence> => {
    const response = await api.post('/presences', data);
    return response.data;
  },

  bulkUpdate: async (presences: Partial<Presence>[]): Promise<Presence[]> => {
    const response = await api.post('/presences/bulk', { presences });
    return response.data;
  },

  update: async (id: number, data: Partial<Presence>): Promise<Presence> => {
    const response = await api.patch(`/presences/${id}`, data);
    return response.data;
  },
};

export const rapportsApi = {
  getStatistiquesAnnuelles: async (annee: number): Promise<StatistiquesAnnuelles> => {
    const response = await api.get('/rapports/statistiques-annuelles', { params: { annee } });
    return response.data;
  },

  exportCSV: async (params?: {
    annee?: number;
    service_id?: number;
    statut?: StatutStage;
  }): Promise<Blob> => {
    const response = await api.get('/rapports/export-csv', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },

  getStagesAcceptes: async (annee?: number): Promise<StageAccepte[]> => {
    const response = await api.get('/rapports/stages-acceptes', { params: { annee } });
    return response.data;
  },

  getStagesRefuses: async (annee?: number): Promise<StageRefuse[]> => {
    const response = await api.get('/rapports/stages-refuses', { params: { annee } });
    return response.data;
  },

  getRapportServices: async (annee: number): Promise<RapportService[]> => {
    const response = await api.get('/rapports/rapport-services', { params: { annee } });
    return response.data;
  },

  getRapportPrevisionnel: async (annee: number): Promise<RapportPrevisionnel[]> => {
    const response = await api.get('/rapports/rapport-previsionnel', { params: { annee } });
    return response.data;
  },
};

export default api;
