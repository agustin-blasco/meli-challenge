# temp stage
FROM postgres:16.2-alpine3.19

RUN apk update && apk upgrade

WORKDIR /var/lib/postgresql/data/

# Set environment variables for the database
ENV POSTGRES_DB=challenge
ENV POSTGRES_USER=user
ENV POSTGRES_PASSWORD=password

# Expose the default postgres port
EXPOSE 5432