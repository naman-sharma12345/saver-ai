import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { useNearbyStores, useExpenses, useCheaperAlternatives } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';
import { MapPin, Navigation } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { useTheme } from '../../context/ThemeContext';

const NOIDA_CENTER: [number, number] = [28.6270, 77.3650];

export const Stores = () => {
  const [selectedExpenseId, setSelectedExpenseId] = useState<number | null>(null);
  const [alternatives, setAlternatives] = useState<any>(null);
  const { resolved } = useTheme();

  const { data: storesData, isLoading: lS } = useNearbyStores({ lat: NOIDA_CENTER[0], lng: NOIDA_CENTER[1], radius: 10 }, true);
  const { data: expensesData, isLoading: lE } = useExpenses();
  const cheaperMutation = useCheaperAlternatives();

  const handleFindCheaper = (expenseId: number) => {
    setSelectedExpenseId(expenseId);
    cheaperMutation.mutate({ expenseId }, {
      onSuccess: (data) => { setAlternatives(data); toast.success(`Found ${data.alternatives?.length || 0} alternatives!`); },
      onError: () => { toast.error("No alternatives found"); }
    });
  };

  if (lS || lE) return <Loader />;

  const stores = storesData?.stores || [];
  const expenses = expensesData?.expenses || [];

  return (
    <div className="h-[calc(100vh-7rem)] flex flex-col lg:flex-row gap-4">
      {/* Map */}
      <div className="flex-1 rounded-[22px] overflow-hidden border border-black/[0.06] relative z-0">
        <MapContainer center={NOIDA_CENTER} zoom={15} className="w-full h-full" zoomControl={false}>
          <TileLayer key={resolved} url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" className={resolved === 'dark' ? 'map-dark-tiles' : ''} attribution='&copy; OpenStreetMap' />
          {stores.map((store: any) => (
            <Marker key={store.id} position={[store.lat, store.lng]}>
              <Popup><div className="font-sans"><h3 className="font-bold text-sm">{store.name}</h3><p className="text-xs text-slate-500">{store.category}</p></div></Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Panel */}
      <div className="w-full lg:w-[380px] flex flex-col gap-3 z-10">
        <Card className="p-5 flex-1 overflow-y-auto no-scrollbar">
          <div className="mb-1">
            <h2 className="text-[21px] font-semibold tracking-[-0.022em] text-ink">Find cheaper options</h2>
          </div>
          <p className="text-[14px] text-ink-2 mb-5">Pick a past expense to see nearby places that cost less.</p>

          <div className="space-y-2">
            {expenses.slice(0, 10).map((exp: any) => (
              <div
                key={exp.id}
                onClick={() => handleFindCheaper(exp.id)}
                className={`p-3.5 rounded-2xl border cursor-pointer transition-all ${selectedExpenseId === exp.id ? 'border-[#0071e3] bg-[#0071e3]/[0.06]' : 'border-transparent bg-black/[0.03] hover:bg-black/[0.06]'}`}
              >
                <div className="flex justify-between items-start">
                  <p className="text-sm font-medium text-white truncate pr-2">{exp.description}</p>
                  <span className="text-sm font-semibold text-white tabular-nums flex-shrink-0">{formatCurrency(exp.amount)}</span>
                </div>
                <div className="flex items-center text-[11px] text-slate-600 mt-1 gap-2">
                  <span>{exp.store_name}</span>
                  <span>•</span>
                  <span>{exp.category}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <AnimatePresence>
          {alternatives?.alternatives?.length > 0 && (
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 20, opacity: 0 }}>
              <Card className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-[16px] font-semibold text-ink">Better options</h3>
                  <button onClick={() => setAlternatives(null)} className="text-[13px] text-accent hover:underline">Close</button>
                </div>
                <div className="space-y-2">
                  {alternatives.alternatives.map((alt: any, i: number) => (
                    <div key={i} className="p-3.5 rounded-2xl bg-black/[0.03]">
                      <div className="flex justify-between items-start">
                        <p className="text-sm font-medium text-white">{alt.store.name}</p>
                        <span className="text-[12px] font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full tabular-nums">
                          Save {formatCurrency(alt.estimated_saving)}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1.5 text-[11px] text-slate-600">
                        <span className="flex items-center gap-1"><Navigation size={10} />{alt.distance_km} km</span>
                        <span className="flex items-center gap-1"><MapPin size={10} />{alt.store.address}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
