
SRC= engine.o geometry.o cairo_drawing.o
OBJS= $(SRC: %.c=%.o) 


LIBS= -lcairo -lm -lc
CFLAGS= -g -Wall -fPIC


all: libplanner.so test_engine 

test_engine: ${OBJS} test_engine.o
	${CC} ${CFLAGS} $^ ${LIBS} -o $@ 


libplanner.so: ${OBJS} planner.o
	${CC} -g -shared -fPIC ${CFLAGS} $^ ${LIBS} -o $@ 


clean:
	${RM} *.o *.so 
	${RM} *.png 

run: test_engine
	./test_engine 0 && timg polygon.png

tags:
	ctags -R .

print:
	a2ps engine.c --font-size=8 --columns=1 --portrait -o engine.ps
	ps2pdf engine.ps
