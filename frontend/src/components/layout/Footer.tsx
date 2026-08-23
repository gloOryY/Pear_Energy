import Link from 'next/link';
import { Phone, ShieldCheck } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-graphite-700 mt-16">
      <div className="max-w-7xl mx-auto px-4 py-10 grid gap-8 md:grid-cols-3 text-sm text-zinc-400">
        <div>
          <div className="font-semibold text-zinc-200 mb-2">Контакты</div>
          <p>7 (700) 000-00-00<br />+7 (999) 000-00-00<br />{new Date().getFullYear()} © ChargePoint Road</p>
        </div>
        <div>
          <div className="flex flex-col gap-2">
            <div className="font-semibold text-zinc-200 mb-1">Документы</div>
            <Link href="/legal/terms" className="hover:text-accent">Условия использования</Link>
            <Link href="/legal/privacy" className="hover:text-accent">Политика конфиденциальности</Link>
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <div className="font-semibold text-zinc-200 mb-1">Поддержка 24/7</div>
          <a href="tel:+78005553535" className="flex items-center gap-2 hover:text-accent"><Phone size={15} />8 800 555-35-35</a>
          <span className="flex items-center gap-2"><ShieldCheck size={15} />support@chargepoint-road.ru</span>
        </div>
      </div>
    </footer>
  );
}
