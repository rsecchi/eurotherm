

OBJS= engine.o geometry.o test_engine.o

LIBS= -lcairo -lm -lc
CFLAGS= -g


test_engine: ${OBJS} tags
	ctags -R .
	${CC} ${CFLAGS} ${OBJS} ${LIBS} -o test_engine

clean:
	${RM} ${OBJS} test_engine
	${RM} *.png 

run: test_engine
	./test_engine && timg polygon.png

tags:
	ctags -R .

print:
	a2ps engine.c --font-size=8 --columns=1 --portrait -o engine.ps
	ps2pdf engine.ps