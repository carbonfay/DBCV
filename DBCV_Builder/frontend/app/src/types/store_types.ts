export interface User {
  id: string;
  email?: string;
  username?: string;
  is_active?: boolean;
  first_name?: string | null;
  last_name?: string | null;
  role?: string | number;
  type?: string;
}

export interface Channel {
  id: string;
  created_at?: string | null;
  updated_at?: string | null;
  name: string;
  description?: string;
  is_public?: boolean;
  default_bot_id?: string | null;
  owner_id?: string | null;
  owner?: User | null;
  default_bot?: Bot | null;
  subscribers?: User[];
  variables?: Record<string, unknown>;
}

export interface Bot {
  id: string;
  type?: string;
  name?: string;
  description?: string;
  created_at?: string | null;
  updated_at?: string | null;
  config?: Record<string, unknown> | string | null;
  owner_id?: string | null;
  first_step_id?: string | null;
  variables?: BotVariables | null;
  owner?: User;
  first_step?: Step | null;
  steps?: Step[];
  emitters?: Emitter[];
  master_connection_groups?: ConnectionGroup[];
  notes?: Note[];
  channels?: Channel[];
}

export interface BotVariables {
  data?: Record<string, unknown>;
}

export interface Message {
  id: string;
  created_at?: string | null;
  updated_at?: string | null;
  text?: string | null;
  params?: Record<string, unknown> | null;
  recipient_id?: string | null;
  sender_id?: string | null;
  widget_id?: string | null;
  channel_id?: string | null;
  widget?: Widget | null;
  attachments?: any[];
  recipient?: User | null;
  sender?: User | null;
}

export interface Step {
  id: string;
  name?: string;
  description?: string | null;
  timeout_after?: number | null;
  bot_id?: string;
  template_instance_id?: string | null;
  message?: Message | null;
  connection_groups?: ConnectionGroup[];
  pos_x?: number;
  pos_y?: number;
  is_proxy?: boolean;
  template_instance?: TemplateInstance | null;
}

export interface Widget {
  id: string;
  name: string;
  description?: string;
  created_at?: string | null;
  updated_at?: string | null;
  js?: string;
  css?: string;
  body?: string;
  bots?: Bot[];
}

export interface Note {
  id: string;
  created_at?: string | null;
  updated_at?: string | null;
  pos_x?: number;
  pos_y?: number;
  text?: string;
  bot_id?: string;
  step_id?: string | null;
}

export interface Request {
  id: string;
  name: string;
  request_url: string;
  method: string;
  created_at?: string | null;
  updated_at?: string | null;
  content?: string | null;
  params?: Record<string, unknown> | null;
  data?: Record<string, unknown> | null;
  json_field?: Record<string, unknown> | null;
  headers?: string | null;
  url_params?: Record<string, unknown> | null;
  attachments?: string | null;
  proxies?: string | null;
  owner_id?: string | null;
  owner?: User | null;
  bots?: Bot[];
}

export interface RequestExecuteResponse {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  data: unknown;
  responseTime: number;
  success: boolean;
  error?: string;
}

export interface Connection {
  id: string;
  priority?: number;
  next_step_id?: string;
  rules?: Record<string, unknown> | string | null;
  filters?: Record<string, unknown> | string | null;
  group_id?: string;
  next_step?: Step | null;
}

export interface ConnectionGroup {
  id: string;
  search_type?: string;
  priority?: number;
  code?: string | null;
  variables?: string | null;
  request_id?: string | null;
  step_id?: string | null;
  bot_id?: string | null;
  request?: Request | null;
  connections?: Connection[];
}

export interface Emitter {
  id: string;
  name?: string;
  created_at?: string | null;
  updated_at?: string | null;
  bot_id?: string;
  pos_x?: number;
  pos_y?: number;
  is_active?: boolean | null;
  needs_message_processing?: boolean;
  message_id?: string | null;
  cron_id?: string | null;
  job_id?: string | null;
  cron?: Cron;
  message?: Message;
}

export interface Cron {
  id: string;
  name?: string;
  year?: string | number | null;
  month?: string | number | null;
  day?: string | number | null;
  day_of_week?: string | number | null;
  hour?: string | number | null;
  minute?: string | number | null;
  second?: string | number | null;
}

export interface Template {
  id: string;
  name?: string;
  description?: string | null;
  first_step_id?: string;
  steps?: Step[];
  variables?: Record<string, unknown>;
  inputs?: Record<string, unknown>;
  outputs?: Record<string, unknown>;
  bot_id?: string | null;
  group?: Record<string, unknown>;
}

export interface TemplateGroups {
  id: string;
  name: string;
  description: string;
  owner: Record<string, unknown>;
  templates: Template[];
}

export interface TemplateInstance {
  id: string;
  name?: string;
  description?: string | null;
  first_step_id?: string;
  steps?: Step[];
  variables?: Record<string, unknown>;
  inputs_mapping?: Record<string, unknown>;
  outputs_mapping?: Record<string, unknown>;
}

export interface Credential {
  id: string;
  bot_id: string;
  name: string;
  is_default: boolean;
  provider: string;
  strategy: string;
  scopes: string[];
  payload: Record<string, unknown>;
}