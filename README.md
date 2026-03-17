# json-rpc mode for the signalbot library

sudo docker run -d  --name signal-api --restart=always -p 9922:8080  \      
     -v signal-state:/home/.local/share/signal-cli \
     -e 'MODE=json-rpc' bbernhard/signal-cli-rest-api

docker container stop  signal-api
docker container rm  signal-api   

# native mode for the pysignalclirestapi library

sudo docker run -d  --name signal-api --restart=always -p 9922:8080  \     
     -v signal-state:/home/.local/share/signal-cli \
     -e 'MODE=native' bbernhard/signal-cli-rest-api

