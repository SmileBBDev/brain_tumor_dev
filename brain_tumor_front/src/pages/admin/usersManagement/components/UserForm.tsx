import { useState } from "react";
import UserInfoSection from "./UserInfoSection";
import AccountSection, { type AccountForm } from "./AccountSection";
import type { UserProfileForm } from "@/types/user";

interface Props {
  onSubmit: (data: { profile: UserProfileForm; account: AccountForm }) => void;
  onClose: () => void;
  onCreated: () => void;
  initialData?: {
    profile?: UserProfileForm;
    account?: AccountForm;
  };
}

export default function UserForm({ onSubmit, onClose, onCreated, initialData }: Props) {
  const [profile, setProfile] = useState<UserProfileForm>({
    name: "",
    birthDate: "",
    phoneMobile: "",
    phoneOffice: "",
    email: "",
    hireDate: "",
    departmentId: "",
    title: "",
    ...initialData?.profile,
  });

  const [account, setAccount] = useState<AccountForm>({
    login_id: "",
    password: "",
    role: "",
    ...initialData?.account,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({ profile, account });
    onCreated();
    onClose();
  };

  return (
    <form className="user-form" onSubmit={handleSubmit}>
      <UserInfoSection value={profile} onChange={setProfile} />
      <AccountSection value={account} onChange={setAccount} />
    </form>
  );
}