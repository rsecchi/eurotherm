CC=gcc
CFLAGS=-shared -fPIC -Wall


all: engine.so

clean:
	$(RM) engine.so geometry.o

engine.so: engine2.c geometry.o
	$(CC) $(CFLAGS) -o $@ geometry.o  $< 

