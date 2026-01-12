# RolePermission 모델 구조 변경 작업 내역

## 작업 일시
2026-01-12

## 변경 배경
다른 개발자가 `RolePermission` 모델의 구조를 변경하여, 기존 코드와의 호환성 문제 및 테이블 충돌 문제가 발생함.

### 변경 전 구조
```python
# Role 모델
class Role(models.Model):
    permissions = models.ManyToManyField("accounts.Permission", ...)
    # Django가 자동으로 accounts_role_permissions 테이블 생성

# RolePermission 모델 (DEPRECATED)
class RolePermission(models.Model):
    role = ForeignKey(Role)
    permission = ForeignKey(Permission)  # Permission 참조
    managed = False  # Django가 관리하지 않음
```

### 변경 후 구조
```python
# Role 모델
class Role(models.Model):
    # permissions M2M 필드 제거됨
    # Role-Menu 권한 매핑은 RolePermission 모델을 통해 관리

# RolePermission 모델 (실제 사용)
class RolePermission(models.Model):
    role = ForeignKey(Role)
    permission = ForeignKey(Menu)  # Menu 참조 (변경됨!)

    class Meta:
        db_table = "accounts_role_permissions"
        managed = True
```

## 발생한 문제들

### 1. 테이블명 충돌
```
accounts.Role.permissions: (fields.E340) The field's intermediary table
'accounts_role_permissions' clashes with the table name of 'accounts.RolePermission'.
```
- `Role.permissions` M2M과 `RolePermission` 모델이 같은 테이블명 사용

### 2. AttributeError
```
AttributeError: 'Role' object has no attribute 'permissions'
```
- 여러 파일에서 `role.permissions.all()` 사용 중

### 3. ValueError
```
ValueError: Cannot assign "<Permission: PATIENT_LIST>":
"RolePermission.permission" must be a "Menu" instance.
```
- `RolePermission.permission`이 이제 `Menu`를 참조하므로 `Permission` 객체 할당 불가

---

## 수정된 파일 목록

### 백엔드 (Django)

#### 1. `apps/accounts/models/role.py`
- `permissions` M2M 필드 제거
- 주석으로 `RolePermission` 모델 참조 안내 추가

#### 2. `apps/authorization/serializers.py`
**`MeSerializer.get_permissions` 메서드 수정**
- 기존: `role.permissions.all()` 사용
- 변경: `RolePermission.objects.filter(role=obj.role)` 사용
- 추가: 부모 메뉴 권한 시 자식(상세 페이지) 자동 포함 로직

```python
def get_permissions(self, obj):
    # 1. RolePermission에 직접 등록된 메뉴 ID 조회
    direct_menu_ids = set(
        RolePermission.objects
        .filter(role=obj.role)
        .values_list("permission_id", flat=True)
    )

    # 2. 직접 등록된 메뉴 + 그 자식 메뉴까지 모두 포함
    all_menu_ids = set(direct_menu_ids)

    def add_children(parent_ids):
        # 재귀적으로 자식 메뉴 추가
        ...

    # 3. path가 있는 메뉴의 code만 반환
    return list(Menu.objects.filter(id__in=all_menu_ids, ...).values_list("code", flat=True))
```

#### 3. `apps/menus/services.py`
**`get_user_menus` 함수 수정**
- 기존: `role.permissions.all()` 사용
- 변경: `RolePermission.objects.filter(role=role)` 사용
- 추가: 자식 메뉴 + 부모 메뉴 재귀 포함 로직
- 사이드바용으로 `breadcrumb_only=False` 필터 추가

#### 4. `apps/authorization/views.py`
**`RoleViewSet.update_menus` 메서드 수정**
- 기존: `Permission.objects.filter()` 사용
- 변경: `Menu.objects.filter()` 사용
- 추가: 권한 변경 시 해당 역할 사용자에게 WebSocket 알림

