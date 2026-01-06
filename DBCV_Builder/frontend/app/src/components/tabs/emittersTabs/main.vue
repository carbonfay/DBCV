<template>
  <BaseCopyableId :id="props.node.id" style="margin-bottom: 10px" />
  <div class="emitter-settings">
    <BaseInput
      v-model="name"
      :label="'Название эмиттера'"
      :labelColor="'rgb(30, 30, 30)'"
      @input="isSomethingChanged = true"
    />
    <BaseSelectSearch
      v-model="selectedCronValue"
      :options="crons"
      label="Частота запуска"
      @update:model-value="handleCronChange"
      @input="isSomethingChanged = true"
    />

    <div>
      <BaseInput
        v-model="cronFields.name"
        :label="'Название крона'"
        :labelColor="'rgb(30, 30, 30)'"
        v-if="isAdvancedCron"
        class="cron-name"
        @input="isSomethingChanged = true"
      />
      <div class="cron-fields">
        <BaseInput
          v-model="cronFields.year"
          :label="'Год'"
          :labelColor="'rgb(30, 30, 30)'"
          :disabled="!isAdvancedCron"
          @input="isSomethingChanged = true"
        />
        <BaseInput
          v-model="cronFields.month"
          :label="'Месяц'"
          :labelColor="'rgb(30, 30, 30)'"
          :disabled="!isAdvancedCron"
          @input="isSomethingChanged = true"
        />
        <BaseInput
          v-model="cronFields.day"
          :label="'День'"
          :labelColor="'rgb(30, 30, 30)'"
          :disabled="!isAdvancedCron"
          @input="isSomethingChanged = true"
        />
        <BaseInput
          v-model="cronFields.day_of_week"
          :label="'День недели'"
          :labelColor="'rgb(30, 30, 30)'"
          :disabled="!isAdvancedCron"
          @input="isSomethingChanged = true"
        />
        <BaseInput
          v-model="cronFields.hour"
          :label="'Час'"
          :labelColor="'rgb(30, 30, 30)'"
          :disabled="!isAdvancedCron"
          @input="isSomethingChanged = true"
        />
        <BaseInput
          v-model="cronFields.minute"
          :label="'Минута'"
          :labelColor="'rgb(30, 30, 30)'"
          :disabled="!isAdvancedCron"
          @input="isSomethingChanged = true"
        />
        <BaseInput
          v-model="cronFields.second"
          :label="'Секунда'"
          :labelColor="'rgb(30, 30, 30)'"
          :disabled="!isAdvancedCron"
          @input="isSomethingChanged = true"
        />
        <button
          v-if="!isActive"
          class="control-btn play"
          @click="toggleActive(true)"
          :disabled="!props.node.data.cron_id || !props.node.data.message_id"
        >
          <PlayIcon class="icon control-icon play-icon" />
          пуск
        </button>
        <button
          v-else
          class="control-btn stop"
          @click="toggleActive(false)"
          :disabled="!props.node.data.cron_id || !props.node.data.message_id"
        >
          <StopIconBlack class="icon control-icon stop-icon" />
          стоп
        </button>
      </div>
    </div>
    <BaseCheckbox
      v-model="needsMessageProcessing"
      class="section-checkbox"
      @input="isSomethingChanged = true"
    >
      Проверять сообщение
    </BaseCheckbox>

    <div class="btns-block">
      <BaseButton styleType="secondary" size="small" @click="save" class="save">
        Сохранить
      </BaseButton>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watchEffect } from 'vue';
import { useCronsStore } from '@/stores'; // импорт сторов
import { PlayIcon, StopIconBlack } from '@/components/icons'; // импорт иконок
import notyf from '@/plugins/notyf';

const isSomethingChanged = ref(false);

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['update-node']);
const cronsStore = useCronsStore();

