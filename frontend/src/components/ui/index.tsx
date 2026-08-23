'use client';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import React from 'react';
import { Loader2, X } from 'lucide-react';

export const cn = (...a: any[]) => twMerge(clsx(...a));

export function Button({ className, variant = 'primary', loading, children, ...p }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' | 'ghost'; loading?: boolean }) {
  return (
    <button {...p} disabled={p.disabled || loading} className={cn(variant === 'primary' ? 'btn-primary' : variant === 'secondary' ? 'btn-secondary' : variant === 'danger' ? 'btn-danger' : 'px-3 py-1.5 rounded-lg text-sm text-zinc-300 hover:text-white hover:bg-graphite-700', className)}>
      {loading ? <Loader2 className="animate-spin inline mr-2 size-[18px]" /> : null}
      {children}
    </button>
  );
}

export function Input({ className, ...p }: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...p} className={cn('input', className)} />;
}

export function Label({ children, ...p }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return <label {...p} className="label">{children}</label>;
}

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn('card p-5', className)}>{children}</div>;
}

const STATUS_STYLE: Record<string, string> = {
  available: 'bg-ok/15 text-ok border-ok/30',
  charging: 'bg-accent/15 text-accent border-accent/30',
  preparing: 'bg-accent/15 text-accent border-accent/30',
  vehicle_connected: 'bg-warn/15 text-warn border-warn/30',
  awaiting_payment: 'bg-warn/15 text-warn border-warn/30',
  suspended_ev: 'bg-warn/15 text-warn border-warn/30',
  finishing: 'bg-accent/15 text-accent border-accent/30',
  offline: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
  unavailable: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
  faulted: 'bg-danger/15 text-danger border-danger/30',
  emergency_stop: 'bg-danger/15 text-danger border-danger/30',
};

const STATUS_LABEL: Record<string, string> = {
  available: 'Свободна',
  charging: 'Зарядка',
  preparing: 'Подготовка',
  vehicle_connected: 'Подключён',
  awaiting_payment: 'Ожидает оплаты',
  suspended_ev: 'Приостановлена',
  finishing: 'Завершение',
  offline: 'Офлайн',
  unavailable: 'Недоступна',
  faulted: 'Неисправна',
  emergency_stop: 'Аварийная остановка',
};

export const statusLabel = (s: string) => STATUS_LABEL[s] ?? s;

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 border rounded-full px-3 py-1 text-xs font-medium', STATUS_STYLE[status] ?? '', className)}>
      <span className={cn('w-2 h-2 rounded-full', STATUS_STYLE[status]?.includes('available') ? 'bg-ok' : STATUS_STYLE[status]?.includes('charging') || STATUS_STYLE[status]?.includes('preparing') || STATUS_STYLE[status]?.includes('finishing') ? 'bg-accent animate-pulse' : STATUS_STYLE[status]?.includes('faulted') || STATUS_STYLE[status]?.includes('emergency_stop') ? 'bg-danger' : 'bg-current')} />
      {statusLabel(status)}
    </span>
  );
}

export function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn('inline-block border border-graphite-600 rounded-lg px-2.5 py-1 text-xs text-zinc-300', className)}>{children}</span>;
}

export function Modal({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode; wide?: boolean }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-100 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className={cn('relative card w-full max-h-[92vh] overflow-y-auto rounded-b-none sm:rounded-2xl p-6', wide ? 'sm:max-w-2xl' : 'sm:max-w-md')}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold">{title}</h3>
          <button onClick={onClose} aria-label="Закрыть" className="p-2 rounded-lg hover:bg-graphite-700"><X size={18} /></button>
        </div>
        <div>{children}</div>
      </div>
    </div>
  );
}

export function Tabs({ tabs, value, onChange }: { tabs: { key: string; label: string }[]; value: string; onChange: (k: string) => void }) {
  return (
    <div className="flex gap-1 overflow-x-auto pb-1 -mx-1 px-1">
      {tabs.map((t) => (
        <button key={t.key} onClick={() => onChange(t.key)} className={cn('whitespace-nowrap px-4 py-2 rounded-xl text-sm font-medium transition-colors', value === t.key ? 'bg-accent text-graphite-950' : 'bg-graphite-800 text-zinc-400 hover:text-zinc-200')}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-pulse bg-graphite-750 rounded-xl', className)} />;
}

export function Progress({ value, className }: { value: number; className?: string }) {
  return (
    <div className={cn('h-3 bg-graphite-750 rounded-full overflow-hidden', className)}>
      <div className="h-full bg-gradient-to-r from-accent-dim to-accent-bright rounded-full transition-all duration-700" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  );
}
