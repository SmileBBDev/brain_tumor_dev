export interface AccountForm {
  login_id: string;
  password: string;
  role: string;
}


interface Props {
  value: AccountForm;
  onChange: (v: AccountForm) => void;
}

export default function AccountSection({ value, onChange }: Props) {
  const handle =
    (key: keyof AccountForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      onChange({ ...value, [key]: e.target.value });
    };

  return (
    <section className="form-section dashed">
      <h3 className="section-title">계정 부여</h3>

      <div className="field">
        <label>User ID</label>
        <input
          className="userInfo"
          value={value.login_id} 
          onChange={handle("login_id")} />
      </div>

      <div className="field">
        <label>Password</label>
        <input
          type="password"
          className="userInfo"
          value={value.password}
          onChange={handle("password")}
        />
      </div>

      <div className="field">
        <label>역할</label>
        <select 
          className="userInfoOption"
          value={value.role} 
          onChange={handle("role")}
        >
          <option value="">선택</option>
          <option value="ADMIN">관리자</option>
          <option value="DOCTOR">의사</option>
          <option value="NURSE">간호사</option>
          <option value="PATIENT">환자</option>
          <option value="RIS">영상과</option>
          <option value="LIS">검사과</option>
        </select>
      </div>
    </section>
  );
}
