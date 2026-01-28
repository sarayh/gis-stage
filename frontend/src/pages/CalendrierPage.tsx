import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { stagesApi, servicesApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, isWithinInterval, parseISO } from 'date-fns';
import { fr } from 'date-fns/locale';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function CalendrierPage() {
  const { user } = useAuth();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedService, setSelectedService] = useState<number | null>(
    user?.role === 'cadre' ? user.service_id : null
  );

  const { data: services } = useQuery({
    queryKey: ['services'],
    queryFn: () => servicesApi.list(),
  });

  const { data: calendrierData } = useQuery({
    queryKey: ['calendrier', selectedService, currentDate.getMonth(), currentDate.getFullYear()],
    queryFn: () =>
      stagesApi.getCalendrier(selectedService!, {
        mois: currentDate.getMonth() + 1,
        annee: currentDate.getFullYear(),
      }),
    enabled: !!selectedService,
  });

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

  const previousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const getStagesForDay = (day: Date) => {
    if (!calendrierData) return [];
    return calendrierData.filter((stage: { date_debut: string; date_fin: string }) => {
      const debut = parseISO(stage.date_debut);
      const fin = parseISO(stage.date_fin);
      return isWithinInterval(day, { start: debut, end: fin });
    });
  };

  const dayNames = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Calendrier des stages</h1>
        {user?.role !== 'cadre' && (
          <select
            value={selectedService || ''}
            onChange={(e) => setSelectedService(e.target.value ? Number(e.target.value) : null)}
            className="input w-64"
          >
            <option value="">Sélectionner un service</option>
            {services?.map((service) => (
              <option key={service.id} value={service.id}>
                {service.nom_service}
              </option>
            ))}
          </select>
        )}
      </div>

      {!selectedService ? (
        <div className="card p-12 text-center">
          <p className="text-gray-500">Sélectionnez un service pour afficher le calendrier</p>
        </div>
      ) : (
        <div className="card">
          <div className="p-4 border-b flex items-center justify-between">
            <button onClick={previousMonth} className="p-2 hover:bg-gray-100 rounded-lg">
              <ChevronLeft className="h-5 w-5" />
            </button>
            <h2 className="text-lg font-semibold capitalize">
              {format(currentDate, 'MMMM yyyy', { locale: fr })}
            </h2>
            <button onClick={nextMonth} className="p-2 hover:bg-gray-100 rounded-lg">
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-7">
            {dayNames.map((day) => (
              <div
                key={day}
                className="p-2 text-center text-sm font-medium text-gray-500 border-b"
              >
                {day}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7">
            {Array.from({ length: (monthStart.getDay() + 6) % 7 }).map((_, i) => (
              <div key={`empty-${i}`} className="h-24 border-b border-r p-1" />
            ))}

            {days.map((day) => {
              const stagesOfDay = getStagesForDay(day);
              return (
                <div
                  key={day.toISOString()}
                  className={`h-24 border-b border-r p-1 ${
                    !isSameMonth(day, currentDate) ? 'bg-gray-50' : ''
                  } ${isToday(day) ? 'bg-primary-50' : ''}`}
                >
                  <span
                    className={`text-sm ${
                      isToday(day)
                        ? 'bg-primary-600 text-white rounded-full w-6 h-6 flex items-center justify-center'
                        : ''
                    }`}
                  >
                    {format(day, 'd')}
                  </span>
                  <div className="mt-1 space-y-1 overflow-y-auto max-h-16">
                    {stagesOfDay.slice(0, 2).map((stage: { id: number; etudiant: string; code_egis: string }) => (
                      <div
                        key={stage.id}
                        className="text-xs bg-green-100 text-green-800 px-1 py-0.5 rounded truncate"
                        title={`${stage.etudiant} (${stage.code_egis})`}
                      >
                        {stage.etudiant}
                      </div>
                    ))}
                    {stagesOfDay.length > 2 && (
                      <div className="text-xs text-gray-500">
                        +{stagesOfDay.length - 2} autre(s)
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {selectedService && calendrierData && calendrierData.length > 0 && (
        <div className="card p-6">
          <h3 className="font-semibold mb-4">Stages du mois</h3>
          <div className="space-y-2">
            {calendrierData.map((stage: { id: number; etudiant: string; code_egis: string; date_debut: string; date_fin: string; statut: string }) => (
              <div
                key={stage.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium">{stage.etudiant}</p>
                  <p className="text-sm text-gray-500">{stage.code_egis}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm">
                    {format(parseISO(stage.date_debut), 'dd/MM')} -{' '}
                    {format(parseISO(stage.date_fin), 'dd/MM/yyyy')}
                  </p>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      stage.statut === 'en_cours'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {stage.statut}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
