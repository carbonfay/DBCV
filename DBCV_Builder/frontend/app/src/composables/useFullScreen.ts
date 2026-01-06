import { ref } from 'vue';

/**
 * Управление полноэкранным режимом модального окна
 * @returns isFullScreen - текущее состояние полноэкранного режима
 * @returns toggleFullScreen - функция переключения полноэкранного режима
 * @returns resetFullScreen - функция сброса полноэкранного режима
 */

export function useFullScreen() {
  const isFullScreen = ref(false);

  const toggleFullScreen = (): void => {
    isFullScreen.value = !isFullScreen.value;

    if (isFullScreen.value) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  };

  const resetFullScreen = (): void => {
    if (isFullScreen.value) {
      isFullScreen.value = false;
      document.body.style.overflow = '';
    }
  };

  return {
    isFullScreen,
    toggleFullScreen,
    resetFullScreen,
  };
}
