import type { Directive } from 'vue';

export interface CustomDirective {
  name: string;
  value: Directive;
}
