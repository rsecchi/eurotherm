#include <stdlib.h>
#include <stdio.h>
#include "geometry.h"


canvas_t _canvas;

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

/* Drawing primitives */
cairo_t* init_cairo() {

    cairo_surface_t *surface;
    cairo_t *cr;
   
    surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, WIDTH, HEIGHT);
    cr = cairo_create(surface);

    // Set background color
    cairo_set_source_rgb(cr, 1.0, 1.0, 1.0); // White
    cairo_paint(cr);

    // Set drawing color
    cairo_set_source_rgb(cr, 0.0, 0.0, 0.0); // Black

    return cr;
}


void draw_polygon(canvas_t *ct, polygon_t* p, colour_t col) 
{

	cairo_t* cr = ct->cr;
	transform_t trsf = ct->trans;
	int i;

	cairo_set_source_rgb(cr, col.red, col.green, col.blue);
    cairo_move_to(cr, 
			p->poly[0].x*trsf.scale.x + trsf.origin.x, 
			p->poly[0].y*trsf.scale.y + trsf.origin.y);

    for (i = 1; i < p->len; i++) 
        cairo_line_to(cr, 
			p->poly[i].x*trsf.scale.x + trsf.origin.x, 
			p->poly[i].y*trsf.scale.y + trsf.origin.y); 

    //cairo_close_path(cr);
    cairo_stroke(cr);
}


void draw_box(canvas_t* ct, box_t* box, colour_t col)
{
polygon_t pgon;
point_t points[5];

	points[0] = (point_t){box->xmin, box->ymin};
	points[1] = (point_t){box->xmin, box->ymax};
	points[2] = (point_t){box->xmax, box->ymax};
	points[3] = (point_t){box->xmax, box->ymin};
	points[4] = points[0];

	pgon.len = 5;
	pgon.poly = (point_t*)points;

	draw_polygon(ct, &pgon, col);
}

void draw_point(canvas_t* ct, point_t point)
{
box_t box = box_point(point, 10);

	draw_box(ct, &box, RED);	
}

void save_png(canvas_t* ct, char* filename)
{
	cairo_t* cr = ct->cr;
	cairo_surface_t* surface = cairo_get_target(cr);
    cairo_surface_write_to_png(surface, filename);
}

canvas_t* init_canvas(transform_t trans)
{
	_canvas.cr = init_cairo();
	_canvas.trans = trans;
	return &_canvas;
}

void print_text(canvas_t* ct, char* text, int line)
{
	cairo_t* cr = ct->cr;
    cairo_set_source_rgb(cr, 0.0, 0.0, 0.0); // Black
	cairo_move_to(cr, 
			TEXT_OFFS_X, 
			TEXT_OFFS_Y + line*LINE_HEIGHT);
	cairo_show_text(cr, text);
	cairo_stroke(cr);
}
