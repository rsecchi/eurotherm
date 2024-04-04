#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

#include "engine.h"

#define MIN_CORNERS   4 
#define MAX_CORNERS   8 
#define MIN_OBS       0
#define MAX_OBS       4
#define MIN_AREA     8.0
#define MIN_OBS_LEN   5
#define MAX_OBS_LEN  25

int compare(const void *a, const void *b) {
    double difference = (*(double*)a - *(double*)b);
    if (difference > 0) return 1;
    if (difference < 0) return -1;
    return 0;
}


void create_room(room_t* rm, int seed) {
int i;
int corners;

point_t poly[MAX_CORNERS*2 + 1];
point_t* obs_poly;
double angle[MAX_CORNERS];
int len;
polygon_t walls;

double areap;
double xmin_obs, ymin_obs, xlen_obs, ylen_obs;
box_t obs_box, walls_box;

	rm->walls.poly = NULL;
	rm->obs_num = 0;
	rm->obstacles = NULL;

	if (seed==0) {
		srandom(time(NULL));
		srand48(time(NULL));
	} else {
		srandom(seed);
		srand48(seed);
	}


	do {
		corners = random() % (MAX_CORNERS-MIN_CORNERS) + MIN_CORNERS;
		len = 2*corners + 1;

		for(i=0; i<corners; i++)
			angle[i] = 2 * M_PI * drand48(); 
		
		qsort(angle, corners, sizeof(double), compare);

		for(i=0; i<corners; i++){
			poly[2*i].x = 500*cos(angle[i]);
			poly[2*i].y = 400*sin(angle[i]);
		}
		poly[2*corners].x = poly[0].x;
		poly[2*corners].y = poly[0].y;
		for(i=0; i<corners; i++){
			poly[2*i+1].x = poly[2*i].x;
			poly[2*i+1].y = poly[2*(i+1)].y;
		}
		walls.poly = &poly[0];
		walls.len = len;
		areap = area_polygon(&walls)/10000;
	} while(self_intersect(&walls) || areap<MIN_AREA);

	rm->walls.len = len;
	rm->walls.poly = (point_t*)malloc(len*sizeof(point_t));
	for(i=0; i<len; i++)
		rm->walls.poly[i] = poly[i];

	
	bounding_box(&walls, &walls_box);
	rm->obs_num = random() % (MAX_OBS-MIN_OBS+1) + MIN_OBS;
	rm->obstacles = (polygon_t*)malloc(sizeof(polygon_t)*rm->obs_num);
	for(i=0; i<rm->obs_num; i++) {
		do {
			xmin_obs = drand48()*(walls_box.xmax-walls_box.xmin)+walls_box.xmin;
			ymin_obs = drand48()*(walls_box.ymax-walls_box.ymin)+walls_box.ymin;
			xlen_obs = drand48()*(MAX_OBS_LEN - MIN_OBS_LEN) + MIN_OBS_LEN;
			ylen_obs = drand48()*(MAX_OBS_LEN - MIN_OBS_LEN) + MIN_OBS_LEN;
			obs_box = (box_t){xmin_obs, xmin_obs+xlen_obs, 
							ymin_obs, ymin_obs+ylen_obs};
		} while(check_box(OUTSIDE, &obs_box, &walls));
		rm->obstacles[i].len = 5;
		obs_poly = rm->obstacles[i].poly = (point_t*)malloc(5*sizeof(point_t));

		obs_poly[0] = (point_t){obs_box.xmin, obs_box.ymin};
		obs_poly[1] = (point_t){obs_box.xmin, obs_box.ymax};
		obs_poly[2] = (point_t){obs_box.xmax, obs_box.ymax};
		obs_poly[3] = (point_t){obs_box.xmax, obs_box.ymin};
		obs_poly[4] = obs_poly[0]; 
	}

}

int main() {

room_t rand_room;
panel_t test_panel;
point_t pos;
box_t room_box;

	create_room(&rand_room, 25);

	transform_t trsf;
	trsf.origin = (point_t){320, 240};
	trsf.scale =(point_t){0.5, -0.5};
	canvas_t* cp = init_canvas(trsf);

	draw_room(cp, &rand_room);

	bounding_box(&rand_room.walls, &room_box);

	for(int i=0; i<NUM_PANEL_T; i++) {
		do {
			pos = random_point(&room_box);
			printf("%d, %lf %lf\n", i, pos.x, pos.y);
			panel(&test_panel, i, pos, DOWN); 
		} while(!fit(&test_panel, &rand_room));
		draw_panel(cp, &test_panel);
	}

	save_png(cp, "polygon.png");
}

