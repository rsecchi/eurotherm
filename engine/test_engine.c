#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>

#include "engine.h"

#define MIN_CORNERS   4 
#define MAX_CORNERS   8 
#define MIN_OBS       0
#define MAX_OBS       4
#define MIN_AREA     8.0
#define MIN_OBS_LEN   5
#define MAX_OBS_LEN  25

int random_seed;

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
		random_seed = random() % 10000;
	} else {
		random_seed = seed;
	}

	srandom(random_seed);
	srand48(random_seed);


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

void generate_random_panels(canvas_t* cp, room_t* room, heading_t h)
{
panel_t test_panel;
point_t pos;
box_t box;

	bounding_box(&room->walls, &box);
	for(int i=0; i<NUM_PANEL_T; i++) {
		do {
			pos = random_point(&box);
			printf("%d, %lf %lf\n", i, pos.x, pos.y);
			panel(&test_panel, i, pos, h); 
		} while(!fit(&test_panel, room));
		draw_panel(cp, &test_panel);
		draw_point(cp, pos); 
	}
}

void free_room(room_t* room)
{
	for(int i=0; i<room->obs_num; i++) 
		free(room->obstacles[i].poly);
	free(room->obstacles);

	free(room->walls.poly);
}

void test_line(int argc, char* argv[]) {
room_t rand_room;
dorsal_t dorsal;

allocation_t alloc;
box_t box;

	create_room(&rand_room, atoi(argv[1]));

	transform_t trsf;
	trsf.origin = (point_t){320, 240};
	trsf.scale =(point_t){0.5, -0.5};
	canvas_t* cp = init_canvas(trsf);

	__debug_canvas = cp;

	draw_room(cp, &rand_room);
	bounding_box(&rand_room.walls, &box);

	//generate_random_panels(cp, &rand_room, DOWN);

	alloc.room = &rand_room;

	dorsal.offset = (point_t){box.xmin,(box.ymin+box.ymax)/2};
	dorsal.width = rand() % 2;
	dorsal.heading = rand() % 2;
	
	make_dorsal(&alloc, &dorsal);
	draw_dorsal(cp, &dorsal);

	save_png(cp, "polygon.png");

	free_room(&rand_room);
}

void test_scanline(int argc, char* argv[]) {
room_t rand_room;
allocation_t alloc;
box_t box;

	create_room(&rand_room, atoi(argv[1]));

	transform_t trsf;
	trsf.origin = (point_t){320, 240};
	trsf.scale =(point_t){0.5, -0.5};
	canvas_t* cp = init_canvas(trsf);

	__debug_canvas = cp;

	draw_room(cp, &rand_room);
	bounding_box(&rand_room.walls, &box);

	alloc.gap = 0;
	alloc.offset = (point_t){box.xmin, box.ymin};
	alloc.room = &rand_room;
	scanline(&alloc);	

	save_png(cp, "polygon.png");

	free_room(&rand_room);
}

void print_summary(canvas_t* cp, room_t* room, panel_t* panels)
{
	char buffer[256];
	double area, act_area, eff;

	sprintf(buffer, "#panels = %d", count_panels(panels));
	print_text(cp, buffer, 2);

	area = area_polygon(&room->walls)/10000;
	sprintf(buffer, "area = %6.2lf", area); 	
	printf("%6.2lf ", area); 	
	print_text(cp, buffer, 3);

	act_area = active_area(panels);
	sprintf(buffer, "active_ area = %.2lf", act_area); 
	printf("%.2lf ", act_area); 
	print_text(cp, buffer, 4);

	eff = 100*act_area/area;
	sprintf(buffer, "perc. active = %.2lf%%", eff);
	printf("%.2lf ", eff);
	print_text(cp, buffer, 5);
}

void test_search_offset(int argc, char* argv[])
{
room_t rand_room;
allocation_t alloc;
char filename[256] = "polygon-";
char num_str[256];
long int clock_time;

	create_room(&rand_room, atoi(argv[1]));

	transform_t trsf;
	trsf.origin = (point_t){320, 240};
	trsf.scale =(point_t){0.5, -0.5};
	canvas_t* cp = init_canvas(trsf);

	__debug_canvas = cp;

	draw_room(cp, &rand_room);

	alloc.room = &rand_room;
	clock_time = clock();
	search_offset(&alloc);
	clock_time = clock() - clock_time;
	draw_panels(cp, alloc.panels);

	sprintf(num_str, "%04d", random_seed);
	printf("%d ", random_seed);
	strcat(filename, num_str); 
	strcat(filename, ".png"); 
	print_text(cp, num_str, 0);

	sprintf(num_str, "time=%ld ms", clock_time/1000);
	printf("%ld", clock_time/1000);
	//printf("filename=%s time=%ld ms\n", filename, clock_time/1000);
	print_text(cp, num_str, 1);
	print_summary(cp, &rand_room, alloc.panels);
	save_png(cp, filename);
	printf("\n");
	free_room(&rand_room);
}

void test_panel_room(int argc, char* argv[])
{
room_t rand_room;
panel_t* panels;
char filename[256] = "polygon-";
char num_str[256];
long int clock_time;

	create_room(&rand_room, atoi(argv[1]));

	transform_t trsf;
	trsf.origin = (point_t){320, 240};
	trsf.scale =(point_t){0.5, -0.5};
	canvas_t* cp = init_canvas(trsf);

	__debug_canvas = cp;

	draw_room(cp, &rand_room);

	clock_time = clock();
	panels = panel_room(&rand_room);
	clock_time = clock() - clock_time;
	draw_panels(cp, panels);

	sprintf(num_str, "%04d", random_seed);
	printf("%d ", random_seed);
	strcat(filename, num_str); 
	strcat(filename, ".png"); 
	print_text(cp, num_str, 0);

	sprintf(num_str, "time=%ld ms", clock_time/1000);
	printf("%ld", clock_time/1000);
	//printf("filename=%s time=%ld ms\n", filename, clock_time/1000);
	print_text(cp, num_str, 1);
	print_summary(cp, &rand_room, panels);
	save_png(cp, filename);
	printf("\n");
	free_room(&rand_room);
}
int main(int argc, char* argv[]) 
{

	if (argc!=2) {
		fprintf(stderr, "usage: %s <random_seed>\n", argv[0]);
		exit(1);
	}
	// test_line(argc, argv);
	// test_scanline(argc, argv);
	// test_search_offset(argc, argv);
	test_panel_room(argc, argv);
}

