<template>
  <div :class="['chat-container', { fullscreen: isFullscreen }]">
    <div class="chat-header">
      <h2>{{ channel?.name }}</h2>
      <div v-if="showActions" class="header-actions">
        <button @click="handleEditChannel">
          <EditIcon class="icon edit-icon" />
        </button>
        <button @click="toggleFullscreen">
          <span v-if="isFullscreen">
            <SmallScreenIcon />
          </span>
          <span v-else>
            <FullScreenIcon />
          </span>
        </button>
        <button @click="closeChat">
          <CloseIcon />
        </button>
      </div>
    </div>

    <div ref="messagesContainer" class="messages" @scroll="handleScroll">
      <BaseButton
        v-if="hasMoreMessages"
        class="btn-show-more"
        size="small"
        styleType="secondary"
        @click="loadMoreMessages"
      >
        Показать еще
      </BaseButton>
      <div
        v-for="(message, index) in visibleMessages"
        :key="message.id"
        :class="['message', message.sender_id === userId ? 'message-sender' : 'message-receiver']"
      >
        <span class="message-author" @click="toggleMessage(message.id)">
          {{ message.sender_id === userId ? '' : message.sender?.name }}
        </span>
        <span
          v-if="message.sender_id != userId || message.recipient != null"
          class="message-history"
        >
          {{ senderName(message) }} > {{ recipientName(message) }}
        </span>
        <div class="message-body" @click="toggleMessage(message.id)">
          <span>{{ message.text }}</span>
        </div>
        <div v-if="message.widget" class="widget-banner">
          <p><strong>Виджет</strong></p>
          <p>{{ message.widget.name || '—' }}</p>
          <p style="margin-top: 10px">
            <strong>ID:</strong>
            {{ message.widget.id || '—' }}
          </p>
        </div>
        <span class="message-time">{{ formatTime(message.created_at) }}</span>

        <div v-if="expandedMessageId === message.id" class="message-details">
          <p>
            <strong>Отправитель:</strong>
            {{ message.sender_id || '—' }}
          </p>
          <p>
            <strong>Получатель:</strong>
            {{ message.recipient_id || '—' }}
          </p>
          <div
            v-if="message.params && Object.keys(message.params).length > 0"
            class="message-details-params"
          >
            <p><strong>Параметры:</strong></p>
            <ul>
              <li v-for="(value, key) in message.params" :key="key">{{ key }}: {{ value }}</li>
            </ul>
          </div>
          <div v-if="message.widget">
            <p style="text-decoration: underline"><strong>Информация о виджете</strong></p>
            <p>
              <strong>Название:</strong>
              {{ message.widget.name || '—' }}
            </p>
            <p>
              <strong>ID виджета:</strong>
              {{ message.widget.id || '—' }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Кнопка прокрутки вниз -->
    <div v-if="showScrollToBottom" class="scroll-to-bottom-button" @click="scrollToBottom">
      <BottomArrowIcon />
      <span v-if="unreadMessagesCount > 0" class="unread-indicator">{{ unreadMessagesCount }}</span>
    </div>

    <div class="input-container">
      <input
        v-model="newMessageText"
        placeholder="Введите сообщение..."
        type="text"
        @keyup.enter="sendMessage"
      />
      <BaseButton size="small" styleType="secondary" class="send-button" @click="sendMessage">
        Отправить
      </BaseButton>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useChannelsStore, useMessagesStore, useUsersStore, useAuthStore } from '@/stores';
import {
  BottomArrowIcon,
  CloseIcon,
  FullScreenIcon,
  SmallScreenIcon,
  EditIcon,
} from '@/components/icons';

const props = defineProps({
  channel: {
    type: Object,
    required: true,
  },
  showActions: {
    type: Boolean,
    default: true,
  },
});
const limit = ref(30);
const skip = ref(0);

const messagesStore = useMessagesStore();
const channelsStore = useChannelsStore();
const usersStore = useUsersStore();
const authStore = useAuthStore();

const channelId = ref(props.channel.id);

const socket = ref(null);
const currentUser = ref(null);
const messages = ref([]);
const newMessageText = ref('');
const messagesContainer = ref(null);
const expandedMessageId = ref(null);

const showScrollToBottom = ref(false); // Показывать ли кнопку прокрутки
const unreadMessagesCount = ref(0); // Счетчик новых сообщений
const isNearBottom = ref(true);

