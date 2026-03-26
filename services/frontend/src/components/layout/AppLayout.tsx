"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Search,
  Heart,
  Bell,
  Radio,
  Trophy,
  BarChart3,
  Radar,
} from "lucide-react";
import type { ReactNode } from "react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/search", label: "Busca", icon: Search },
  { href: "/ranking", label: "Ranking", icon: Trophy },
  { href: "/wishlist", label: "Wishlist", icon: Heart },
  { href: "/alerts", label: "Alertas", icon: Bell },
  { href: "/groups", label: "Grupos", icon: Radio },
];

export function AppLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-surface-50">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-surface-200 bg-white">
        {/* Logo */}
        <div className="flex h-16 items-center gap-3 border-b border-surface-100 px-6">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Radar className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-surface-900 tracking-tight">
              PromoRadar
            </h1>
            <p className="text-[10px] font-medium text-surface-700/40 uppercase tracking-widest">
              Telegram
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname?.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-surface-700/70 hover:bg-surface-50 hover:text-surface-900"
                )}
              >
                <Icon className={cn("h-4.5 w-4.5", isActive && "text-brand-600")} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="border-t border-surface-100 p-4">
          <div className="rounded-lg bg-surface-50 p-3">
            <p className="text-xs font-medium text-surface-700/60">
              PromoRadar v0.1.0
            </p>
            <p className="text-[10px] text-surface-700/40 mt-0.5">
              Inteligência de preços via Telegram
            </p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 flex-1">
        <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
      </main>
    </div>
  );
}
