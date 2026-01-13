# WebSocket 이벤트 난제 해결 정리

## 문제 상황 목록

### 1. Toast 무한 반복 문제
- WebSocket 메시지 수신 시 Toast가 무한 생성됨
- 원인: useEffect 의존성 배열 문제로 리렌더링 루프 발생

### 2. 중복 알림 문제
- 같은 이벤트에 대해 여러 번 알림이 발생
- 원인: 페이지 이동 시 WebSocket 리스너가 중복 등록됨
- 각 컴포넌트마다 별도 WebSocket 연결 생성

### 3. OCS 생성 시 RIS/LIS에서 알림/새로고침 안됨
- OCS 생성 후 WebSocket 메시지는 수신되나 화면 갱신이 안됨
- Toast는 나오는데 목록이 갱신 안됨

### 4. 작업 접수 후 작업자 ID 미등록
- 상태는 '접수완료'로 변경되나 worker_id가 저장 안됨
- 미배정 필터에 여전히 노출됨

### 5. 새로고침 호출 시 데이터 변화 없음
- refresh() 호출되나 DB 트랜잭션 완료 전에 조회하여 이전 데이터 반환

---

## 해결 방안

### 1. Toast 무한 반복 → 싱글톤 WebSocket 패턴

**Before (각 컴포넌트마다 연결)**
```typescript
useEffect(() => {
  const socket = connectOCSSocket({
    onCreated: (event) => {
      toast.success('새 OCS가 생성되었습니다');
    }
  });
  return () => socket?.close();
}, []);
```

**After (전역 싱글톤 + 구독 패턴)**
```typescript
// ocsSocket.ts - 싱글톤 관리
let globalSocket: WebSocket | null = null;
const listeners: Array<{ id: string; callbacks: OCSSocketCallbacks }> = [];

export function subscribeOCSSocket(callbacks: OCSSocketCallbacks): string {
  const listenerId = `listener-${Date.now()}-${Math.random()}`;
  listeners.push({ id: listenerId, callbacks });

  if (!globalSocket || globalSocket.readyState === WebSocket.CLOSED) {
    initGlobalSocket();
  }
  return listenerId;
}

export function unsubscribeOCSSocket(listenerId: string) {
  const index = listeners.findIndex(l => l.id === listenerId);
  if (index !== -1) listeners.splice(index, 1);
}
```

### 2. 중복 알림 → 전역 Context로 일원화

**OCSNotificationContext.tsx**
```typescript
export function OCSNotificationProvider({ children }: Props) {
  const listenerIdRef = useRef<string | null>(null);

  useEffect(() => {
    // 한 번만 구독
    listenerIdRef.current = subscribeOCSSocket({
      onCreated: (event) => showToast(event),
      onStatusChanged: (event) => showToast(event),
    });

    return () => {
      if (listenerIdRef.current) {
        unsubscribeOCSSocket(listenerIdRef.current);
      }
    };
  }, []);

  return <Context.Provider value={...}>{children}</Context.Provider>;
}
```

### 3. 새로고침 안됨 → onSuccess 콜백 추가

```typescript
const { accept, start } = useOCSActions({
  onSuccess: () => {
    refresh();
  },
});
```

### 4. DB 타이밍 문제 → 300ms 딜레이

```typescript
// Before
onSuccess: () => {
  refresh();
}

// After
onSuccess: () => {
  setTimeout(() => refresh(), 300);
}
```

---

## 수정된 파일 목록

| 파일 | 수정 내용 |
|------|-----------|
| `ocsSocket.ts` | 싱글톤 패턴, subscribe/unsubscribe 함수 추가 |
| `OCSNotificationContext.tsx` | 전역 알림 관리, useOCSEventCallback 훅 제공 |
| `useOCSActions.ts` | onSuccess, onError 콜백에 serverMessage 추가 |
| `LISWorklistPage.tsx` | onSuccess, onError, autoRefresh에 딜레이 추가 |
| `RISWorklistPage.tsx` | onSuccess, onError, autoRefresh에 딜레이 추가 |
| `OCSManagePage.tsx` | useOCSEventCallback 추가, 딜레이 추가 |
| `DoctorOrderPage.tsx` | useOCSEventCallback 추가, 딜레이 추가 |
| `LISProcessStatusPage.tsx` | autoRefresh에 딜레이 추가 |
| `OCSProcessStatusPage.tsx` | autoRefresh에 딜레이 추가 |

---

## 아키텍처 변경

### Before
```
[LISWorklistPage] ──→ [WebSocket 연결 1]
[RISWorklistPage] ──→ [WebSocket 연결 2]
[DoctorOrderPage] ──→ [WebSocket 연결 3]
         ↓
   중복 알림 발생!
```

### After
```
[AppLayout]
    └── [OCSNotificationProvider] ──→ [싱글톤 WebSocket]
            │
            ├── [LISWorklistPage] ──→ useOCSEventCallback(autoRefresh)
            ├── [RISWorklistPage] ──→ useOCSEventCallback(autoRefresh)
            └── [DoctorOrderPage] ──→ useOCSEventCallback(autoRefresh)
```

---

## 알림 규칙 (Backend → Frontend)

| 역할 | 수신하는 알림 |
|------|---------------|
| SYSTEMMANAGER, ADMIN | 모든 OCS 알림 |
| DOCTOR | 자신이 생성한 OCS 알림만 |
| RIS | job_role이 'RIS'인 OCS 알림만 |
| LIS | job_role이 'LIS'인 OCS 알림만 |

**Backend WebSocket 그룹**
```python
# consumers.py
async def connect(self):
    user = self.scope['user']

    if user.role in ['SYSTEMMANAGER', 'ADMIN']:
        await self.channel_layer.group_add('ocs_all', self.channel_name)
    elif user.role == 'DOCTOR':
        await self.channel_layer.group_add(f'ocs_doctor_{user.id}', self.channel_name)
    elif user.role == 'RIS':
        await self.channel_layer.group_add('ocs_ris', self.channel_name)
    elif user.role == 'LIS':
        await self.channel_layer.group_add('ocs_lis', self.channel_name)
```

---

## 디버그 로그 위치

### Frontend
```typescript
// ocsSocket.ts
console.log('🔌 [ocsSocket] 리스너 등록:', listenerId);
console.log('📨 [ocsSocket] 메시지 수신:', event.type);
console.log('📨 [ocsSocket] 리스너에게 전달:', id, event.type);
```

### Backend
```python
# views.py
print(f"[OCS] accept 저장 전: ocs_id={ocs.ocs_id}, worker_id={ocs.worker_id}")
print(f"[OCS] accept 저장 후: ocs_id={ocs.ocs_id}, worker_id={ocs.worker_id}")
```

---

## 핵심 교훈

1. **WebSocket은 싱글톤으로 관리** - 컴포넌트마다 연결하면 중복 문제 발생
2. **알림은 전역 Context에서 일원화** - 각 페이지에서 Toast 띄우면 중복
3. **DB 트랜잭션 타이밍 고려** - API 응답 후 바로 조회하면 이전 데이터 올 수 있음
4. **useEffect 의존성 주의** - 잘못된 의존성은 무한 루프 유발
