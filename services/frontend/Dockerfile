FROM node:18-alpine

WORKDIR /app

COPY package.json .
run npm install

COPY . .

CMD ["npm", "run", "dev", "--", "--host"]
