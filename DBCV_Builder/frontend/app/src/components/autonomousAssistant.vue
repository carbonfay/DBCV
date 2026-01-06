<template>
  <div class="mcp-assistant">
    <section class="panel">
      <div class="panel-header">
        <h3>Автоматическая генерация сценария</h3>
        <span class="status-pill" :class="generationStatus">{{ statusLabel }}</span>
      </div>

      <label class="field-label" for="prompt-input">Описание задачи</label>
      <textarea
        id="prompt-input"
        v-model="prompt"
        :disabled="isGenerating"
        rows="4"
        placeholder="Опиши, какие шаги нужно построить"
      ></textarea>

      <label class="field-label" for="context-input">Контекст (JSON, необязательно)</label>
      <textarea
        id="context-input"
        v-model="contextString"
        :disabled="isGenerating"
        rows="3"
        placeholder='{"session.telegram_chat_id": "123", "bot.news_api_key": "..."}'
      ></textarea>
      <p v-if="contextError" class="error-text">{{ contextError }}</p>

      <div class="actions">
        <button
          type="button"
          class="primary"
          :disabled="isGenerating || !prompt.trim()"
          @click="handlePlan"
        >
          <LoaderIcon v-if="planLoading" class="inline-spinner" />
          <span v-if="planLoading">Формируем план…</span>
          <span v-else>Сформировать план</span>
        </button>
        <button
          type="button"
          class="secondary"
          :disabled="isGenerating || !prompt.trim()"
          @click="handleGenerate"
        >
          <LoaderIcon v-if="isGenerating" class="inline-spinner" />
          <span v-if="isGenerating">Запуск…</span>
          <span v-else>Запустить генерацию</span>
        </button>
        <button type="button" class="ghost" :disabled="isGenerating" @click="resetAll">
          Сбросить
        </button>
      </div>
    </section>

    <section v-if="planLoading || plan || planError" class="panel">
      <div class="panel-header">
        <h4>Предварительный план</h4>
        <span v-if="plan" class="meta">Шагов: {{ planSteps.length }}</span>
      </div>

      <div v-if="planLoading" class="plan-loading">
        <LoaderIcon class="inline-spinner" />
        <span>Готовим последовательность действий…</span>
      </div>

      <div v-else-if="planError" class="error-card">{{ planError }}</div>

      <div v-else-if="plan">
        <div v-if="planSteps.length" class="plan-steps">
          <article v-for="(step, index) in planSteps" :key="index" class="plan-step">
            <header>
              <span class="badge">Шаг {{ index + 1 }}</span>
              <h5>{{ step.name }}</h5>
            </header>
            <p class="plan-text">{{ step.action }}</p>
            <ul v-if="step.required_data?.length" class="plan-list">
              <li v-for="item in step.required_data" :key="item">{{ item }}</li>
            </ul>
            <p v-if="step.notes" class="plan-notes">{{ step.notes }}</p>
          </article>
        </div>
        <p v-else class="empty-hint">План пуст — уточните запрос или контекст.</p>

        <div v-if="missingData.length" class="missing-block">
          <h5>Желательно уточнить:</h5>
          <div class="chip-list">
            <span v-for="item in missingData" :key="item" class="chip">{{ item }}</span>
          </div>
        </div>

        <div v-if="promptSuggestion" class="suggestion">
          <div class="suggestion-header">
            <h5>Предложенный промпт</h5>
            <div class="suggestion-actions">
              <button class="ghost" @click="applySuggestion">Вставить</button>
              <button class="ghost" @click="copyPromptSuggestion"><CopyIcon /></button>
            </div>
          </div>
          <textarea readonly rows="3">{{ promptSuggestion }}</textarea>
        </div>
      </div>
    </section>

    <section v-if="activeSession" class="panel">
      <div class="panel-header">
        <h4>Результат генерации</h4>
        <span class="meta">{{ activeSession?.completedAt ? formatDate(activeSession.completedAt) : 'в процессе' }}</span>
      </div>

      <div v-if="outputText" class="result-block">
        <div class="result-header">
          <span>Ответ ассистента</span>
          <button class="ghost" @click="copyOutput"><CopyIcon />Скопировать</button>
        </div>
        <pre>{{ outputText }}</pre>
      </div>

      <div v-if="toolHistory.length" class="tool-history">
        <h5>Вызовы инструментов</h5>
        <details v-for="(call, index) in toolHistory" :key="index" :open="index === toolHistory.length - 1">
          <summary>
            <span>{{ call.tool }}</span>
            <span :class="['tool-status', call.success ? 'success' : 'failed']">
              {{ call.success ? 'успех' : 'ошибка' }} · {{ formatDate(call.timestamp) }}
            </span>
          </summary>
          <div class="tool-block">
            <strong>Аргументы</strong>
            <pre>{{ pretty(call.arguments) }}</pre>
          </div>
          <div class="tool-block">
            <strong>Результат</strong>
            <pre>{{ pretty(call.result) }}</pre>
          </div>
        </details>
      </div>

      <div v-if="activeSession?.error" class="error-card">{{ activeSession.error }}</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { LoaderIcon, CopyIcon } from '@/components/icons';
