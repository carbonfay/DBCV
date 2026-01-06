/**
 * Обновляет элемент в массиве по id
 * @param array - массив элементов
 * @param id - id элемента для обновления
 * @param newData - новые данные элемента
 * @returns обновленный массив
 */

export function updateValueByIndex<T extends { id: string }>(
  array: T[],
  id: string,
  newData: T
): T[] {
  const index = array.findIndex((item) => item.id === id);
  if (index !== -1) {
    array[index] = newData;
  }
  return array;
}
