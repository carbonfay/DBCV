// Сохраняем текущий выбранный channelId и WebSocket соединение
let selectedChannelId = null;
let socket = null;
let messagePollingInterval = null;
const myHeaders = new Headers();
myHeaders.append("Accept", "application/json");

// Функция выхода из аккаунта
async function logout() {
    try {
        const response = await fetch('/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });

        if (response.ok) {
            window.location.href = '/auth';
        } else {
            console.error('Ошибка при выходе');
        }
    } catch (error) {
        console.error('Ошибка при выполнении запроса:', error);
    }
}

// Функция выбора канала
async function selectChannel(channelId, channelName, event) {
    selectedChannelId = channelId;

    document.getElementById('chatHeader').innerHTML = `<span>Чат с ${channelName}</span><button class="logout-button" id="logoutButton">Выход</button>`;
    document.getElementById('messageInput').disabled = false;
    document.getElementById('sendButton').disabled = false;
    document.getElementById('input-area').classList.remove("hidden");


    document.querySelectorAll('.channel').forEach(item => item.classList.remove('active'));
    event.target.classList.add('active');

    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';
    messagesContainer.style.display = 'block';

    document.getElementById('logoutButton').onclick = logout;
    await loadMessages(channelId);
    connectWebSocket();
    startMessagePolling(channelId);
}

// Загрузка сообщений
async function loadMessages(channelId) {
    try {
        const response = await fetch(`/api/v1/channels/${channelId}/messages`, {
                method: 'GET',
                headers: myHeaders,
            });
        const messages = await response.json();
        const messagesContainer = document.getElementById('messages');
        messagesContainer.innerHTML = messages.map(message =>
            createMessageElement(message)
        ).join('');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

    } catch (error) {
        console.error('Ошибка загрузки сообщений:', error);
    }
}

// Подключение WebSocket
function connectWebSocket() {
    if (socket) socket.close();

    socket = new WebSocket(`ws://${window.location.host}/api/v1/ws/${currentUserId}`);

    socket.onopen = () => console.log('WebSocket соединение установлено');

    socket.onmessage = (event) => {
        const incomingMessage = JSON.parse(event.data);
        if (incomingMessage.channel_id === selectedChannelId){
            addMessage(incomingMessage);
        }

    };

    socket.onclose = () => console.log('WebSocket соединение закрыто');
}

// Отправка сообщения
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (message && selectedChannelId) {

        const payload = {channel_id: selectedChannelId, text: message, params: null, recipient_id: null, sender_id: currentUserId};

        try {
            await fetch('/api/v1/messages', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            socket.send(JSON.stringify(payload));
            addMessage(payload, currentUserId);
            messageInput.value = '';
        } catch (error) {
            console.error('Ошибка при отправке сообщения:', error);
        }
    }
}

// Добавление сообщения в чат
function addMessage(message) {

    const messagesContainer = document.getElementById('messages');
    messagesContainer.insertAdjacentHTML('beforeend', createMessageElement(message));
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Создание HTML элемента сообщения
function createMessageElement(message) {
    const userID = currentUserId;
    const messageClass = userID === message.sender_id ? 'my-message' : 'other-message';

    return `<div class="message ${messageClass}">${message.text}${createWidgetElement(message.widget)}</div>`;
}

function createWidgetElement(widget){
    console.log(widget);
    return widget !== null ? `<div class="widget">${widget.body}</div>` : "";
}


// Запуск опроса новых сообщений
function startMessagePolling(channelId) {
    clearInterval(messagePollingInterval);
    messagePollingInterval = setInterval(() => loadMessages(channelId), 1000);
}

// Обработка нажатий на канал
function addChannelClickListeners() {
    document.querySelectorAll('.channel').forEach(item => {
        item.onclick = event => selectChannel(item.getAttribute('data-id'), item.textContent, event);
    });
}

// Первоначальная настройка событий нажатия на пользователей
addChannelClickListeners();

// Обновление списка пользователей
async function fetchChannels() {
    try {
        const response = await fetch('/api/v1/channels/my',{
            method: 'GET',
            headers: {'Content-Type': 'application/json'},
        });
        const channels = await response.json();
        const channelList = document.getElementById('channelList');

        // Очищаем текущий список пользователей
        channelList.innerHTML = '';

        // Генерация списка каналов
        channels.forEach(channel => {
            const channelElement = document.createElement('div');
            channelElement.classList.add('channel');
            channelElement.setAttribute('data-id', channel.id);
            channelElement.textContent = channel.name;
            channelList.appendChild(channelElement);
        });

        // Повторно добавляем обработчики событий для каждого пользователя
        addChannelClickListeners();
    } catch (error) {
        console.error('Ошибка при загрузке списка каналов:', error);
    }
}


document.addEventListener('DOMContentLoaded', fetchChannels);
setInterval(fetchChannels, 10000); // Обновление каждые 10 секунд

// Обработчики для кнопки отправки и ввода сообщения
document.getElementById('sendButton').onclick = sendMessage;

document.getElementById('messageInput').onkeypress = async (e) => {
    if (e.key === 'Enter') {
        await sendMessage();
    }
};
