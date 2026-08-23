declare global {
  interface Window {
    ymaps?: any;
  }
}

let loadingPromise: Promise<any> | null = null;

export function loadYmaps(apiKey: string): Promise<any> {
  if (typeof window === 'undefined') return Promise.reject(new Error('SSR'));
  if (window.ymaps) return Promise.resolve(window.ymaps);
  if (loadingPromise) return loadingPromise;
  loadingPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    const keyParam = apiKey ? `&apikey=${apiKey}` : '';
    script.src = `https://api-maps.yandex.ru/2.1/?lang=ru_RU${keyParam}`;
    script.onload = () => { (window.ymaps as any).ready(() => resolve(window.ymaps)); };
    script.onerror = reject;
    document.head.appendChild(script);
  });
  return loadingPromise;
}

export const STATUS_COLOR: Record<string, string> = {
  available: '#22c55e',
  charging: '#17c99e',
  preparing: '#17c99e',
  vehicle_connected: '#f59e0b',
  awaiting_payment: '#f59e0b',
  suspended_ev: '#f59e0b',
  finishing: '#17c99e',
  offline: '#71717a',
  unavailable: '#71717a',
  faulted: '#ef4444',
  emergency_stop: '#ef4444',
};
