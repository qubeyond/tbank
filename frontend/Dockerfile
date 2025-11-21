# Базовый образ Node.js для сборки
FROM node:18-alpine as build

# Рабочая директория в контейнере
WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm ci --only=production

# Копируем исходный код
COPY . .

# Собираем приложение
RUN npm run build

# Финальный образ с nginx для раздачи статики
FROM nginx:alpine

# Копируем собранное приложение в nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Копируем кастомную конфигурацию nginx (опционально)
# COPY nginx.conf /etc/nginx/nginx.conf

# Открываем порт 80
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]