const userId = computed(() => usersStore.currentUser?.id);

const visibleMessages = computed(() => {
  return messages.value;
});

const hasMoreMessages = computed(() => {
  const lastBatchSize = messages.value.length % limit.value;
  return lastBatchSize === 0 || messages.value.length === 0;
});

// Текущий пользователь
const loadCurrentUser = async () => {
  await usersStore.readCurrentUser();
  currentUser.value = usersStore.currentUser;
};

// Загрузка сообщений канала
const loadMessages = async () => {
  const response = await channelsStore.fetchMessagesByChannel(
    channelId.value,
    skip.value,
    limit.value
  );

  const fetchedMessages = response?.data || [];

  if (Array.isArray(fetchedMessages)) {
    messages.value = [...fetchedMessages, ...messages.value];
    skip.value += limit.value;
  } else {
    console.error('fetchMessagesByChannel вернул не массив:', fetchedMessages);
  }
};

const loadMoreMessages = async () => {
  const previousScrollHeight = messagesContainer.value.scrollHeight;
  const previousScrollTop = messagesContainer.value.scrollTop;
  const distanceFromBottom = previousScrollHeight - previousScrollTop;
  await loadMessages();
  nextTick(() => {
    const newScrollHeight = messagesContainer.value.scrollHeight;
    const newScrollTop = newScrollHeight - distanceFromBottom;
    messagesContainer.value.scrollTop = newScrollTop;
  });
};

// Имена отправителя/получателя
const getDisplayName = (entity) => {
  if (!entity) return 'Неизвестный тип';
  switch (entity.type) {
    case 'bot':
      return entity.name;
    case 'user':
      return entity.username;
    case 'anonymous_user':
      return entity.type;
    default:
      return 'Неизвестный тип';
  }
};

const senderName = (message) => getDisplayName(message.sender);
const recipientName = (message) => getDisplayName(message.recipient);

// Подписка на новые сообщения
const subscribeToChannel = () => {
  try {
    const accessToken = authStore.accessToken;
    if (!accessToken) {
      console.error('Токен доступа отсутствует');
      return;
    }

    const socketUrl = channelsStore.getWebSocketUrl(props.channel.id, accessToken);
    socket.value = new WebSocket(socketUrl);

    socket.value.onmessage = (event) => {
      let rawMessage = JSON.parse(event.data);

      const isDuplicate = messages.value.some((msg) => msg.id === rawMessage.id);
      if (isDuplicate) {
        return;
      }
      messages.value.push(rawMessage);

      nextTick(() => {
        const isNotCurrentUserMessage = rawMessage.sender_id !== userId.value;
        if (isNearBottom.value) {
          scrollToBottom();
        } else if (isNotCurrentUserMessage) {
          unreadMessagesCount.value++;
        }
      });
    };

    socket.value.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.value.onclose = () => {
      console.log('WebSocket connection closed');
    };
  } catch (error) {
    console.error('Ошибка при установке WebSocket соединения:', error);
  }
};

// Отправка нового сообщения
const sendMessage = async () => {
  if (!newMessageText.value.trim()) return;

  try {
    const newMessage = await messagesStore.sendMessage(newMessageText.value, channelId.value);
    newMessageText.value = '';

    nextTick(() => {
      scrollToBottom();
    });
  } catch (error) {
    console.error('Ошибка отправки сообщения:', error);
  }
};

const formatTime = (timestamp) => {
  if (!timestamp.endsWith('Z')) {
    timestamp += 'Z';
  }

  const date = new Date(timestamp);

  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
};

const handleScroll = () => {
  if (messagesContainer.value) {
    const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value;
    const threshold = 100;
    isNearBottom.value = scrollHeight - (scrollTop + clientHeight) <= threshold;

    if (isNearBottom.value) {
      unreadMessagesCount.value = 0;
    }

    showScrollToBottom.value = !isNearBottom.value;
  }
};

// Прокрутка вниз
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    unreadMessagesCount.value = 0;
    isNearBottom.value = true;
  }
};

// Переключение развернутого состояния сообщения
const toggleMessage = (messageId) => {
  if (expandedMessageId.value === messageId) {
    expandedMessageId.value = null;
  } else {
    expandedMessageId.value = messageId;
  }
};

