# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.11.4-slim-buster as build

# Set the working directory in the container
WORKDIR  /main

# Add current directory code to working directory
ADD . /main

RUN apt-get update
RUN apt-get install -f

# Download and install wget
RUN apt-get update && apt-get install -y wget

# Download geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz

# Extract geckodriver
RUN tar -xvzf geckodriver-v0.34.0-linux64.tar.gz

# Move geckodriver to a directory in the PATH
RUN su -
RUN mv geckodriver /usr/local/bin
RUN chmod +x /usr/local/bin/geckodriver
RUN apt-get update && apt-get install -y coreutils
RUN touch geckodriver.log
RUN chown root:root geckodriver.log
RUN chmod ugo+w geckodriver.log
RUN mkdir -p /var/www
RUN mkdir /var/www/.mozilla
RUN chown root:root /var/www/.mozilla
RUN mkdir /var/www/.cache
RUN chown root:root /var/www/.cache

# Cleanup unnecessary files
RUN rm geckodriver-v0.34.0-linux64.tar.gz

# Install necessary dependencies
#RUN apt-get update && \
#    apt-get install -y wget bzip2
#
## Download and install Firefox
#RUN wget 'https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US' -O firefox.tar.bz2 && \
#    tar xjf firefox.tar.bz2 && \
#    mv firefox /usr/bin && \
#    chmod +x /usr/bin/firefox
#
## Clean up unnecessary files
#RUN rm -f firefox.tar.bz2
#
## Set the PATH environment variable
#ENV PATH="/usr/local/bin:${PATH}"


RUN apt-get install -y firefox-esr

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
COPY requirements.txt /main
RUN pip install --no-cache-dir -r requirements.txt
#RUN pip install --upgrade selenium


# Copy the .env file into the image
COPY .env /main
COPY account_handler.py /main
COPY spreadsheet_handler.py /main
COPY logic_handler.py /main

# Make port 80 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
CMD ["python", "main.py"]

