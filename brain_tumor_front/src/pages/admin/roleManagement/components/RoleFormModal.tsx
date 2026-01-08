import { useEffect, useState } from "react";
import type { Role } from "@/types/role";

interface Props {
  open: boolean;
  role?: Role | null;
  onClose: () => void;
  onSubmit: (data: any) => void;
}

export default function RoleFormModal({
  open,
  role,
  onClose,
  onSubmit,
}: Props) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [description, setDescription] = useState("");
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    if (role) {
      setName(role.name);
      setCode(role.code);
      setDescription(role.description || "");
      setIsActive(role.is_active);
    } else {
      setName("");
      setCode("");
      setDescription("");
      setIsActive(true);
    }
  }, [role]);

  if (!open) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3>{role ? "역할 수정" : "역할 생성"}</h3>

        <input
          placeholder="역할명"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {!role && (
          <input
            placeholder="역할 코드 (ROLE_*)"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
        )}

        <textarea
          placeholder="설명"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        {role && (
          <label>
            <input
              type="checkbox"
              checked={isActive}
              onChange={() => setIsActive(!isActive)}
            />
            활성
          </label>
        )}

        <div className="actions">
          <button onClick={onClose}>취소</button>
          <button
            onClick={() =>
              onSubmit({
                name,
                code,
                description,
                is_active: isActive,
              })
            }
          >
            저장
          </button>
        </div>
      </div>
    </div>
  );
}
