#ifndef GEOM_H
#define GEOM_H

#include <stdint.h>

#define EPS 1e-6
#define NO_CROSS  0
#define CROSS     1
#define TOUCH     2

#define MAX(a,b)  (((a)>(b))?(a):(b))
#define MIN(a,b)  (((a)<(b))?(a):(b))

enum mode {INSIDE, OUTSIDE, INTERSECT};

typedef struct {
	double r00, r01, r10, r11;
} rot_matrix_t;

extern rot_matrix_t rot_matrix[];

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
	void* bounds;
	void* gaps;
	void* flags;
} grid_t;

typedef struct {
	uint32_t i, j;
	grid_t* grid;
} grid_pos_t;


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
void update_grid(grid_t* grid, int);
void free_grid(grid_t* grid);

void copy_polygon(polygon_t*, polygon_t*);
void free_polygon(polygon_t*);

point_t rotate(point_t point, uint32_t rot);


#endif
