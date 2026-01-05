import type { UserProfileForm } from "@/types/user";

interface Props {
  value: UserProfileForm;
  onChange: (v: UserProfileForm) => void;
}

export default function UserInfoSection({ value, onChange }: Props) {
    const handle = 
    (key : keyof UserProfileForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        onChange({ ...value, [key]: e.target.value });
    };


  return (
    <section className="form-section dashed">
      <h3 className="section-title">개인정보</h3>

      <div className="user-info-grid">
        {/* 프로필 */}
        <div className="profile-box">
          <div className="profile-image" />
        </div>

        {/* 입력 필드 */}
        <div className="info-fields">
          <div className="field">
            <label>이름</label>
            <input 
                id="user-name"
                className = "userInfo"
                value={value.name} 
                onChange={handle("name")} />
          </div>

          <div className="field">
            <label>성년월일</label>
            <input 
                id="user-birth-date" 
                className = "userInfo"
                value={value.birthDate} 
                onChange={handle("birthDate")} />
          </div>

          <div className="field">
            <label>연락처</label>
            <input
              placeholder="010-0000-0000"
              id="user-phone-mobile"
                className = "userInfo"
              value={value.phoneMobile}
              onChange={handle("phoneMobile")}
            />
          </div>

          <div className="field">
            <label>이메일</label>
             <input
              type="email"
              id="user-email"
              className = "userInfo"
              value={value.email}
              onChange={handle("email")}
            />
          </div>

          <div className="field">
            <label>유선전화</label>
            <input
              placeholder="042-000-0000"
              id="user-phone-office"
              className = "userInfo"
              value={value.phoneOffice}
              onChange={handle("phoneOffice")}
            />
          </div>

          <div className="field">
            <label>입사일</label>
            <input
              type="date"
              id="user-hire-date"
              className="userInfo"
              value={value.hireDate}
              onChange={handle("hireDate")}
            />
          </div>

          <div className="field">
            <label>소속부서</label>
             <select
              className="userInfoOption"
              value={value.departmentId}
              onChange={handle("departmentId")}
            >
              <option value="">선택</option>
              <option value="1">신경외과</option>
              <option value="2">영상의학과</option>
              <option value="3">검사과</option>
            </select>
          </div>

          <div className="field">
            <label>호칭</label>
            <select 
                className="userInfoOption" 
                value={value.title} onChange={handle("title")}>
              <option value="">선택</option>
              <option value="교수">교수</option>
              <option value="정교수">정교수</option>
              <option value="전문의">전문의</option>
            </select>
          </div>
        </div>
      </div>
    </section>
  );
}