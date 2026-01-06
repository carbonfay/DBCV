import { ref, computed } from 'vue';
import { useRecentItems } from '@/composables/useRecentItems';

export type SortOption = 'recently_updated' | 'newest' | 'name' | 'recently_opened';

export interface SortConfig {
  value: SortOption;
  label: string;
}

interface WithRequiredFields {
  id: string;
  name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export const defaultSortOptions: SortConfig[] = [
  { value: 'recently_updated', label: 'Недавно обновленные' },
  { value: 'newest', label: 'Новые' },
  { value: 'name', label: 'По названию' },
];

export const getSortOptionsWithRecent = (hasRecentItems: boolean): SortConfig[] => {
  const baseOptions = [...defaultSortOptions];
  if (hasRecentItems) {
    baseOptions.unshift({ value: 'recently_opened', label: 'Последние открытые' });
  }
  return baseOptions;
};

export function useSorting<T extends WithRequiredFields>(
  items: T[] | (() => T[]),
  customSortOptions?: SortConfig[],
  recentType?: 'channel' | 'bot' | 'request' | 'widget'
) {
  const sortOption = ref<SortOption>('recently_updated');
  const searchQuery = ref('');

  // Управляем recent items внутри useSorting
  const { recentItems, addRecentItem } = recentType
    ? useRecentItems(recentType)
    : { recentItems: ref([]), addRecentItem: () => {} };

  const sortOptions = computed(() => {
    const hasRecent = recentItems.value.length > 0;
    return customSortOptions || getSortOptionsWithRecent(hasRecent);
  });

  const sortedItems = computed<T[]>(() => {
    const currentItems = typeof items === 'function' ? items() : items;
    let filteredItems: T[] = [...currentItems];
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase();
      filteredItems = filteredItems.filter((item) => item.name?.toLowerCase().includes(query));
    }

    switch (sortOption.value) {
      case 'recently_updated':
        return filteredItems.sort(
          (a, b) => new Date(b.updated_at || '').getTime() - new Date(a.updated_at || '').getTime()
        );
      case 'newest':
        return filteredItems.sort(
          (a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime()
        );
      case 'name':
        return filteredItems.sort((a, b) =>
          (a.name || '').localeCompare(b.name || '', ['ru', 'en'], { sensitivity: 'base' })
        );
      case 'recently_opened':
        if (!recentItems.value || recentItems.value.length === 0) {
          return [];
        }
        // Показываем только элементы из recentItems
        const recentIds = recentItems.value.map((item) => item.id);
        const recentFiltered = filteredItems.filter((item) => recentIds.includes(item.id));

        // Сортируем recent items по порядку в recentItems
        const sortedRecent = recentFiltered.sort((a, b) => {
          const aIndex = recentIds.indexOf(a.id);
          const bIndex = recentIds.indexOf(b.id);
          return aIndex - bIndex;
        });

        return sortedRecent;
      default:
        return filteredItems;
    }
  });

  return {
    sortOption,
    sortOptions,
    searchQuery,
    sortedItems,
    addRecentItem,
  };
}
