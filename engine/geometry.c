#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include "geometry.h"

rot_matrix_t rot_matrix[] =
{
	{ 1., 0., 1., 0.},
	{ 0.,-1., 1., 0.},
	{-1., 0.,-1., 0.},
	{ 0., 1.,-1., 0.},
};


/* check if a point is inside the box */
int point_inside_box(point_t* point, box_t* box)
{
	if (point->x>=box->xmin && point->x<=box->xmax &&
		point->y>=box->ymin && point->y<=box->ymax)
		return 1;

	return 0;
}

/* check if a polygon is inside a box */
int polygon_inside_box(polygon_t* pgon, box_t* box)
{
	for(int i=0; i<pgon->len-1; i++)
		if (!point_inside_box(&pgon->poly[i], box))
			return 0;

	return 1;
}

/* check if p is inside poly */
int point_inside_polygon(point_t *q, polygon_t* pgon)
{
int i, count = 0;
point_t *p = pgon->poly;
double ax, ay, bx, by, dd;
double xp = q->x;
double yp = q->y;

	for(i=0; i<pgon->len-1; i++)
	{
		ax = p[i].x;
		ay = p[i].y;
		bx = p[i+1].x;
		by = p[i+1].y;

		if ((ay>yp && by>yp) || (ay<yp && by<yp))
			continue;

		/* sidestep cases of alignment */
		if (ay==yp || by==yp) {
			yp += EPS;
			return point_inside_polygon(&(point_t){xp, yp}, pgon);
		}

		dd = (bx - ax)*(yp - ay) - (xp - ax)*(by - ay);
		if ((dd>0 && by>ay) || (dd<0 && by<ay))
			count++;
	}
	return (count % 2) == 1;
}


/* check if the line "a" crosses or not line "b" */
int cross(point_t* a, point_t* b)
{
	double dd, dt, ds;
	double dax, day, dbx, dby, d0x, d0y;

	/* differentials */
	dax = a[1].x - a[0].x;
	day = a[1].y - a[0].y;
	dbx = b[1].x - b[0].x;
	dby = b[1].y - b[0].y;
	d0x = a[0].x - b[0].x;
	d0y = a[0].y - b[0].y;

	/* determinants */
	dd = -dax * dby + dbx * day;
	dt =  d0x * dby - dbx * d0y;
	ds = -dax * d0y + d0x * day;


	//printf("dd=%lf ds=%lf dt=%lf\n", dd, ds, dt);

	if ( ((ds==0 || ds==dd) && (0<=dt && dt<=dd)) ||
		 ((dt==0 || dt==dd) && (0<=ds && ds<=dd)))
		return TOUCH;

	if (dd==0)
		return NO_CROSS;

	if (dd<0)
		return ((dd<ds) && (ds<0) && (dd<dt) && (dt<0))?CROSS:NO_CROSS;
	else
		return ((0<ds) && (ds<dd) && (0<dt) && (dt<dd))?CROSS:NO_CROSS;
}


/* check if the box is inside (mode==INSIDE), outside 
 * (mode==OUTSIDE) or intersect (mode==INTERSECT) the polygon */
int check_box(int mode, box_t* bb, polygon_t* pgon)
{
double x, y;
point_t centre;
point_t vbox[5];
int i,j,res;

	centre = (point_t){(bb->xmin+bb->xmax)/2, 
                     (bb->ymin+bb->ymax)/2};

	res = point_inside_polygon(&centre, pgon);

	if ((mode==INSIDE && !res) ||
		(mode==OUTSIDE && res))
		return 0;

	vbox[0] = (point_t){bb->xmin+2*EPS, bb->ymin};
	vbox[1] = (point_t){bb->xmin+2*EPS, bb->ymax};
	vbox[2] = (point_t){bb->xmax, bb->ymax};
	vbox[3] = (point_t){bb->xmax, bb->ymin};
	vbox[4] = vbox[0];

	for(i=0; i<pgon->len-1; i++) {
		x = pgon->poly[i].x;
		y = pgon->poly[i].y;
		if (bb->xmin<x && x<bb->xmax && 
			bb->ymin<y && y<bb->ymax)
			return 0; 

		for(j=0; j<4; j++) {

			res = cross(&pgon->poly[i], &vbox[j]);

			if (res == CROSS)
				return mode==INTERSECT;
		}
	}

	return mode!=INTERSECT;
} 


