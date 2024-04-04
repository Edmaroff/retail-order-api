<h1>API Сервис заказа товаров для розничных сетей</h1>

<hr>

<h2>Описание</h2>

<p>Проект представляет собой API-сервис для автоматизации процесса закупок в розничной торговой сети. 
Основной целью является создание платформы для эффективного взаимодействия между покупателями 
и продавцами через API-интерфейс. Сервис позволяет клиентам просматривать ассортимент товаров 
различных магазинов, формировать заказы, а продавцам - управлять своими товарами, обрабатывать 
заказы и контролировать продажи через единую систему.<p>

<p>Ключевыми задачами проекта являются: обеспечение удобного пользовательского опыта для 
покупателей и продавцов, автоматизация процессов закупок и продаж, повышение эффективности 
взаимодействия между участниками торговой сети, а также создание масштабируемой и гибкой платформы
для дальнейшего развития и интеграции с другими системами.<p>

<h3>Пользователи сервиса:</h3>

<h4>Клиент (покупатель):</h4>
<ul>
  <li>Авторизация, регистрация и восстановление пароля через API. Также поддерживается регистрация через Google и GitHub.</li>
  <li>Управление контактами (телефон, адрес) для оформления заказов.</li>
  <li>Работа с корзиной: добавление, изменение, чтение и удаление товаров.</li>
  <li>Возможность создания заказов, содержащих товары от различных магазинов.</li>
  <li>Просмотр оформленных заказов, списка всех товаров, подробной информации о товарах, а также активных магазинов.</li>
</ul>

<h4>Магазин (продавец):</h4>
<ul>
  <li>Регистрация, активация и аутентификация через API, аналогично клиентам.</li>
  <li>Управление магазином: создание, просмотр, изменение и удаление.</li>
  <li>Управление продуктами с возможностью добавления фотографии.</li>
  <li>Загрузка товаров в базу данных из файла YAML и их выгрузка из базы.</li>
  <li>Просмотр списка всех категорий и активных заказов для своего магазина.</li>
</ul>

<h3><a href="https://documenter.getpostman.com/view/25907870/2s9Ykn92Za">API Документация (Postman)</a></h3>
<h3><a href="https://github.com/Edmaroff/retail-order-api/blob/main/retail_order_api/data/shop_1.yaml">Пример файла YAML для импорта товаров</a></h3>

<details>
  <summary style="font-size: 1.3em;"><b>Схема базы данных</b></summary>
  <a href="https://drive.google.com/file/d/1z1P4F3oXjBnAK8kHxRroIrrPYS2sGIEr/view?usp=sharing" title='Python' target="_blank"><img src="https://github.com/Edmaroff/retail-order-api/blob/main/Схема_БД.jpg" alt="Схема БД"></a>
</details>


<details >
  <summary style="font-size: 1.3em;"><b>Используемые технологии</b></summary>
    <ul>
      <li>Django</li>
      <li>Django REST framework</li>
      <li>Celery</li>
      <li>Redis</li>
      <li>Djoser</li>
      <li>social_django</li>
      <li>Imagekit</li>
      <li>Pytest</li>
    </ul>
</details>
<hr>

<h2>Запуск проекта</h2>

<h3>Предварительная установка</h3>

<ol>
  <li>Клонируйте репозиторий:
    <pre><code>git clone https://github.com/Edmaroff/retail-order-api</code></pre>
  </li>
  <li>Перейдите в директорию проекта:
    <pre><code>cd retail-order-api/retail_order_api</code></pre>
  </li>
  <li>Настройте почтовый сервер по <a href="https://docs.djangoproject.com/en/5.0/topics/email/" target="_blank">SMTP</a></li>
  <li>Настройте OAuth приложения:
    <ul>
      <li><a href="https://console.cloud.google.com/" target="_blank">Google</a></li>
      <li><a href="https://github.com/settings/applications/new" target="_blank">GitHub</a></li>
    </ul>
  </li>
  <li>Создайте и заполните файл <code>.env</code> по шаблону <code>.env.template</code>. Файл <code>.env</code> должен находиться в одной директории с <code>manage.py</code>.</li>
</ol>

<h3>Запуск с Docker</h3>

<p>После выполнения шагов из раздела "Предварительная установка":</p>

<ol>
  <li>Соберите Docker-образ:
    <pre><code>docker-compose build</code></pre>
  </li>
  <li>Запустите контейнеры:
    <pre><code>docker-compose up</code></pre>
  </li>
</ol>

<h3>Локальный запуск</h3>

<p>После выполнения шагов из раздела "Предварительная установка":</p>

<ol>
  <li>Установите виртуальное окружение для проекта <code>venv</code> в директории проекта:
    <pre><code>python3 -m venv venv</code></pre>
  </li>
  <li>Активируйте виртуальное окружение:
    <pre><code>source venv/bin/activate</code></pre>
  </li>
  <li>Установите зависимости из <code>requirements.txt</code>:
    <pre><code>pip install -r requirements.txt</code></pre>
  </li>
  <li>Выполните миграции:
    <pre><code>python3 manage.py migrate</code></pre>
  </li>
  <li>Запустите Redis:
    <pre><code>redis-server</code></pre>
  </li>
  <li>Запустите Celery:
    <pre><code>python3 -m celery -A retail_order_api worker -l info</code></pre>
  </li>
  <li>Запустите сервер:
    <pre><code>python3 manage.py runserver</code></pre>
  </li>
</ol>

<p>Список эндпоинтов (документация Swagger) доступен по адресу: <code>http://127.0.0.1:8000/api/v1/schema/docs/</code></p>
<hr>