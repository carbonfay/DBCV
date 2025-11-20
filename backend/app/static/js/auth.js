
const myHeaders = new Headers();
myHeaders.append("Accept", "application/json");


// Обработка кликов по вкладкам
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => showTab(tab.dataset.tab));
});

// Функция отображения выбранной вкладки
function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.form').forEach(form => form.classList.remove('active'));

    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}Form`).classList.add('active');
}

// Функция для валидации данных формы
const validateForm = fields => fields.every(field => field.trim() !== '');

// Функция для отправки запросов
const sendRequest = async (url, data) => {
    try {
        const authRequestOptions = {
          method: "POST",
          headers: myHeaders,
          body: data,
          // redirect: "follow"
        };
        const response = await fetch(url, authRequestOptions);
        console.log(response);
        const result = await response.json();
        if (response.ok) {
            alert(result.message || 'Операция выполнена успешно!');
            return result;
        } else {
            alert(result.message || 'Ошибка выполнения запроса!');
            return null;
        }
    } catch (error) {
        console.error("Ошибка:", error);
        alert('Произошла ошибка на сервере');
    }
};

// Функция для обработки формы
const handleFormSubmit = async (formType, url, fields) => {
    if (!validateForm(fields)) {
        alert('Пожалуйста, заполните все поля.');
        return;
    }
    var data = null;
    if (formType === 'login'){
        const urlencoded = new URLSearchParams();
        urlencoded.append("username", fields[0]);
        urlencoded.append("password", fields[1]);
        urlencoded.append("grant_type", "");
        urlencoded.append("scope", "");
        urlencoded.append("client_id", "");
        urlencoded.append("client_secret", "");
        data = await sendRequest(url, urlencoded);

    }
       // ? {username: fields[0], password: fields[1]}
       // : {username: fields[0], email: fields[1], name: fields[2], password: fields[3], password_check: fields[4]});
    if (data && formType === 'login') {
        window.location.href = '/chat';
    }
};

// Обработка формы входа
document.getElementById('loginButton').addEventListener('click', async (event) => {
    event.preventDefault();

    const username = document.querySelector('#loginForm input[name="username"]').value;
    const password = document.querySelector('#loginForm input[type="password"]').value;

    await handleFormSubmit('login', 'login/', [username, password]);
});

// Обработка формы регистрации
document.getElementById('registerButton').addEventListener('click', async (event) => {
    event.preventDefault();

    const email = document.querySelector('#registerForm input[type="email"]').value;
    const name = document.querySelector('#registerForm input[type="text"]').value;
    const password = document.querySelectorAll('#registerForm input[type="password"]')[0].value;
    const password_check = document.querySelectorAll('#registerForm input[type="password"]')[1].value;

    if (password !== password_check) {
        alert('Пароли не совпадают.');
        return;
    }

    await handleFormSubmit('register', 'register/', [email, name, password, password_check]);
});

