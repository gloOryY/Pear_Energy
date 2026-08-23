import { WS_URL } from './config';
import { useAuth } from '../stores/auth';

export function connectUserSocket(userId: string, onMessage: (msg: any) => void) {
  const token = useAuth.getState().accessToken ?? '';
  let ws: WebSocket | null = null;
  let closed = false;
  let attempt = 0;
  const open = () => {
    ws = new WebSocket(`${WS_URL}/ws/users/${userId}/sessions?token=${encodeURIComponent(token)}`);
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)); } catch {}
    };
    ws.onclose = () => {
      if (!closed) {
        attempt = Math.min(attempt + 1, 10);
        setTimeout(open, Math.min(attempt * 2000, 10000));
      }
    };
  };
  open();
  return () => { closed = true; ws?.close(); };
}

export function connectStationSocket(publicId: string, onMessage: (msg: any) => void) {
  let ws: WebSocket | null = null;
  let closed = false;
  const open = () => {
    ws = new WebSocket(`${WS_URL}/ws/stations/${publicId}`);
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)); } catch {}
    };
    ws.onclose = () => {
      if (!closed) setTimeout(open, 3000);
    };
  };
  open();
  return () => { closed = true; ws?.close(); };
}
