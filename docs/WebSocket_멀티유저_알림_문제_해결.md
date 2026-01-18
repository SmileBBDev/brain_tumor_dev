# WebSocket 멀티유저 알림 문제 해결

## 문제 상황

RIS 방사선사가 OCS를 접수할 때 다른 방사선사에게 Toast 알림이 가고 화면이 리프레시되어야 하는데, 어떤 경우는 되고 어떤 경우는 발생하지 않음.

### 테스트 환경
- ris1, ris2 두 계정으로 테스트
- 서로 다른 브라우저에서 접속해도 동일 문제 발생

## 원인 분석

### 1. 토큰 변경 감지 미비 (같은 브라우저에서 다른 계정 로그인 시)

**문제**: 싱글톤 WebSocket이 이전 사용자의 토큰으로 연결된 상태를 유지

```typescript
// 기존 코드 - 토큰 변경 감지 없음
function initGlobalSocket(): void {
  if (globalSocket && globalSocket.readyState === WebSocket.OPEN) {
    return; // 이미 연결됨 - 토큰이 달라도 재사용
  }
  // ...
}
```

### 2. 연결 끊김 시 토큰 리셋 누락

**문제**: WebSocket 연결이 끊어져도 `currentConnectedToken`이 리셋되지 않아 재연결 시 문제 발생

### 3. WebSocket 상태 체크 불완전

**문제**: `CLOSING` 상태를 체크하지 않아 닫히는 중인 소켓을 재사용 시도

```typescript
// 기존 코드
if (!globalSocket || globalSocket.readyState === WebSocket.CLOSED) {
  // CLOSING 상태는 체크하지 않음
}
```

### 4. 로그아웃 시 OCS WebSocket 미종료

**문제**: 로그아웃 시 OCS WebSocket을 명시적으로 종료하지 않아 다음 로그인 시 이전 연결 재사용

## 해결 방법

### 1. `ocsSocket.ts` - 토큰 변경 감지 및 재연결

```typescript
// 현재 연결된 토큰 추적
let currentConnectedToken: string | null = null;

function initGlobalSocket(): void {
  const token = localStorage.getItem('accessToken');
  if (!token) {
    console.warn('OCS WebSocket: No access token');
    return;
  }

  // 토큰이 변경되었으면 기존 연결 종료 후 재연결 (다른 사용자로 로그인한 경우)
  if (globalSocket && currentConnectedToken && currentConnectedToken !== token) {
    console.log('🔄 [ocsSocket] 토큰 변경 감지, 기존 연결 종료 후 재연결...');
    if (globalSocket.readyState === WebSocket.OPEN || globalSocket.readyState === WebSocket.CONNECTING) {
      globalSocket.close();
    }
    globalSocket = null;
    currentConnectedToken = null;
  }

  if (globalSocket && globalSocket.readyState === WebSocket.OPEN) {
    return; // 이미 동일 토큰으로 연결됨
  }

  const wsBaseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  const wsUrl = `${wsBaseUrl}/ocs/?token=${token}`;
  currentConnectedToken = token;
  console.log('🔌 [ocsSocket] 새 WebSocket 연결 생성');
  globalSocket = new WebSocket(wsUrl);
  // ...
}
```

### 2. `ocsSocket.ts` - onclose에서 토큰 리셋

```typescript
globalSocket.onclose = (event) => {
  console.log('OCS WebSocket disconnected (global), code:', event.code, 'reason:', event.reason);
  listeners.forEach(({ callbacks }) => callbacks.onClose?.());

  if (pingInterval) {
    clearInterval(pingInterval);
    pingInterval = null;
  }

  globalSocket = null;
  // 연결 끊김 시 토큰도 리셋 (재연결 시 새 토큰으로 연결하도록)
  currentConnectedToken = null;

  // 자동 재연결 로직...
};
```

### 3. `ocsSocket.ts` - CLOSING 상태 체크 추가

```typescript
export function subscribeOCSSocket(callbacks: OCSSocketCallbacks): string {
  // ...

  // 연결이 없거나 닫혔으면 새로 연결
  if (!globalSocket || globalSocket.readyState === WebSocket.CLOSED || globalSocket.readyState === WebSocket.CLOSING) {
    console.log('🔌 [ocsSocket] WebSocket 연결 시작...');
    initGlobalSocket();
  } else if (globalSocket.readyState === WebSocket.CONNECTING) {
    console.log('🔌 [ocsSocket] WebSocket 연결 중... 대기');
  } else {
    console.log('🔌 [ocsSocket] WebSocket 이미 연결됨');
  }

  return listenerId;
}
```

### 4. `ocsSocket.ts` - closeGlobalSocket 개선

```typescript
export function closeGlobalSocket(): void {
  console.log('🔌 [ocsSocket] 전역 소켓 종료');
  if (pingInterval) {
    clearInterval(pingInterval);
    pingInterval = null;
  }

  if (globalSocket) {
    globalSocket.close();
    globalSocket = null;
  }

  currentConnectedToken = null;
  connectionAttempts = 0;
  listeners.length = 0;
}
```

