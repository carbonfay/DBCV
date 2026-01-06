import { ref, computed } from 'vue';

interface RecentItem {
  id: string;
  name: string;
  type: 'channel' | 'bot' | 'request' | 'widget';
  timestamp: number;
}

const MAX_RECENT_ITEMS = 8;

export function useRecentItems(type: 'channel' | 'bot' | 'request' | 'widget') {
  const storageKey = `recent_${type}s`;

  // Загружаем из localStorage
  const loadRecentItems = (): RecentItem[] => {
    try {
      const stored = localStorage.getItem(storageKey);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  };

  const recentItems = ref<RecentItem[]>(loadRecentItems());

  // Добавляем новый элемент в список
  const addRecentItem = (id: string, name: string) => {
    const newItem: RecentItem = {
      id,
      name,
      type,
      timestamp: Date.now(),
    };

    // Убираем дубликаты по ID
    const filtered = recentItems.value.filter((item) => item.id !== id);

    // Добавляем новый элемент в начало
    const updated = [newItem, ...filtered];

    // Ограничиваем до MAX_RECENT_ITEMS
    const limited = updated.slice(0, MAX_RECENT_ITEMS);

    recentItems.value = limited;

    // Сохраняем в localStorage
    localStorage.setItem(storageKey, JSON.stringify(limited));
  };

  // Получаем список последних элементов
  const getRecentItems = computed(() => recentItems.value);

  // Очищаем список
  const clearRecentItems = () => {
    recentItems.value = [];
    localStorage.removeItem(storageKey);
  };

  return {
    recentItems: getRecentItems,
    addRecentItem,
    clearRecentItems,
  };
}
