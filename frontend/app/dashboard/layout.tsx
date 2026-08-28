"use client";

import Sidebar from "@/components/Sidebar";
import ToastContainer from "@/components/Toast";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto" style={{ background: "var(--bg-primary)" }}>
        {children}
      </main>
      <ToastContainer />
    </div>
  );
}
