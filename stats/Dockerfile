FROM node:alpine

# set up directory structure
RUN mkdir /app
WORKDIR /app

# set up packages
RUN npm install -g yarn
ADD package.json /app
RUN yarn install

# copy over the rest
ADD . /app

# run the app
EXPOSE 3000
CMD [ "npm", "start" ]

