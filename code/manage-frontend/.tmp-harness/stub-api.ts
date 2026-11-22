const files = import.meta.glob('./*.json', { eager: true }) as Record<string, any>
const f = new URLSearchParams(location.search).get('f') || 'profile'
export const studentApi = { getProfile: async () => (files[`./${f}.json`].default ?? files[`./${f}.json`]).data, handleWarning: async () => null }
