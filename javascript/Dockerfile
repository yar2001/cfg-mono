FROM node:20

WORKDIR /app


COPY package.json yarn.lock ./

RUN npm config set registry https://registry.npm.taobao.org
RUN yarn install

COPY . .

CMD [ "yarn", "start" ]