import notyf from '@/plugins/notyf';
import { useAutonomousAssistantStore, type PlanResponse, type PlanStep } from '@/stores/autonomousAssistant';

type SessionStatus = 'idle' | 'generating' | 'completed' | 'error';

const props = defineProps<{ botId?: string }>();
const assistantStore = useAutonomousAssistantStore();

const prompt = ref('');
const contextString = ref('{}');
const contextError = ref('');

const plan = computed<PlanResponse | null>(() => assistantStore.plan);
const planLoading = computed(() => assistantStore.planLoading);
const planError = computed(() => assistantStore.planError);
const planSteps = computed<PlanStep[]>(() => plan.value?.steps ?? []);
const missingData = computed<string[]>(() => plan.value?.missing_data ?? []);
const promptSuggestion = computed(() => plan.value?.prompt_suggestion ?? '');

const currentSessionId = ref<string | null>(null);
const activeSession = computed(() => (currentSessionId.value ? assistantStore.getSession(currentSessionId.value) : undefined));
const isGenerating = computed(() => (currentSessionId.value ? assistantStore.isSessionActive(currentSessionId.value) : false));
const toolHistory = computed(() => (currentSessionId.value ? assistantStore.getToolHistory(currentSessionId.value) : []));
const outputText = computed(() => activeSession.value?.outputText ?? '');
const generationStatus = computed<SessionStatus>(() => activeSession.value?.status ?? 'idle');

const statusLabel = computed(() => {
  switch (generationStatus.value) {
    case 'generating':
      return 'в работе';
    case 'completed':
      return 'готово';
    case 'error':
      return 'ошибка';
    default:
      return 'ожидает';
  }
});

function parseContext(): any {
  contextError.value = '';
  const raw = contextString.value.trim();
  if (!raw) {
    return {};
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    contextError.value = 'Некорректный JSON';
    throw error;
  }
}

async function handlePlan(): Promise<void> {
  try {
    const ctx = parseContext();
    await assistantStore.generatePlan(prompt.value, props.botId, ctx);
    notyf.success('План обновлён');
  } catch (error: any) {
    if (contextError.value) {
      notyf.error('Исправьте JSON контекста');
    } else {
      notyf.error(error?.message || 'Не удалось построить план');
    }
  }
}

async function handleGenerate(): Promise<void> {
  try {
    const ctx = parseContext();
    if (!currentSessionId.value) {
      currentSessionId.value = assistantStore.createSession(props.botId ?? '', prompt.value, ctx);
    }
    await assistantStore.generateBot(currentSessionId.value, prompt.value, props.botId, ctx);
    notyf.success('Генерация завершена');
  } catch (error: any) {
    if (contextError.value) {
      notyf.error('Исправьте JSON контекста');
    } else {
      notyf.error(error?.message || 'Генерация завершилась с ошибкой');
    }
  }
}

function applySuggestion(): void {
  if (promptSuggestion.value) {
    prompt.value = promptSuggestion.value;
    notyf.success('Промпт обновлён из плана');
  }
}

async function copyPromptSuggestion(): Promise<void> {
  if (!promptSuggestion.value) {
    return;
  }
  try {
    await navigator.clipboard.writeText(promptSuggestion.value);
    notyf.success('Промпт скопирован');
  } catch {
    notyf.error('Не удалось скопировать текст');
  }
}

async function copyOutput(): Promise<void> {
  if (!outputText.value) {
    return;
  }
  try {
    await navigator.clipboard.writeText(outputText.value);
    notyf.success('Ответ скопирован');
  } catch {
    notyf.error('Не удалось скопировать текст');
  }
}

