CC=gcc
CFLAGS=-shared -fPIC -Wall


all: engine.so

clean:
	$(RM) engine.so

engine.so: engine.c
	$(CC) $(CFLAGS) -o $@  $< 

