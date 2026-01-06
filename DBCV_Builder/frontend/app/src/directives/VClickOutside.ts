import type { CustomDirective } from '@/types/types';

const VClickOutside: CustomDirective = {
  name: 'click-outside',
  value: {
    mounted(element, { value }) {
      element.clickOutside = function (event: Event) {
        if (!(element == event.target || element.contains(event.target))) {
          value(event);
        }
      };

      document.body.addEventListener('click', element.clickOutside);
    },
    unmounted(element, { value }) {
      document.body.removeEventListener('click', element.clickOutside);
    },
  },
};

export default VClickOutside;
