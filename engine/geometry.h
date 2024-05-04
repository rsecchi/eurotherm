#ifndef GEOM_H
#define GEOM_H

#include <cairo/cairo.h>
#include <math.h>
#include <stdint.h>

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
	polygon_t* poly;
	box_t box;
	point_t origin;
	double x_step, y_step;
	int cols, rows;
	void* _gridh;
	void* _gridv;
} grid_t;

typedef struct {
	uint32_t i, j;
	grid_t* grid;
} grid_pos_t;

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

#define TEXT_OFFS_X    10
#define TEXT_OFFS_Y    20
#define LINE_HEIGHT    10

#define RED    (colour_t){1., 0., 0.}
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
box_t box_point(point_t point, double size);

int self_intersect(polygon_t* pgon);
double area_polygon(polygon_t* pgon);
double hdist(point_t* p, polygon_t* pgon);

void build_grid(grid_t* grid);
void init_grid(grid_t* grid);
void update_grid(grid_t* grid);
void free_grid(grid_t* grid);

canvas_t* init_canvas(transform_t trfs);
void draw_polygon(canvas_t* ct, polygon_t* poly, colour_t col);
void draw_box(canvas_t* ct, box_t* box, colour_t col);
void draw_point(canvas_t* ct, point_t point);
void print_text(canvas_t* ct, char* text, int line);
void save_png(canvas_t* ct, char* filename);



#endif
