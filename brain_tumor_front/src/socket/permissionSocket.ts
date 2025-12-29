// WebSocket 연결
export function connectPermissionSocket(onChanged: () => void) {
  const ws = new WebSocket('ws://localhost:8000/ws/permissions/');

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'PERMISSION_CHANGED') {
      onChanged();
    }
  };

  return ws;
}
