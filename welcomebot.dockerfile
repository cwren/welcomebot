FROM python:3.14-slim
 
# Set the working directory in the container to /app
WORKDIR /home
ENV HOME=/home
 
# Install any necessary dependencies
RUN pip install --no-cache-dir welcomebot
 
# Run the command to start the application when the container starts
# the python file to run is called "main.py"
CMD ["python", "-m", "welcomebot"]