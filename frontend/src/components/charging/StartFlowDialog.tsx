'use client';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Zap, BatteryCharging, CreditCard, CheckCircle2 } from 'lucide-react';
import { Modal, Button, Card, Badge, Progress, Skeleton } from '../ui';
import { get, post } from '../../lib/api';
import { useAuth } from '../../stores/auth';
import { money } from '../../lib/format';
import type { StationDetail } from '../../types';

interface Props { open: boolean; onClose: () => void; station: StationDetail; }

const LIMIT_TYPES = [{ k: 'kwh', l: 'кВт⋅ч' }, { k: 'rub', l: '₽' }, { k: 'minutes', l: 'мин' }];
const LIMIT_PRESETS: Record<string, { label: string; value: number }[]> = {
  kwh: [{ label: '10', value: 10 }, { label: '20', value: 20 }, { label: '40', value: 40 }],
  rub: [{ label: '300', value: 300 }, { label: '500', value: 500 }, { label: '1000', value: 1000 }],
  minutes: [{ label: '30', value: 30 }, { label: '120', value: 120 }, { label: '240', value: 240 }],
};

export function StartFlowDialog({ open, onClose, station }: Props) {
  const user = useAuth();
  const [step, setStep] = useState(1);
  const [limitType, setLimitType] = useState<'kwh' | 'rub' | 'minutes'>('kwh');
  const [limitValue, setLimitValue] = useState<number>(10);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [paymentId, setPaymentId] = useState<string | null>(null);

  const { data: quote, isLoading: qLoading } = useQuery({
    queryKey: ['quote', station.id, limitType, limitValue],
    enabled: step === 2,
    queryFn: () => post<any>('charging-sessions/quote', { station_id: station.id, limit_type: limitType, limit_value: limitValue }),
  });

  const startSession = async () => {
    const r = await post('charging-sessions/start', { station_id: station.id, limit_type: limitType, limit_value: limitValue });
    setSessionId(r.id);
    setStep(3);
  };

  const createPayment = async () => {
    const r = await post('payments/create', { session_id: sessionId, method: 'sbp_qr' });
    setPaymentId(r.payment.id);
    setStep(4);
  };

  const simulateSuccess = async () => {
    await post(`payments/mock/${paymentId}/simulate-success`, {});
    setStep(5);
  };

  if (!user.accessToken) {
    return <Modal open={open} onClose={onClose} title="Начать зарядку"><p className="text-sm text-zinc-400 mb-4">Для начала зарядки необходимо войти в аккаунт</p><div className="flex gap-2"><Button variant="secondary" onClick={onClose}>Отмена</Button><Button onClick={() => window.location.href='/auth/login'}>Войти</Button></div></Modal>;
  }

  return (
    <Modal open={open} onClose={onClose} title="Начать зарядку" wide>
      <div className="flex items-center gap-2 mb-6">
        {[1, 2, 3, 4, 5].map((n) => (<div key={n} className={n <= step ? 'text-accent' : 'text-zinc-500'}><CheckCircle2 size={20} /></div>))}
      </div>
      {step === 1 && (
        <div className="space-y-4">
          <Card className="p-4"><div className="flex items-center gap-3"><Zap size={24} className="text-accent" /><div><div className="font-semibold">{station.name}</div><div className="text-sm text-zinc-400">{station.address}</div></div></div></Card>
          <div className="grid grid-cols-3 gap-2">
            {LIMIT_TYPES.map((t) => (<Button key={t.k} variant={limitType === t.k ? 'primary' : 'secondary'} onClick={() => { setLimitType(t.k as any); setLimitValue(LIMIT_PRESETS[t.k][0].value); }}>{t.l}</Button>))}
          </div>
          <div className="grid grid-cols-3 gap-2">
            {LIMIT_PRESETS[limitType].map((p) => (<Button key={p.value} variant={limitValue === p.value ? 'primary' : 'secondary'} onClick={() => setLimitValue(p.value)}>{p.label}</Button>))}
          </div>
          <div className="flex gap-2"><Button variant="secondary" onClick={onClose}>Отмена</Button><Button onClick={() => setStep(2)}>Далее</Button></div>
        </div>
      )}
      {step === 2 && (
        <div className="space-y-4">
          {qLoading ? <Skeleton className="h-24" /> : (
            <Card className="p-4">
              <div className="text-sm text-zinc-400">Примерная стоимость</div>
              <div className="text-2xl font-bold text-accent mt-1">{money(Number(quote.estimated_amount ?? 0))} ₽</div>
              <div className="text-xs text-zinc-500 mt-1">{quote.estimated_kwh} кВт⋅ч · {quote.estimated_minutes} мин</div>
            </Card>
          )}
          <div className="flex gap-2"><Button variant="secondary" onClick={() => setStep(1)}>Назад</Button><Button onClick={startSession}>Подтвердить и начать</Button></div>
        </div>
      )}
      {step === 3 && (
        <div className="space-y-4">
          <Card className="p-4"><div className="flex items-center gap-3"><BatteryCharging size={24} className="text-accent" /><div><div className="font-semibold">Сессия создана</div><div className="text-sm text-zinc-400">Ожидает оплаты</div></div></div></Card>
          <div className="flex gap-2"><Button variant="secondary" onClick={onClose}>Отмена</Button><Button onClick={createPayment}>Оплатить</Button></div>
        </div>
      )}
      {step === 4 && (
        <div className="space-y-4">
          <Card className="p-4"><div className="flex items-center gap-3"><CreditCard size={24} className="text-accent" /><div><div className="font-semibold">Оплата</div><div className="text-sm text-zinc-400">СБП QR</div></div></div></Card>
          <div className="flex gap-2"><Button variant="secondary" onClick={() => setStep(3)}>Назад</Button><Button onClick={simulateSuccess}>Симулировать успешную оплату</Button></div>
        </div>
      )}
      {step === 5 && (
        <div className="space-y-4">
          <Card className="p-4"><div className="flex items-center gap-3"><CheckCircle2 size={24} className="text-ok" /><div><div className="font-semibold">Оплата прошла</div><div className="text-sm text-zinc-400">Станция запускает зарядку</div></div></div></Card>
          <Button onClick={onClose}>Готово</Button>
        </div>
      )}
    </Modal>
  );
}
