#ifndef GEOM_H
#define GEOM_H

#include <cairo/cairo.h>
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
} point_t;

typedef struct {
	point_t* poly;
	int len;
} polygon_t;

typedef struct {
	double xmin, xmax;
	double ymin, ymax;
} box_t;

typedef struct {
	point_t origin;
	point_t scale;
} transform_t;

typedef struct {
	double red, green, blue;
} colour_t;

typedef struct {
	cairo_t* cr;
	transform_t trans;
} canvas_t;

extern canvas_t _canvas;

// Drawing
#define WIDTH  640
#define HEIGHT 480

#define GREEN  (colour_t){0., 1., 0.}
#define BLUE   (colour_t){0., 0., 1.}
#define YELLOW (colour_t){1., 1., 0.}
#define BLACK  (colour_t){0., 0., 0.}

int point_inside_polygon(point_t*q, polygon_t* pgon);
int point_inside_box(point_t* point, box_t* box);
int polygon_inside_box(polygon_t* pgon, box_t* box);

int cross(point_t* a, point_t* b);
int check_box(int mode, box_t* bb, polygon_t* pgon);
void bounding_box(polygon_t* pgon, box_t* bb);
point_t random_point(box_t* bb);

int self_intersect(polygon_t* pgon);
double area_polygon(polygon_t* pgon);
double hdist(point_t* p, polygon_t* pgon);

canvas_t* init_canvas(transform_t trfs);
void draw_polygon(canvas_t* ct, polygon_t* poly, colour_t col);
void save_png(canvas_t* ct, char* filename);



#endif
