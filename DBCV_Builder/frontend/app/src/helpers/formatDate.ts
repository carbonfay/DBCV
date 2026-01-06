import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

/**
 * Функция принимает строку даты и возвращает читаемое представление времени, прошедшего с момента указанной даты (например: "2 часа назад")
 *
 * @param dateString - Строка даты с бэкенда
 * @returns Отформатированная строка
 *
 * @note
 * - Функция автоматически конвертирует UTC время в локальное время пользователя
 * - Использует русский язык для вывода
 */

export const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '';

  const utcDate = new Date(dateString);
  const localDate = new Date(utcDate.getTime() - utcDate.getTimezoneOffset() * 60000);

  return formatDistanceToNow(localDate, { locale: ru, addSuffix: true });
};