function resetAll(): void {
  prompt.value = '';
  contextString.value = '{}';
  contextError.value = '';
  assistantStore.clearPlan();
  if (currentSessionId.value) {
    assistantStore.removeSession(currentSessionId.value);
    currentSessionId.value = null;
  }
}

function formatDate(value: string): string {
  try {
    const date = new Date(value);
    return date.toLocaleString();
  } catch {
    return value;
  }
}

function pretty(value: any): string {
  return JSON.stringify(value, null, 2);
}
</script>

<style scoped>
.mcp-assistant {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: #0f0f10;
  color: #f5f5f5;
}

.panel {
  background: #18181a;
  border: 1px solid #29292e;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-header h3,
.panel-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.status-pill {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: #2c2c2f;
  color: #b0b0b5;
}

.status-pill.generating {
  background: #2f3a1d;
  color: #b0ffaa;
}

.status-pill.completed {
  background: #1d3a2f;
  color: #8bffd3;
}

.status-pill.error {
  background: #3a1d1d;
  color: #ff9a9a;
}

.field-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-top: 12px;
  margin-bottom: 6px;
  color: #cfcfd6;
}

textarea {
  width: 100%;
  background: #111113;
  border: 1px solid #2b2b30;
  border-radius: 8px;
  padding: 10px 12px;
  color: #f2f2f5;
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
}

textarea:focus {
  outline: none;
  border-color: #4d9eff;
  box-shadow: 0 0 0 1px #4d9eff33;
}

.error-text {
  margin: 4px 0 0;
  font-size: 12px;
  color: #ff8d8d;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.actions button {
  flex: 1 1 180px;
  padding: 10px 16px;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary {
  background: linear-gradient(135deg, #4d9eff, #3a78ff);
  color: #fff;
}

.primary:hover:not(:disabled) {
  transform: translateY(-1px);
}

.secondary {
  background: #24242a;
  color: #fff;
  border: 1px solid #3c3c43;
}

.secondary:hover:not(:disabled) {
  background: #2d2d34;
}

.ghost {
  background: transparent;
  border: 1px solid #3c3c43;
  color: #c1c1c9;
}

.inline-spinner {
  width: 16px;
  height: 16px;
}

.plan-loading,
.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #c1c1c9;
}

.plan-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-step {
  background: #111113;
  border: 1px solid #2a2a30;
  border-radius: 10px;
  padding: 14px;
}

.plan-step header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.plan-step h5 {
  margin: 0;
  font-size: 15px;
}

.badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: #2e2e34;
  font-size: 11px;
  color: #dcdce7;
}

.plan-text {
  margin: 0 0 6px;
  color: #d4d4e0;
}

.plan-list {
  margin: 0 0 6px;
  padding-left: 18px;
  color: #b6b6c5;
  font-size: 13px;
}

.plan-notes {
  margin: 0;
  font-size: 12px;
  color: #9fa0ad;
}

.empty-hint {
  margin: 0;
  color: #9fa0ad;
  font-size: 13px;
}

.missing-block {
  margin-top: 16px;
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 4px 10px;
  background: #202028;
  border-radius: 999px;
  font-size: 12px;
  color: #dcdde6;
}

.suggestion {
  margin-top: 16px;
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.suggestion-actions {
  display: flex;
  gap: 8px;
}

.meta {
  font-size: 12px;
  color: #8d8da1;
}

.result-block {
  margin-bottom: 16px;
}

.result-block pre,
.tool-block pre {
  background: #111113;
  border: 1px solid #2a2a30;
  border-radius: 8px;
  padding: 12px;
  color: #e5e5ef;
  font-size: 12px;
  overflow-x: auto;
}

.tool-history details {
  background: #111113;
  border: 1px solid #2a2a30;
  border-radius: 8px;
  margin-bottom: 8px;
  padding: 10px;
}

.tool-history summary {
  display: flex;
  justify-content: space-between;
  cursor: pointer;
  color: #d4d4e0;
}

.tool-status.success {
  color: #6dd9a8;
}

.tool-status.failed {
  color: #ff8d8d;
}

.error-card {
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  background: #2a1c1c;
  border: 1px solid #a14444;
  color: #ffb3b3;
  font-size: 13px;
}
</style>
