<h1>API Сервис заказа товаров для розничных сетей</h1>

<hr>

<h2>Описание</h2>

<p>Проект представляет собой API-сервис для автоматизации закупок в розничной сети. Основной целью является обеспечение взаимодействия между клиентами (покупателями) и магазинами (продавцами) через API запросы.</p>

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
