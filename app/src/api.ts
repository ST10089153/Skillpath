// Thin client for the SkillPath API. All decisions are made server-side by the engine.
// Set EXPO_PUBLIC_API_URL (e.g. http://192.168.1.10:8000) when running on a phone via Expo Go.
export const API_URL = (process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export type Competency = 'limited' | 'foundational' | 'moderate';

export interface NearestOccupation {
  occupation: string;
  similarity: number;
  skills_held: number;
  skills_total: number;
  skills_missing: string[];
  source: string;
}

export interface DetectedSkill {
  skill: string;
  score: number;
  evidence: string;
  method: 'exact' | 'semantic';
}

export interface PickedFile {
  uri: string;
  name: string;
  mimeType?: string;
  file?: File;
}

export interface Recommendation {
  recommended_skill: string;
  alternatives: string[];
  explanation: string;
  income_displayed: string;
  status: string;
  nearest_occupations: NearestOccupation[];
  unrecognised_skills: string[];
  arm: string;
}

export interface ModuleView {
  module_id: string;
  difficulty: number;
  minutes: number;
  done: boolean;
}

export interface Progress {
  status: string;
  skill: string;
  milestones: string[];
  modules: ModuleView[];
  modules_completed: number;
  total_modules: number;
  current_module: { module_id: string; index: number; difficulty: number; minutes: number } | null;
  difficulty: number | null;
  message: string;
  completed: boolean;
  next_milestone_message?: string;
}

export interface ModuleContent {
  title: string;
  description: string;
  resource_label: string;
  resource_url: string;
}

export interface SkillInfo {
  skill: string;
  label: string;
  category: string;
  how_to_show: string;
  demand_evidence: string;
  demand_source: string;
  description: string;
  esco_uri: string;
  esco_url: string;
  occupations: string[];
}

export interface ModuleLibrary {
  default: ModuleContent[];
  skills: Record<string, ModuleContent[]>;
}

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : `Request failed (${res.status})`;
    throw new Error(detail);
  }
  return data as T;
}

async function upload<T>(path: string, f: PickedFile): Promise<T> {
  const form = new FormData();
  if (f.file) form.append('file', f.file, f.name); // web
  else form.append('file', { uri: f.uri, name: f.name, type: f.mimeType || 'application/octet-stream' } as unknown as Blob);
  const res = await fetch(`${API_URL}${path}`, { method: 'POST', body: form });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : `Upload failed (${res.status})`);
  return data as T;
}

export const api = {
  extractCv: (f: PickedFile) => upload<{ skills: DetectedSkill[]; message: string }>('/cv/extract', f),
  createUser: () =>
    call<{ user_id: string; arm: string }>('POST', '/users', { consent: true, age_confirmed: true }),
  vocabulary: () =>
    call<{
      categories: { category: string; skills: string[] }[];
      labels: Record<string, string>;
      occupations: { occupation: string; skills: string[] }[];
      skills: string[];
    }>('GET', '/vocabulary'),
  modules: () => call<ModuleLibrary>('GET', '/modules'),
  skill: (skill: string) => call<SkillInfo>('GET', `/skills/${encodeURIComponent(skill)}`),
  myData: (id: string) => call<Record<string, unknown>>('GET', `/users/${id}`),
  saveProfile: (id: string, skills: string[], competency_level: Competency) =>
    call('POST', `/users/${id}/profile`, { skills, competency_level }),
  recommendation: (id: string) => call<Recommendation>('GET', `/users/${id}/recommendation`),
  accept: (id: string) => call<Progress>('POST', `/users/${id}/pathway/accept`),
  swap: (id: string, skill: string) => call<Progress>('POST', `/users/${id}/pathway/swap`, { skill }),
  defer: (id: string) => call<{ status: string; message: string }>('POST', `/users/${id}/pathway/defer`),
  result: (id: string, moduleId: string, passed: boolean) =>
    call<{ milestone: string; revised: boolean; message: string; progress: Progress }>(
      'POST', `/users/${id}/modules/${encodeURIComponent(moduleId)}/result`, { passed }),
  progress: (id: string) => call<Progress>('GET', `/users/${id}/progress`),
  nudge: (id: string) => call<{ nudge: boolean; days_inactive: number; message: string }>('GET', `/users/${id}/nudge`),
  event: (id: string, event_type: string, item_id = '') =>
    call('POST', `/users/${id}/events`, { event_type, item_id }).catch(() => undefined),
  deleteMe: (id: string) => call<{ deleted: boolean }>('DELETE', `/users/${id}`),
};

export function slugify(skill: string): string {
  return skill.toLowerCase().trim().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'skill';
}

export function moduleContent(lib: ModuleLibrary | null, skill: string, index: number, escoUrl = '', howToShow = ''): ModuleContent {
  const list = lib?.skills?.[slugify(skill)] ?? lib?.default ?? [];
  const item = list[index] ?? { title: `Module ${index + 1}`, description: '', resource_label: '', resource_url: '' };
  const fill = (s: string) => (s || '')
    .split('{skill}').join(skill)
    .split('{query}').join(encodeURIComponent(skill))
    .split('{esco_url}').join(escoUrl)
    .split('{how_to_show}').join(howToShow);
  const url = fill(item.resource_url);
  return { title: fill(item.title), description: fill(item.description),
           resource_label: item.resource_label || 'Open resource', resource_url: url };
}
