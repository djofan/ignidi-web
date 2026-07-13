import { Flame } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--color-line)] py-10">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 font-mono text-xs text-[var(--color-slate)] sm:flex-row">
        <div className="flex items-center gap-2">
          <Flame className="h-4 w-4 text-[var(--color-ember)]" />
          <span>IGNIDI WEB — ©{new Date().getFullYear()}</span>
        </div>
        <p>Build with &lt;3 &amp; in Bekasi, ID.</p>
      </div>
    </footer>
  );
}
