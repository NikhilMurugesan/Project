// Thin axios wrapper. Vite proxies /api/* to the FastAPI server (see
// vite.config.ts) so this works the same in dev and in a built bundle.
import axios from 'axios';
import type {
  AllocationResult,
  CompareResult,
  Scenario,
  Weights,
} from '../types';

const http = axios.create({ baseURL: '/api' });

export async function listScenarios(): Promise<{ id: number; name: string }[]> {
  const { data } = await http.get('/scenarios');
  return data;
}

export async function getScenario(id: number): Promise<Scenario> {
  const { data } = await http.get(`/scenarios/${id}`);
  return data;
}

export async function createScenario(
  size: 'small' | 'medium' | 'large',
  seed = 42,
  name?: string
): Promise<Scenario> {
  const { data } = await http.post('/scenarios', { size, seed, name });
  return data;
}

export async function deleteScenario(id: number): Promise<void> {
  await http.delete(`/scenarios/${id}`);
}

export async function allocate(
  id: number,
  algorithm: 'greedy' | 'hungarian',
  weights: Weights
): Promise<AllocationResult> {
  const { data } = await http.post(`/scenarios/${id}/allocate`, {
    algorithm,
    weights,
  });
  return data;
}

export async function compare(
  id: number,
  weights: Weights
): Promise<CompareResult> {
  const { data } = await http.post(`/scenarios/${id}/compare`, {
    algorithm: 'greedy',
    weights,
  });
  return data;
}
