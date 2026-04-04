import { describe, expect, it } from 'vitest';

import { resolveApiUrl } from '@/config/api';

describe('resolveApiUrl', () => {
  it('prefers the runtime config when present', () => {
    expect(
      resolveApiUrl(
        {
          PROD: true,
          VITE_API_URL: 'https://build.example.com',
        },
        {
          VITE_API_URL: 'https://runtime.example.com/',
        },
      ),
    ).toBe('https://runtime.example.com');
  });

  it('uses the configured VITE_API_URL when present', () => {
    expect(
      resolveApiUrl({
        PROD: true,
        VITE_API_URL: 'https://api.example.com/',
      }),
    ).toBe('https://api.example.com');
  });

  it('falls back to localhost during development', () => {
    expect(
      resolveApiUrl({
        DEV: true,
      }),
    ).toBe('http://localhost:8000');
  });

  it('throws when VITE_API_URL is missing in production', () => {
    expect(() =>
      resolveApiUrl({
        PROD: true,
      }),
    ).toThrow(/VITE_API_URL is required/);
  });
});