void bounding_box(polygon_t* pgon, box_t* bb)
{
double x,y;
double xmin, xmax, ymin, ymax;
int i;

	xmin = xmax = pgon->poly[0].x;
	ymin = ymax = pgon->poly[0].y;

	for(i=0; i<pgon->len-1; i++) {
		x = pgon->poly[i].x;
		y = pgon->poly[i].y;

		if (x<xmin)	xmin = x;
		if (x>xmax) xmax = x;
		if (y<ymin) ymin = y;
		if (y>ymax) ymax = y;
	}

	bb->xmin = xmin;
	bb->xmax = xmax;
	bb->ymin = ymin;
	bb->ymax = ymax;
}

point_t random_point(box_t* bb)
{
point_t p;

	p.x = drand48()*(bb->xmax-bb->xmin)+bb->xmin;
	p.y = drand48()*(bb->ymax-bb->ymin)+bb->ymin;

	return p;
}


box_t box_point(point_t point, double size)
{
	box_t box;
	box.xmin = point.x - size/2;
	box.xmax = point.x + size/2;
	box.ymin = point.y - size/2;
	box.ymax = point.y + size/2;

	return box;
}


int self_intersect(polygon_t* pgon)
{
int i, j;
point_t *a, *b;

	for(i=2; i<pgon->len-1; i++) {
		for(j=0; j<i-1; j++) {
			a = &pgon->poly[i];
			b = &pgon->poly[j];
			if (cross(a, b) == CROSS)
				return 1;
		}
	}
	return 0;
}

double hdist(point_t* q, polygon_t* pgon)
{
int i;
point_t *p = pgon->poly;
double ax, ay, bx, by;
double xp = q->x;
double yp = q->y;
double d, dmin;

	dmin = INFINITY;

	for(i=0; i<pgon->len-1; i++)
	{
		ax = p[i].x;
		ay = p[i].y;
		bx = p[i+1].x;
		by = p[i+1].y;

		if ((ay>yp && by>yp) || (ay<yp && by<yp))
			continue;

		if (ay==by) {
			/* point aligned with line */
			d = MIN(fabs(bx-xp), fabs(ax - xp));
		} else {
			/* denom cannot be zero */
			d = fabs(ax-xp+(yp-ay)*(bx-ax)/(by-ay));
		}

		dmin = MIN(dmin, d);
	}
	return dmin;
}

double area_polygon(polygon_t* pgon)
{
int i;
double area_tot = 0.;
point_t a, b;

	for(i=0; i<pgon->len-1; i++){
		a = pgon->poly[i];
		b = pgon->poly[i+1];
		area_tot += 0.5 * (b.x - a.x) * (b.y + a.y);
	}

	return fabs(area_tot);
}

void copy_polygon(polygon_t* poly_in, polygon_t* poly_out)
{
int len;

	len = poly_out->len = poly_in->len;

	poly_out->poly = malloc(len*sizeof(point_t));
	for(int i=0; i<len; i++)
		poly_out->poly[i] = poly_in->poly[i];

}

void free_polygon(polygon_t* poly)
{
	free(poly->poly);
	free(poly);
}


void init_grid(grid_t* grid)
{
polygon_t* poly = grid->poly;
box_t* box = &grid->box;
double xlen, ylen, x_step, y_step;
int rows, cols;

	bounding_box(poly, box);

	xlen = box->xmax - box->xmin;
	ylen = box->ymax - box->ymin;
	x_step = grid->x_step;
	y_step = grid->y_step;
	rows = grid->rows = 1 + ylen/y_step;
	cols = grid->cols = 1 + xlen/x_step;

	grid->origin = (point_t){
		box->xmin + (xlen - x_step*(cols-1))/2,
		box->ymin + (ylen - y_step*(rows-1))/2 };

	grid->_gridh = malloc(cols*rows);
	grid->_gridv = malloc(cols*rows);
	grid->bounds = malloc(rows*sizeof(uint32_t)*2);
	grid->gaps   = malloc(cols*rows*sizeof(uint32_t));
	grid->flags  = malloc(cols*rows*sizeof(uint16_t));

	memset(grid->_gridh, 0, cols*rows);
	memset(grid->_gridv, 0, cols*rows);
	memset(grid->gaps, 0xFF, cols*rows*sizeof(uint32_t));
	memset(grid->flags, 0, cols*rows*sizeof(uint16_t));

	uint32_t (*bounds)[2] = grid->bounds;
	for(int i=0; i<rows; i++) {
		bounds[i][0] = cols-1;
		bounds[i][1] = 0;
	}
		
}

