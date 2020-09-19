FROM node:13.12.0-alpine
EXPOSE 3000 9229
# Create app directory
WORKDIR /NJIT-IT490/FRONTEND

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)

# install app dependencies
COPY package.json /NJIT-IT490/FRONTEND
COPY package-lock.json /NJIT-IT490/FRONTEND

RUN npm install --silent
RUN npm install react-scripts@3.4.1 -g --silent
# If you are building your code for production
# RUN npm ci --only=production

# Bundle app source
COPY . /NJIT-IT490/FRONTEND

CMD ./start.sh
#CMD [ "node", "/FRONTEND/app.js" ]
