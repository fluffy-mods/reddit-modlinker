FROM node:alpine

# set up directory structure
RUN mkdir /app
WORKDIR /app

# set up packages
ADD package.json /app
RUN npm install

# copy over the rest
ADD . /app

# run the app
EXPOSE 3000
CMD [ "npm", "start" ]

