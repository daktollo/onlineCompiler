FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

# COPY . .  # Commented out for development - using volume mount instead

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