### 5. `OCSNotificationContext.tsx` - 사용자 변경 시 재구독

```typescript
useEffect(() => {
  if (!isAuthenticated || !user) {
    // 로그아웃 시 기존 구독 해제
    if (listenerIdRef.current) {
      unsubscribeOCSSocket(listenerIdRef.current);
      listenerIdRef.current = null;
    }
    return;
  }

  // 이미 구독 중이면 먼저 해제 (사용자 변경 대응)
  if (listenerIdRef.current) {
    console.log('🔌 [OCSNotificationProvider] 기존 구독 해제 후 재연결');
    unsubscribeOCSSocket(listenerIdRef.current);
    listenerIdRef.current = null;
  }

  // 싱글톤 WebSocket에 전역 구독 등록
  listenerIdRef.current = subscribeOCSSocket({
    // callbacks...
  });

  return () => {
    if (listenerIdRef.current) {
      unsubscribeOCSSocket(listenerIdRef.current);
      listenerIdRef.current = null;
    }
  };
}, [isAuthenticated, user, addNotification]);
```

### 6. `AuthProvider.tsx` - 로그아웃 시 OCS WebSocket 종료

```typescript
import { closeGlobalSocket as closeOCSSocket } from '@/socket/ocsSocket';

const logout = async () => {
  setUser(null);
  setRole(null);
  setMenus([]);
  // ...

  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');

  // Permission WebSocket 닫기
  if (wsRef.current) {
    wsRef.current.close();
  }

  // OCS WebSocket 닫기 (사용자 변경 시 재연결을 위해)
  closeOCSSocket();
};
```

## 아키텍처 설명

### WebSocket 연결 흐름

```
사용자 로그인
    ↓
AuthProvider → OCSNotificationProvider useEffect 실행
    ↓
subscribeOCSSocket() 호출
    ↓
initGlobalSocket() → 토큰으로 WebSocket 연결
    ↓
Django OCSConsumer.connect()
    ↓
역할에 따라 그룹 구독 (ocs_ris, ocs_lis, ocs_doctor_{id})
    ↓
Redis Channel Layer에 그룹 멤버 등록
```

### OCS 상태 변경 시 알림 흐름

```
RIS 방사선사 A가 OCS 접수
    ↓
POST /api/ocs/{id}/accept/
    ↓
OCSViewSet.accept() → notify_ocs_status_changed() 호출
    ↓
channel_layer.group_send('ocs_ris', event_data)
    ↓
Redis가 'ocs_ris' 그룹의 모든 채널에 브로드캐스트
    ↓
모든 RIS 작업자의 OCSConsumer.ocs_status_changed() 호출
    ↓
각 클라이언트의 WebSocket.onmessage 이벤트
    ↓
listeners의 모든 콜백 실행 → Toast 알림 + 목록 새로고침
```

## 디버깅 방법

### 1. 프론트엔드 Console 확인

브라우저 개발자 도구(F12) > Console에서 다음 로그 확인:

```
🔌 [ocsSocket] 리스너 등록: listener-xxx
🔌 [ocsSocket] WebSocket 연결 시작...
🔌 [ocsSocket] 새 WebSocket 연결 생성
OCS WebSocket connected (global)
```

### 2. 백엔드 로그 확인

```bash
docker logs nn-django --tail 100
```

다음 로그가 모든 RIS 사용자에게 나타나야 함:
```
🔌 OCS WebSocket connected: user=ris1, groups=['ocs_ris']
🔌 OCS WebSocket connected: user=ris2, groups=['ocs_ris']
```

### 3. 알림 발송 로그 확인

OCS 접수 시:
```
📤 [OCS 알림] group=ocs_ris, type=ocs_status_changed, msg=xxx님의 MRI 오더가 접수되었습니다....
```

## 관련 파일

| 파일 | 역할 |
|------|------|
| `brain_tumor_front/src/socket/ocsSocket.ts` | OCS WebSocket 클라이언트 (싱글톤) |
| `brain_tumor_front/src/context/OCSNotificationContext.tsx` | OCS 알림 전역 Context |
| `brain_tumor_front/src/pages/auth/AuthProvider.tsx` | 인증 및 로그아웃 처리 |
| `brain_tumor_back/apps/ocs/consumers.py` | Django Channels OCS Consumer |
| `brain_tumor_back/apps/ocs/notifications.py` | OCS 알림 발송 서비스 |
| `brain_tumor_back/apps/ocs/views.py` | OCS API (accept 등 액션) |

## 주의사항

1. **Redis 필수**: WebSocket 그룹 브로드캐스트는 Redis Channel Layer를 통해 동작. Redis가 실행 중이어야 함.

2. **토큰 갱신**: JWT 토큰 만료 시 WebSocket도 재연결 필요. 현재는 연결 끊김 시 자동 재연결 (최대 5회).

3. **서로 다른 브라우저**: localStorage가 분리되어 토큰 충돌 없음. 문제 발생 시 백엔드 연결 자체가 안 되는 것일 수 있음.
