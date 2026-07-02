import { Outlet } from "react-router-dom";

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <main className="mx-auto w-full max-w-[1120px] px-4 py-8 md:px-6 md:py-12">
        <Outlet />
      </main>
    </div>
  );
}
