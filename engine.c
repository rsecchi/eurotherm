#include <stdio.h>

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


int cross(point* a, point* b)
{

	double dax = a[1].x - a[0].x;
	double day = a[1].y - a[0].y;
	double dbx = b[1].x - b[0].x;
	double dby = b[1].y - b[0].y;

	double d0x = a[0].x - b[0].x;
	double d0y = a[0].y - b[0].y;


	double dd = -dax * dby + dbx * day;
	double dt =  d0x * dby - dbx * d0y;
	double ds = -dax * d0y + d0x * day;

	printf("dd=%lf\n", dd);
	printf("dd=%lf\n", ds);
	printf("dd=%lf\n", dt);

	if (dd!=0) {
		printf("s=%lf\n", ds/dd);
		printf("t=%lf\n", dt/dd);
	}

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



int main() {
	printf("HW\n");
	point l0[2] = {{0,1}, {0,0}};
	point l1[2] = {{1,1},{1,0}};
	cross(l0, l1);
}



