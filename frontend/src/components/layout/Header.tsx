'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Zap, MapPin, User, LayoutDashboard, LogOut, Menu } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../../stores/auth';
import { Button } from '../ui';
import { post } from '../../lib/api';

export default function Header() {
  const { user, accessToken, clear } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const logout = async () => {
    try { await post('auth/logout', { refresh_token: useAuth.getState().refreshToken }); } catch { clear(); }
    router.push('/');
  };
  const cabinetHref = user?.role === 'admin' ? '/admin' : user?.role === 'operator' ? '/operator' : '/account';
  return (
    <header className="sticky top-0 z-50 border-b border-graphite-700 bg-graphite-900/90 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          <span className="w-9 h-9 rounded-xl bg-accent flex items-center justify-center"><Zap size={20} className="text-graphite-950" /></span>
          <span>ChargePoint</span><span className="text-accent">Road</span>
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-sm">
          <Link href="/map" className="flex items-center gap-1.5 text-zinc-300 hover:text-accent"><MapPin size={16} />Карта</Link>
          {accessToken ? (
            <Link href={cabinetHref} className="flex items-center gap-1.5 text-zinc-300 hover:text-accent"><LayoutDashboard size={16} />Кабинет</Link>
          ) : null}
        </nav>
        <div className="hidden md:block">
          {accessToken ? (
            <div className="flex items-center gap-3">
              <Link href={cabinetHref}><Button variant="secondary" className="!py-2 !px-4"><User size={16} className="mr-1 inline" />{user?.full_name?.split(' ')[0]}</Button></Link>
              <button onClick={logout} aria-label="Выйти" className="p-2 rounded-lg hover:bg-graphite-700 text-zinc-400"><LogOut size={18} /></button>
            </div>
          ) : (
            <div className="flex gap-2">
              <Link href="/auth/login"><Button variant="secondary" className="!py-2">Войти</Button></Link>
              <Link href="/auth/register"><Button className="!py-2">Регистрация</Button></Link>
            </div>
          )}
        </div>
        <button className="md:hidden p-2" onClick={() => setOpen(!open)} aria-label="Меню"><Menu /></button>
      </div>
      {open && (
        <div className="md:hidden border-t border-graphite-700 px-4 py-4 flex flex-col gap-3">
          <Link href="/map" onClick={() => setOpen(false)}>Карта</Link>
          {accessToken ? (
            <Link href={cabinetHref} onClick={() => setOpen(false)}>Кабинет</Link>
          ) : null}
          {accessToken ? (
            <Button variant="secondary" onClick={logout}>Выйти</Button>
          ) : (
            <>
              <Link href="/auth/login"><Button variant="secondary" className="w-full">Войти</Button></Link>
              <Link href="/auth/register"><Button className="w-full">Регистрация</Button></Link>
            </>
          )}
        </div>
      )}
    </header>
  );
}
