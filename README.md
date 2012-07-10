tw2vk
=====

Twitter to VKontakte translator

Транслирует твиты на стену вконтакта.
Нужны логин-пароль от вконтакта и id-secret от вконтактового приложения.
Все это забиваем в файлик settings.py как-то так:

	IKITO_USER_ID = '1234567'
	IKITO_VK_LOGIN = 'yourlogin'
	IKITO_VK_PASS = 'yourverysecretpassword'

	VK_APP_ID = '7654321'
	VK_APP_SECRET = 'QQQQ35QzEWRuDvJYwgDvx'
	TWITTER_LOGIN = 'twitter_username'

Вконтактовое приложение должно быть stand-alone, т.е. просто какбы десктопное приложение.
