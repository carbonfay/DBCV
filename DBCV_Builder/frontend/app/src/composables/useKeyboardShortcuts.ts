import { onMounted, onBeforeUnmount } from 'vue';

interface KeyboardShortcutsOptions {
  onEscape?: () => void;
  onSave?: () => Promise<void> | void;
}

export function useKeyboardShortcuts(options: KeyboardShortcutsOptions) {
  const handleKeyDown = async (e: KeyboardEvent): Promise<void> => {
    // Escape - закрытие/отмена
    if (e.key === 'Escape') {
      e.preventDefault();
      options.onEscape?.();
    }
    // Ctrl/Cmd + S - сохранение
    else if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'ы')) {
      e.preventDefault();
      if (options.onSave) {
        await options.onSave();
      }
    }
  };

  // Добавляем слушателя нажатий клавиш при монтировании компонента
  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown);
  });

  // Удаляем слушателя нажатий клавиш при размонтировании компонента
  onBeforeUnmount(() => {
    window.removeEventListener('keydown', handleKeyDown);
  });

  return {
    handleKeyDown,
  };
}