```python
@action(detail=True, methods=["put"], url_path="menus")
def update_menus(self, request, pk=None):
    # Menu 객체로 RolePermission 생성
    valid_menus = Menu.objects.filter(id__in=menu_ids)

    RolePermission.objects.bulk_create([
        RolePermission(role=role, permission=menu)
        for menu in valid_menus
    ])

    # 해당 역할을 가진 모든 사용자에게 권한 변경 알림
    users_with_role = User.objects.filter(role=role)
    for user in users_with_role:
        notify_permission_changed(user.id)
```

#### 5. `setup_dummy_data/setup_dummy_data_1_base.py`
**역할별 권한 매핑 로직 수정**
- 기존: `role.permissions.set(perms)` M2M 방식
- 변경: `RolePermission.objects.create(role=role, permission=menu)` 직접 생성

```python
# 메뉴 code → Menu 객체 매핑
menu_map = {menu.code: menu for menu in Menu.objects.all()}

for role_code, menu_codes in role_menu_permissions.items():
    role = Role.objects.get(code=role_code)
    RolePermission.objects.filter(role=role).delete()
    for menu_code in menu_codes:
        if menu_code in menu_map:
            RolePermission.objects.create(
                role=role,
                permission=menu_map[menu_code]
            )
```

### 프론트엔드 (React)

#### 6. `src/pages/admin/MenuPermissionPage.tsx`
**저장/비교 로직 수정**
- 기존: `getLeafMenuIds()` - leaf 메뉴만 저장
- 변경: `checkedMenuIds` - 체크된 모든 메뉴 저장

```typescript
const save = async () => {
    // 체크된 모든 메뉴 ID 저장 (백엔드에서 자식 메뉴 자동 포함)
    await saveRoleMenus(selectedRole.id, checkedMenuIds);
    setOriginLeafMenuIds([...checkedMenuIds]);
    alert('저장 완료');
};

const isChanged =
    JSON.stringify(normalize(checkedMenuIds)) !==
    JSON.stringify(normalize(originLeafMenuIds));
```

---

## 주요 기능 개선

### 1. 부모 메뉴 권한 → 자식 자동 포함
- 관리자가 `환자 목록`만 체크해도 `환자 상세` 페이지 접근 가능
- `breadcrumb_only=True` 상세 페이지들이 자동으로 권한에 포함됨

### 2. 사이드바 실시간 갱신
- 권한 변경 시 WebSocket으로 해당 역할 사용자에게 알림
- `AuthProvider`에서 알림 수신 후 메뉴 자동 갱신

### 3. 저장 버튼 동작 수정
- 체크된 메뉴 변경 시 저장 버튼 활성화
- 모든 체크된 메뉴 ID 저장 (leaf만 아님)

---

## 마이그레이션

### 생성된 마이그레이션
- `0006_remove_role_permissions_and_more.py`
  - `Role.permissions` M2M 필드 제거
  - `RolePermission.permission` FK를 `Menu` 참조로 변경
  - 테이블명 `accounts_role_permissions` 유지

### 마이그레이션 실행
```bash
python manage.py migrate
```

---

## 테스트 체크리스트

- [x] 로그인 정상 동작
- [x] 사이드바 메뉴 정상 표시
- [x] 상세 페이지 접근 권한 정상 동작
- [x] 메뉴 권한 관리 페이지 저장 동작
- [x] 권한 변경 시 사이드바 실시간 갱신
- [x] 더미 데이터 생성 정상 동작

---

## 관련 모델 관계도

```
User
  └── role (FK) ──► Role
                      │
                      ▼
                RolePermission
                  ├── role (FK) ──► Role
                  └── permission (FK) ──► Menu
                                            │
                                            ▼
                                         MenuLabel
                                         MenuPermission
```

## 참고 사항

1. `accounts_role_permissions` 테이블은 `RolePermission` 모델이 관리
2. `Permission` 모델은 더 이상 `RolePermission`과 직접 연결되지 않음
3. 메뉴 권한은 `Menu` 모델을 통해 관리됨
