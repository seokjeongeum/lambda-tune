FROM ubuntu:20.04

# Set environment variables so that the locale is used system-wide
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PGPASSWORD=your_new_password

# Keep the container running by tailing /dev/null indefinitely.
CMD ["tail", "-f", "/dev/null"]