// Кнопки закрытия / развернуть / свернуть
const isFullscreen = ref(false);

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

const emit = defineEmits(['close', 'edit']);

const closeChat = () => {
  emit('close');
};

const handleEditChannel = () => {
  emit('edit', props.channel);
};

const initChat = async () => {
  messages.value = [];
  skip.value = 0;
  newMessageText.value = '';
  expandedMessageId.value = null;
  showScrollToBottom.value = false;
  unreadMessagesCount.value = 0;
  isNearBottom.value = true;

  channelId.value = props.channel.id;

  await loadCurrentUser();
  await loadMessages();

  nextTick(() => {
    scrollToBottom();
  });

  subscribeToChannel();
};

watch(
  () => props.channel,
  (newChannel, oldChannel) => {
    if (newChannel && newChannel.id !== oldChannel?.id) {
      initChat();
    }
  },
  { deep: true }
);

onMounted(async () => {
  await loadCurrentUser();
  await loadMessages();
  nextTick(() => {
    scrollToBottom();
  });
  subscribeToChannel();
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.close();
  }
});
</script>

<style scoped>
h2 {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  padding: 0;
  color: #fff;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100vh;
  position: sticky;
  top: 0;
  padding: 20px;
  border-left: 1px solid rgba(116, 116, 116, 1);
  background: rgba(49, 49, 49, 1);
  transition: all 0.3s ease;
}

.chat-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1000;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-header .header-actions {
  display: flex;
  gap: 15px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  margin: 10px 0;
  scrollbar-width: none;
}

.messages::-webkit-scrollbar {
  display: none;
}

.message {
  padding: 10px;
  border-radius: 8px;
  margin: 10px 0;
  word-wrap: break-word;
  border-radius: 20px;
  border: 2px solid rgba(227, 227, 227, 1);
  display: flex;
  flex-direction: column;
  max-width: 75%;
}

.message-receiver {
  background-color: rgba(255, 255, 255, 1);
}

.message-sender {
  background-color: rgba(217, 217, 217, 1);
  margin-left: auto;
  width: fit-content;
  min-width: 30%;
}

.message-author {
  color: rgb(115, 115, 115);
  font-size: 12px;
  font-weight: 800;
  line-height: 15px;
  text-transform: uppercase;
  cursor: pointer;
}

.message-history {
  margin: 0 0 10px;
  font-size: 12px;
  color: #979696;
}

.message-body span {
  color: rgb(0, 0, 0);
  font-size: 18px;
  font-weight: 400;
  line-height: 1.1;
}

.message-time {
  color: rgb(140, 140, 140);
  font-size: 10px;
  font-weight: 700;
  line-height: 12px;
  text-transform: uppercase;
  align-self: flex-end;
  margin: 10px 0 0;
}

.widget-banner {
  border: 1px solid rgb(217, 217, 217);
  border-radius: 8px;
  margin: 10px 0 0;
  padding: 20px;
}

.widget-banner * {
  color: #000;
  font-size: 14px;
}

.message-details {
  margin-top: 10px;
  padding: 10px;
  background-color: #f9f9f9;
  border: 1px solid rgb(217, 217, 217);
  border-radius: 8px;
}

.message-details * {
  color: #525252;
  font-size: 16px;
}

.message-details .message-details-params {
  margin: 10px 0;
}

.input-container {
  width: 100%;
  border: 1px solid rgb(217, 217, 217);
  border-radius: 8px;
  background: rgb(255, 255, 255);
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  gap: 15px;
}

.input-container input {
  width: 100%;
  border: 0;
  color: #000000;
  background: #fff;
}

.btn-show-more {
  margin: 0 auto;
  display: flex;
  margin-bottom: 20px;
}

.scroll-to-bottom-button {
  position: absolute;
  bottom: 85px;
  right: 20px;
  background-color: #fff;
  border: 1px solid rgba(49, 49, 49, 1);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.unread-indicator {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: red;
  color: white;
  font-size: 12px;
  font-weight: bold;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 1.5s infinite;
}
.send-button:hover {
  opacity: 0.95;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7);
  }

  70% {
    transform: scale(1.2);
    box-shadow: 0 0 0 10px rgba(255, 0, 0, 0);
  }

  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 0, 0, 0);
  }
}
</style>
