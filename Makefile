CC=gcc
CFLAGS=-shared -fPIC


all: engine.so

engine.so: engine.c
	$(CC) $(CFLAGS) -o $@  $< 

