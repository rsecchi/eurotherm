
SRC= engine.o geometry.o 
OBJS= $(SRC: %.c=%.o) 
SOBJS= $(SRC: %.c=%so)


LIBS= -lcairo -lm -lc
CFLAGS= -g


test_engine: ${OBJS} %.o
	ctags -R .
	${CC} ${CFLAGS} $^ ${LIBS} -o $@ 

%.so: %.o
	${CC} -shared -fPIC ${CFLAGS} $^ ${LIBS} -o $@ 

libplanner.so: ${SOBJS}
	ctags -R .
	${CC} -shared -fPIC ${CFLAGS} $^ ${LIBS} -o $@ 


test: ${OBJS} %.o libplanner.so
	ctags -R .
	${CC} ${CFLAGS} $^ ${LIBS} -o $@ 


clean:
	${RM} *.o *.so 
	${RM} *.png 

run: test_engine
	./test_engine && timg polygon.png

tags:
	ctags -R .

print:
	a2ps engine.c --font-size=8 --columns=1 --portrait -o engine.ps
	ps2pdf engine.ps
