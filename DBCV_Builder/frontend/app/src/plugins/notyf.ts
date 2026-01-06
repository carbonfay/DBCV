import { Notyf } from 'notyf';
import 'notyf/notyf.min.css';
import '@/assets/styles/notyf.css';

const notyf = new Notyf({
  duration: 3000,
  position: {
    x: 'right',
    y: 'top',
  },
  types: [
    {
      type: 'success',
      background: '#4caf50',
      icon: false,
    },
    {
      type: 'error',
      background: '#f44336',
      icon: false,
    },
  ],
});

export default notyf;
