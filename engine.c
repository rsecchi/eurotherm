#include <stdio.h>
#include <stdlib.h>
#define EPS 1e-6

#define NO_CROSS 0
#define CROSS    1
#define TOUCH    2

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

		if (ay>yp && by>yp || ay<yp && by<yp)
			continue;

		/* sidestep cases of alignment */
		if (ay==yp || by==yp) {
			yp += EPS;
			return inside(&(point){xp, yp}, pgon);
		}

		dd = (bx - ax)*(yp - ay) - (xp - ax)*(by - ay);
		if (dd>0 && by>ay || dd<0 && by<ay)
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

	/*
	printf("dax=%lf\n", dax);
	printf("day=%lf\n", day);
	printf("dbx=%lf\n", dbx);
	printf("dby=%lf\n", dby);
	printf("d0x=%lf\n", d0x);
	printf("d0y=%lf\n", d0y);
	*/

	/* determinants */
	dd = -dax * dby + dbx * day;
	dt =  d0x * dby - dbx * d0y;
	ds = -dax * d0y + d0x * day;

	if (dd==0)
		return NO_CROSS;

	if (ds==0 || dt==0)
		return TOUCH;

	if (dd<0) 
		return ((dd<ds) && (ds<0) && (dd<dt) && (dt<0))?CROSS:NO_CROSS;
	else 
		return ((0<ds) && (ds<dd) && (0<dt) && (dt<dd))?CROSS:NO_CROSS;

}



void grid(room r)
{
int i,j;
double x,y;

polygon* obs;

	printf("WALLS\n");
	for(int i=0; i<r.walls.len; i++) {
		x = r.walls.poly[i].x;
		y = r.walls.poly[i].y;
		printf("%d. %lf %lf\n", i, x, y);
	}
	printf("OBSTACLES\n");
	for(i=0; i<r.obs_num; i++) {
		obs = &(r.obstacles[i]);
		for(j=0; j<obs->len; j++){
			x = obs->poly[j].x;
			y = obs->poly[j].y;
			printf("%d. %lf %lf\n", j, x, y);
		}
	}

}



int is_box_inside(box* bb, polygon* pgon)
{
double x, y;
point centre;
point vbox[5];
int i,j,res,t;

	centre = (point){(bb->xmin+bb->xmax)/2, 
                     (bb->ymin+bb->ymax)/2};

	if (!inside(&centre, pgon))
		return 0;

	vbox[0] = (point){bb->xmin, bb->ymin};
	vbox[1] = (point){bb->xmin, bb->ymax};
	vbox[2] = (point){bb->xmax, bb->ymax};
	vbox[3] = (point){bb->xmax, bb->ymin};
	vbox[4] = vbox[0];

	for(i=0; i<pgon->len-1; i++) {
		x = pgon->poly[i].x;
		y = pgon->poly[i].y;
		if (bb->xmin<x && x<bb->xmax && 
			bb->ymin<y && y<bb->ymax)
			return 0; 

		t = 0;
		for(j=0; j<4; j++) {

			res = cross(&pgon->poly[i], &vbox[j]);

			if (res == CROSS)
				return 0;

			if (res == TOUCH) {
				t++;
				if (t>1)
					return 0;
			}
		}
	}

	return 1;

} 


void print_banner()
{
	printf("OK\n");
}

int main() {

	polygon pgon;
	box mbox;

	pgon.poly = (point*)malloc(7*sizeof(point));
	pgon.poly[0] = (point){0,0};
	pgon.poly[1] = (point){1,0};
	pgon.poly[2] = (point){1,1};
	pgon.poly[3] = (point){2,1};
	pgon.poly[4] = (point){2,2};
	pgon.poly[5] = (point){0,2};
	pgon.poly[6] = (point){0,0};
	pgon.len = 7;

	mbox.xmin = 1.7;
	mbox.xmax = 2.01;
	mbox.ymin = 1.7;
	mbox.ymax = 2;

	if (is_box_inside(&mbox, &pgon)) {
		printf("INSIDE\n");
	} else {
		printf("OUTSIDE\n");
	}

}



