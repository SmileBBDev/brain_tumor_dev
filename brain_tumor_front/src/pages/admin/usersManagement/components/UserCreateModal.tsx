// 사용자 추가 모달 컴포넌트
import type { UserProfileForm } from "@/types/user";
import UserForm from "./UserForm";
import type { AccountForm } from "./AccountSection";
import { createUser, type CreateUserPayload } from "@/services/users.api";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export default function UserCreateModal({ onClose, onCreated }: Props) {
  const handleSubmit = async (data: { profile: UserProfileForm; account: AccountForm }) => {
    // profile + account → CreateUserPayload로 변환
    const payload: CreateUserPayload = {
      login_id: data.account.login_id,
      password: data.account.password,
      role: data.account.role,
      name: data.profile.name,
      email: data.profile.email,
      phoneMobile: data.profile.phoneMobile,
      phoneOffice: data.profile.phoneOffice,
      birthDate: data.profile.birthDate,
      hireDate: data.profile.hireDate,
      departmentId: data.profile.departmentId,
      title: data.profile.title,
    };

    await createUser(payload);   // API 호출
    onCreated();              // 부모(UserListPage)에서 목록 새로고침
    onClose();                // 모달 닫기
  };


  return (
     <div className="user-create-modal-backdrop">
      <div className="user-create-modal">
        <h3>신규 사용자 생성</h3>

        {/* 입력 폼 */}
        <UserForm onSubmit={handleSubmit} onClose={onClose} onCreated={onCreated} />

        {/* 모달 하단 버튼 */}
        <div className="form-actions">
          <button type="button" className="ghost" onClick={onClose}>
            취소
          </button>
          <button
            className="primary"
            type="button"
            onClick={() => {
              // UserForm 내부의 handleSubmit을 직접 호출할 수 없으니,
              // 저장 버튼을 모달에서 제어하려면 UserForm을 ref로 감싸거나
              // onSubmit을 여기서 직접 실행하도록 구조를 바꿔야 합니다.
              // 간단히는 UserForm을 form 태그로 두고, 이 버튼에 form="user-form" 속성을 주면 됩니다.
              const form = document.querySelector<HTMLFormElement>(".user-form");
              form?.requestSubmit();
            }}
          >
            저장
          </button>
        </div>
      </div>

      
    </div>

  );
}