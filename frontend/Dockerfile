FROM node:20-alpine AS base

WORKDIR /app

# 의존성 설치
COPY package.json package-lock.json* ./
RUN npm install

# 소스 복사
COPY . .

EXPOSE 3000

# 개발 모드 (hot reload)
CMD ["npm", "run", "dev"]
