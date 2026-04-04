# Stage 1: Base image
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./

# Stage 2: Development environment
FROM base AS development
# Install all dependencies (including devDependencies)
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Stage 3: Build the frontend for production
FROM base AS build
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm install
COPY . .
RUN npm run build

# Stage 4: Lightweight Production environment
FROM nginx:alpine AS production
# Copy the built React/Vite assets to NGINX
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
