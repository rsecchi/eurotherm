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

