#include "geometry.h"

/* check if p is inside poly */
int inside(point *q, polygon* pgon)
{
int i, count = 0;
point *p = pgon->poly;
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
			return inside(&(point){xp, yp}, pgon);
		}

		dd = (bx - ax)*(yp - ay) - (xp - ax)*(by - ay);
		if ((dd>0 && by>ay) || (dd<0 && by<ay))
			count++;
	}
	return (count % 2) == 1;
}


int cross(point* a, point* b)
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



int check_box(int mode, box* bb, polygon* pgon)
{
double x, y;
point centre;
point vbox[5];
int i,j,res;

	centre = (point){(bb->xmin+bb->xmax)/2, 
                     (bb->ymin+bb->ymax)/2};

	res = inside(&centre, pgon);

	if ((mode==INSIDE && !res) ||
		(mode==OUTSIDE && res))
		return 0;

	vbox[0] = (point){bb->xmin+2*EPS, bb->ymin};
	vbox[1] = (point){bb->xmin+2*EPS, bb->ymax};
	vbox[2] = (point){bb->xmax, bb->ymax};
	vbox[3] = (point){bb->xmax, bb->ymin};
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


void bounding_box(polygon* pgon, box* bb)
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


double hdist(point* q, polygon* pgon)
{
int i;
point *p = pgon->poly;
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

int fit(point* p, room* r)
{
int i;
box panel;

	/* build box */			
	panel.xmin = p->x;
	panel.xmax = p->x+100;
	panel.ymin = p->y;
	panel.ymax = p->y+60;

	/* check if inside room */
	if (!check_box(INSIDE, &panel, &r->walls))
		return 0;

	/* check if outside obstacles */
	for(i=0; i<r->obs_num; i++)
		if (!check_box(OUTSIDE, &panel, &(r->obstacles[i])))
			return 0;

	return 1;
}


int gap_is_okay(point *q, room *r)
{
int i;

	for(i=0; i<4; i++)
		if (hdist(&q[i], &(r->walls))<20.0)
			return 0;

	return 1;
}



