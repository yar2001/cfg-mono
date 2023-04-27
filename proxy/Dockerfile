FROM node:20

RUN npm install -g pm2

WORKDIR /app


COPY package.json .yarnrc.yml yarn.lock ./
COPY .yarn .yarn
RUN yarn install 


COPY . .
RUN yarn build

ENV NODE_ENV=production
ENV TZ=Asia/Shanghai

CMD ["pm2-runtime", "start", "pm2.json"]