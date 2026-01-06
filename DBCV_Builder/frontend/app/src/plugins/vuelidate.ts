import { required, minLength, maxLength, email, helpers } from '@vuelidate/validators';

const requiredRu = helpers.withMessage('Это поле обязательно для заполнения', required);
const emailRu = helpers.withMessage('Неверный формат email', email);
const minLengthRu = (min: number) =>
  helpers.withMessage(`Минимальная длина ${min} символов`, minLength(min));
const maxLengthRu = (max: number) =>
  helpers.withMessage(`Максимальная длина ${max} символов`, maxLength(max));

export const loginRules = {
  username: {
    required: requiredRu,
    minLength: minLengthRu(3),
    maxLength: maxLengthRu(50),
  },
  password: {
    required: requiredRu,
    minLength: minLengthRu(6),
    maxLength: maxLengthRu(100),
  },
};

export const emailRules = {
  email: {
    required: requiredRu,
    email: emailRu,
  },
};

export const requestRules = {
  name: {
    required: requiredRu,
    minLength: minLengthRu(1),
    maxLength: maxLengthRu(100),
  },
  method: {
    required: requiredRu,
  },
  request_url: {
    required: requiredRu,
    minLength: minLengthRu(1),
  },
};

export const botRules = {
  name: {
    required: requiredRu,
    minLength: minLengthRu(1),
    maxLength: maxLengthRu(100),
  },
};

export const channelRules = {
  name: {
    required: requiredRu,
    minLength: minLengthRu(1),
    maxLength: maxLengthRu(100),
  },
};

export const widgetRules = {
  name: {
    required: requiredRu,
    minLength: minLengthRu(1),
    maxLength: maxLengthRu(100),
  },
};

export const credentialRules = {
  name: {
    required: requiredRu,
    minLength: minLengthRu(1),
    maxLength: maxLengthRu(100),
  },
  provider: {
    required: requiredRu,
  },
  strategy: {
    required: requiredRu,
  },
  payload: {
    required: requiredRu,
  },
};