import { useVueFlow } from '@vue-flow/core';

/**
 * Управление камерой vueflow при переключении страниц
  * @returns cleanupOldCameraPositions - функция очистки старых позиций камеры
  * @returns saveCameraPosition - функция сохранения позиции камеры
  * @returns loadCameraPosition - функция загрузки позиции камеры
  * @returns initCameraTracking - функция инициализации отслеживания позиции камеры
  * @returns setupViewportTracking - функция настройки отслеживания для перезагрузки страницы
 */

const MAX_CAMERA_POSITIONS = 8;
const CAMERA_POSITIONS_KEY = 'vueflow_camera_positions';

export function useCameraPosition(botId: string) {
  const { getViewport, setViewport } = useVueFlow();

  // Получить все сохраненные позиции камеры
  const getAllCameraPositions = () => {
    const savedData = localStorage.getItem(CAMERA_POSITIONS_KEY);
    return savedData ? JSON.parse(savedData) : {};
  };

  // Очистить старые позиции камеры (оставить только 8 самых последних)
  const cleanupOldCameraPositions = () => {
    const allPositions = getAllCameraPositions();
    const entries = Object.entries(allPositions);
    
    if (entries.length <= MAX_CAMERA_POSITIONS) {
      return;
    }
    
    const sortedEntries = entries.sort((a, b) => ((b[1] as any).timestamp || 0) - ((a[1] as any).timestamp || 0));
    const limitedEntries = sortedEntries.slice(0, MAX_CAMERA_POSITIONS);
    const limitedPositions = Object.fromEntries(limitedEntries);
    
    localStorage.setItem(CAMERA_POSITIONS_KEY, JSON.stringify(limitedPositions));
  };

  // Сохранить позицию камеры
  const saveCameraPosition = () => {
    const viewportData = getViewport();
    const cameraData = {
      ...viewportData,
      botId: botId,
      timestamp: Date.now()
    };
    
    const allPositions = getAllCameraPositions();
    allPositions[botId] = cameraData;
    
    localStorage.setItem(CAMERA_POSITIONS_KEY, JSON.stringify(allPositions));
  };

  // Загрузить позицию камеры
  const loadCameraPosition = () => {
    const allPositions = getAllCameraPositions();
    const cameraData = allPositions[botId];
    
    if (cameraData && cameraData.botId === botId) {
      setViewport(cameraData, { duration: 0 });
    }
  };

  // Инициализия
  const initCameraTracking = () => {
    loadCameraPosition();
    cleanupOldCameraPositions();
  };

  // Настроить отслеживание для перезагрузки страницы
  const setupViewportTracking = () => {
    const handleBeforeUnload = () => {
      saveCameraPosition();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  };

  return {
    saveCameraPosition,
    loadCameraPosition,
    initCameraTracking,
    setupViewportTracking,
    cleanupOldCameraPositions
  };
}
