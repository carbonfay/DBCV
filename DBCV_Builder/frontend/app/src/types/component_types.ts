import type { Request, Widget, Bot, Channel } from '@/types/store_types';

export interface Option {
  value: string | number;
  label: string;
}

export interface Tab {
  name: string;
  label: string;
}

// Реквесты
export const defaultRequest = {
  name: '',
  request_url: '',
  method: 'get',
  content: null,
  headers: null,
  attachments: null,
  proxies: null,
  json_field: null,
  params: null,
  data: null,
  url_params: null,
};

export type RequestFormData = Omit<Request, 'id' | 'created_at' | 'updated_at'>;

// Виджеты
export const defaultWidget = {
  name: '',
  description: '',
  js: '',
  css: '',
  body: '',
};

export type WidgetFormData = Omit<Widget, 'id' | 'created_at' | 'updated_at'>;

// Боты
export type BotFormData = Pick<Bot, 'name' | 'description'>;

export const defaultBot = {
  name: '',
  description: '',
};

// Каналы
export const defaultChannel = {
  name: '',
  description: '',
  is_public: true,
  default_bot_id: null,
  variables: '{}',
  subscribers: [],
};

export type ChannelFormData = Omit<
  Channel,
  'id' | 'created_at' | 'updated_at' | 'owner_id' | 'owner' | 'default_bot' | 'variables'
> & {
  variables: string | null;
};
