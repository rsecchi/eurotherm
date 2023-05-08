#ifndef GEOM_H
#define GEOM_H

#include <math.h>

#define EPS 1e-6
#define NO_CROSS  0
#define CROSS     1
#define TOUCH     2

#define MAX(a,b)  (((a)>(b))?(a):(b))
#define MIN(a,b)  (((a)<(b))?(a):(b))

enum mode {INSIDE, OUTSIDE, INTERSECT};

typedef struct {
	double x, y;
} point;

typedef struct {
	point* poly;
	int len;
} polygon;

typedef struct {
	polygon walls;
	polygon* obstacles;
	int obs_num;
} room;

typedef struct {
	double xmin, xmax;
	double ymin, ymax;
} box;


int inside(point*q, polygon* pgon);
int cross(point* a, point* b);
int check_box(int mode, box* bb, polygon* pgon);
void bounding_box(polygon* pgon, box* bb);
double hdist(point* p, polygon* pgon);
int fit(point* p, room* r);
int gap_is_okay(point *q, room* r);

#endif
