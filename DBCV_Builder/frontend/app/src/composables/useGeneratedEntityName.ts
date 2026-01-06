import { useUsersStore } from '@/stores';

type EntityType = 'канал' | 'агент' | 'виджет' | 'реквест' | 'шаблон';

export function useGeneratedEntityName() {
  const usersStore = useUsersStore();

  const getCurrentDate = () => {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    return `${day}/${month}`;
  };

  const generateName = (entityType: EntityType): string => {
    const date = getCurrentDate();
    const user = usersStore.currentUser;

    return `Новый ${entityType} ${user?.first_name || ''} ${user?.last_name || ''} ${date}`;
  };

  return {
    generateName,
  };
}