const name = ref(props.node.data.name);
const isActive = ref(props.node.data.is_active || false);
const needsMessageProcessing = ref(props.node.data.needs_message_processing);
const selectedCronValue = ref(null);
const isAdvancedCron = ref(false);
watchEffect(() => (isActive.value = props.node.data.is_active));

const resetCronFields = () => ({
  name: '',
  year: '*',
  month: '*',
  day: '*',
  day_of_week: '*',
  hour: '*',
  minute: '*',
  second: '*',
});

const cronFields = reactive(resetCronFields());

const crons = ref([{ value: 'advanced', label: 'Расширенный' }]);

(async () => {
  const loadedCrons = await cronsStore.readCrons();
  const formattedCrons = loadedCrons.map((cron) => ({
    value: cron.id.toString(),
    label: cron.name,
    ...cron,
  }));
  crons.value = [{ value: 'advanced', label: 'Расширенный' }, ...formattedCrons];

  if (props.node.data.cron_id !== undefined && props.node.data.cron_id !== null) {
    selectedCronValue.value = props.node.data.cron_id.toString();
    handleCronChange();
  }
})();

// Логика изменения cron
const handleCronChange = () => {
  if (selectedCronValue.value === 'advanced') {
    isAdvancedCron.value = true;
    Object.assign(cronFields, resetCronFields());
  } else {
    isAdvancedCron.value = false;
    const selectedCronData = crons.value.find((cron) => cron.value === selectedCronValue.value);
    if (selectedCronData) {
      Object.assign(cronFields, {
        name: selectedCronData.name,
        year: selectedCronData.year,
        month: selectedCronData.month,
        day: selectedCronData.day,
        day_of_week: selectedCronData.day_of_week,
        hour: selectedCronData.hour,
        minute: selectedCronData.minute,
        second: selectedCronData.second,
      });
    }
  }
};

const toggleActive = async (newState) => {
  isActive.value = newState;
  await save();
  notyf.success(newState ? 'Запущено!' : 'Остановлено!');
};

// Сохранение данных
const save = async () => {
  let cronId = null;

  if (selectedCronValue.value === 'advanced') {
    if (!cronFields.name || cronFields.name.trim() === '') {
      notyf.error('Название не может быть пустым!');
      return;
    }
    const newCron = await cronsStore.createCron({ ...cronFields });
    cronId = newCron.id;
  } else if (selectedCronValue.value) {
    cronId = selectedCronValue.value;
  }

  const data = {
    type: 'emitter',
    id: props.node.id,
    name: name.value,
    is_active: isActive.value,
    needs_message_processing: needsMessageProcessing.value,
  };

  if (cronId) {
    data.cron_id = cronId;
  }

  if (selectedCronValue.value) {
    const selectedCron = crons.value.find((cron) => cron.value === selectedCronValue.value);
    if (selectedCron) {
      data.cron_name = selectedCron.label;
    }
  }

  notyf.success('Сохранено!');
  isSomethingChanged.value = false;
  emit('update-node', data);
};

defineExpose({ isSomethingChanged, save });
</script>

<style scoped>
.emitter-settings {
  box-sizing: border-box;
  border: 2px solid rgb(227, 227, 227);
  border-radius: 10px;
  background: rgb(255, 255, 255);
  padding: 10px 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cron-fields {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.cron-name {
  margin-bottom: 10px;
}

.save {
  align-self: flex-end;
}

.btns-block {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.control-btn {
  width: 100%;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: end;
  border-radius: 6px;
  line-height: 1;
}

.control-btn:disabled {
  background-color: rgb(167 104 115);
  cursor: not-allowed;
}

.play {
  background: rgb(188, 46, 72);
}

.stop {
  border: 1px solid rgb(217, 217, 217);
  color: rgb(0, 0, 0);
}

.icon {
  height: 16px;
  width: auto;
  margin-right: 10px;
  stroke: #000000;
}

.icon.control-icon.play-icon {
  height: 12px;
  stroke: #ffffff;
}

.icon.control-icon.stop-icon {
  height: 14px;
}
</style>
