type ApiEnv = {
  DEV?: boolean;
  PROD?: boolean;
  VITE_API_URL?: string;
};

type RuntimeConfig = {
  VITE_API_URL?: string;
};

function normalizeApiUrl(value?: string): string | undefined {
  const configuredUrl = value?.trim();

  if (configuredUrl) {
    return configuredUrl.replace(/\/$/, '');
  }

  return undefined;
}

export function resolveApiUrl(env: ApiEnv, runtimeConfig?: RuntimeConfig): string {
  const runtimeUrl = normalizeApiUrl(runtimeConfig?.VITE_API_URL);

  if (runtimeUrl) {
    return runtimeUrl;
  }

  const buildTimeUrl = normalizeApiUrl(env.VITE_API_URL);

  if (buildTimeUrl) {
    return buildTimeUrl;
  }

  if (env.DEV) {
    return 'http://localhost:8000';
  }

  throw new Error(
    'VITE_API_URL is required in production. Set it as a container runtime env var or a Vite build env var.',
  );
}

export const API_URL = resolveApiUrl(import.meta.env, window.__APP_CONFIG__);