void update_grid(grid_t* grid, int do_gaps)
{
polygon_t* poly = grid->poly;
point_t orig, *p = poly->poly;
double x_step, y_step, x, y;
int rows, cols, i1, j1;
uint32_t gap;
double xmin, xmax, ymin, ymax;
int x_cm, x_step_cm = grid->x_step;

	x_step = grid->x_step;
	y_step = grid->y_step;
	rows = grid->rows;
	cols = grid->cols;
	orig = grid->origin;

	uint8_t (*gh)[cols] = grid->_gridh;
	uint8_t (*gv)[cols] = grid->_gridv;
	uint32_t (*bounds)[2] = grid->bounds;
	uint32_t (*gaps)[cols] = grid->gaps;

	for(int k=0; k<poly->len-1; k++)
	{
		xmin = MIN(p[k].x, p[k+1].x);
		xmax = MAX(p[k].x, p[k+1].x);
		ymin = MIN(p[k].y, p[k+1].y);
		ymax = MAX(p[k].y, p[k+1].y);

		if (ymin==ymax)
			goto next;

		for(int i=0; i<rows; i++)
		{
			y = orig.y + i * y_step;

			if (y<ymin || y>ymax || y==p[k+1].y)
				continue;

			/* calculate crossing point x */
			if (y==p[k].y)
				x = p[k].x;
			else 
				if (xmin == xmax)
					x = xmin;
				else {
					x = (y-p[k].y)*p[k+1].x - (y-p[k+1].y)*p[k].x;
					x /= p[k+1].y - p[k].y;
				}

			j1 = (x-orig.x)/x_step;

			if (do_gaps) {
				bounds[i][0] = MIN(j1, bounds[i][0]);
				bounds[i][1] = MAX(j1, bounds[i][1]);
			}

			for(int j=0; j<=MIN(j1,cols-1); j++)
				gh[i][j]++;

			if (do_gaps) {
				x_cm = x - orig.x;
				for(int j=0; j<cols; j++) {
					gap =  abs(x_cm-j*x_step_cm);
					if (gap < gaps[i][j])
						gaps[i][j] =  gap;
				}
			}
		}

next:
		if (xmin==xmax)
			continue;

		for(int j=0; j<cols; j++)
		{
			x = orig.x + j * x_step;

			if (x<xmin || x>xmax || x==p[k+1].x)
				continue;

			/* calculate crossing point y */
			if (x==p[k].x)
				y = p[k].y;
			else 
				if (ymin == ymax)
					y = ymin;
				else {
					/* x = (y-p[k].y)*p[k+1].x - (y-p[k+1].y)*p[k].x; */
					y = (x-p[k].x)*p[k+1].y - (x-p[k+1].x)*p[k].y;
					y /= p[k+1].x - p[k].x;
				}

			i1 = (y-orig.y)/y_step;

			for(int i=0; i<=MIN(i1,rows-1); i++)
				gv[i][j]++;

		}
	}

	
	/* for(int i=0; i<rows; i++) { */
	/* 		printf("%d\n", (int)bounds[i][1]); */
	/* 			/1* bounds[i][1]); *1/ */
	/* } */
}

void free_grid(grid_t* grid)
{
	free(grid->_gridh);
	free(grid->_gridv);
	free(grid->bounds);
	free(grid->gaps);
	free(grid->flags);
}

point_t rotate(point_t point, uint32_t rot)
{
	point_t result;
	rot_matrix_t* r = &rot_matrix[rot];

	result.x = r->r00 * point.x + r->r01 * point.x;
	result.y = r->r10 * point.y + r->r11 * point.y;

	return result;
}


