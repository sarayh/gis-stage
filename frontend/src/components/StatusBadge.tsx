import { StatutStage } from '../types';

interface StatusBadgeProps {
  status: StatutStage;
}

const statusLabels: Record<StatutStage, string> = {
  brouillon: 'Brouillon',
  valide: 'Validé',
  conventionne: 'Conventionné',
  en_cours: 'En cours',
  termine: 'Terminé',
  annule: 'Annulé',
  refuse: 'Refusé',
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`badge badge-${status}`}>
      {statusLabels[status]}
    </span>
  );
}
