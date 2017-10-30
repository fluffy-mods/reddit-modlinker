FROM node:alpine

# set up packages
ADD package.json .
RUN npm install

# copy over the rest
ADD . .

# run the app
EXPOSE 3000
CMD [ "npm", "start" ]

