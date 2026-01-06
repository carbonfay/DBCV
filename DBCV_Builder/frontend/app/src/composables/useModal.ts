import { ref } from 'vue';

export function useModal() {
  const isModalOpen = ref(false);
  const isEditMode = ref(false);

  const openModal = (): void => {
    isModalOpen.value = true;
    isEditMode.value = false;
  };

  const closeModal = (): void => {
    isModalOpen.value = false;
    isEditMode.value = false;
  };

  const openEditModal = (): void => {
    isModalOpen.value = true;
    isEditMode.value = true;
  };

  return {
    isModalOpen,
    isEditMode,
    openModal,
    closeModal,
    openEditModal,
  };
}
