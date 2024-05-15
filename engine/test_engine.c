#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>

#include "engine.h"

#define MIN_CORNERS   6 
#define MAX_CORNERS   12 
#define MIN_OBS       7
#define MAX_OBS       14
#define MIN_AREA     8.0
#define MIN_OBS_LEN   5
#define MAX_OBS_LEN  250

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
			poly[2*i].x = 800*cos(angle[i]);
			poly[2*i].y = 600*sin(angle[i]);
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
grid_t grid;
grid_pos_t pos;
uint16_t flags;

	//bounding_box(&room->walls, &box);
	grid.poly = &room->walls;
	init_grid(&grid);
	pos.grid = &grid;

	for(int i=0; i<NUM_PANEL_T; i++) {
		do {
			panel(&test_panel, i, pos, h); 
		} while(!fit(&test_panel, room, &flags));
		draw_panel(cp, &test_panel);
		//draw_point(cp, pos); 
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

	//dorsal.offset = (point_t){box.xmin,(box.ymin+box.ymax)/2};
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
	print_text(cp, buffer, 4);

	area = area_polygon(&room->walls)/10000;
	sprintf(buffer, "area = %6.2lf", area); 	
	printf("%6.2lf ", area); 	
	print_text(cp, buffer, 5);

	act_area = active_area(panels);
	sprintf(buffer, "active_ area = %.2lf", act_area); 
	printf("%.2lf ", act_area); 
	print_text(cp, buffer, 6);

	eff = 100*act_area/area;
	sprintf(buffer, "perc. active = %.2lf%%", eff);
	printf("%.2lf ", eff);
	print_text(cp, buffer, 7);
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

void test_panel_room(int argc, char* argv[], room_t* rand_room)
{
panel_t* panels;
polygon_t line;
box_t box;
char filename[256] = "polygon-";
char num_str[256];
char rows_str[256];
char score_str[256];
long int clock_time;

	line.len = 2;
	line.poly = malloc(2*sizeof(point_t));


	transform_t trsf;
	trsf.origin = (point_t){320, 240};
	trsf.scale =(point_t){0.3, -0.3};
	canvas_t* cp = init_canvas(trsf);

	__debug_canvas = cp;

	draw_room(cp, rand_room);

	clock_time = clock();
	panels = panel_room(rand_room);
	clock_time = clock() - clock_time;
	draw_panels(cp, panels);

	sprintf(num_str, "%04d", random_seed);
	sprintf(rows_str, "-%04d", __max_row_debug);
	sprintf(score_str, "score=%d", __score);

	printf("%d ", random_seed);
	strcat(filename, num_str); 
	strcat(filename, rows_str); 
	strcat(filename, ".png"); 
	print_text(cp, num_str, 0);

	sprintf(num_str, "time=%ld ms", clock_time/1000);
	printf("%ld", clock_time/1000);
	//printf("filename=%s time=%ld ms\n", filename, clock_time/1000);
	print_text(cp, num_str, 1);
	print_text(cp, rows_str, 2);
	print_text(cp, score_str, 3);
	print_summary(cp, rand_room, panels);

	int h = 2*__max_row_debug;
	bounding_box(&rand_room->walls, &box);
	line.poly[0] = (point_t){box.xmin, box.ymin + h};
	line.poly[1] = (point_t){box.xmax, box.ymin + h};

	draw_polygon(cp, &line, ORANGE);

	save_png(cp, filename);
	printf("\n");
	free_panels(panels);
}

void test_grid(int argc, char* argv[])
{
room_t rand_room;
char num_str[256];
long int clock_time;
point_t pp;
double x,y;

grid_t grid;

	create_room(&rand_room, atoi(argv[1]));

	transform_t trsf;
	trsf.origin = (point_t){320, 240};
	trsf.scale =(point_t){0.5, -0.5};
	canvas_t* cp = init_canvas(trsf);

	__debug_canvas = cp;

	draw_polygon(cp, &rand_room.walls, GREEN);

	grid.poly = &rand_room.walls;
	grid.x_step = INTER_LINE_GAP;
	grid.y_step = INTER_LINE_GAP;
	clock_time = clock();
	init_grid(&grid);	
	clock_time = clock() - clock_time;

	uint8_t (*cxs)[grid.cols] = grid._gridh;

	// printf("%d %d\n", grid.rows, grid.cols);
	for(int i=0; i<grid.rows; i++) {
		for(int j=0; j<grid.cols; j++) {
			//printf("cxs[%d][%d]=%d\n",i,j,cxs[i][j]);
			// printf("%d",cxs[i][j]);
			if (cxs[i][j] % 2) {
				x = grid.origin.x + grid.x_step * j;
				y = grid.origin.y + grid.y_step * i;
				pp.x = x;
				pp.y = y;

				//printf("%.2lf %.2lf\n", x, y);
				draw_point(cp, pp);
			}
		}
		//printf("\n");
	}
	sprintf(num_str, "%04d", random_seed);
	printf("%d ", random_seed);

	sprintf(num_str, "time=%ld ms", clock_time/1000);
	printf("(%ld ms)", clock_time/1000);
	//printf("filename=%s time=%ld ms\n", filename, clock_time/1000);
	print_text(cp, num_str, 1);
	printf("\n");
	save_png(cp, "grid.png");
	free_grid(&grid);
	free_room(&rand_room);
}

int main(int argc, char* argv[]) 
{
room_t rand_room;
box_t box;
int rows;

	if (argc!=2) {
		fprintf(stderr, "usage: %s <random_seed>\n", argv[0]);
		exit(1);
	}

	create_room(&rand_room, atoi(argv[1]));
	bounding_box(&rand_room.walls, &box);

	rows = MIN(400, (box.xmax-box.xmin)/2);
	printf("rows=%d\n", rows);	

	// test_line(argc, argv);
	// test_scanline(argc, argv);
	// test_search_offset(argc, argv);
	for(__max_row_debug=31; __max_row_debug<rows; __max_row_debug++) { 
	/* 	__max_row_debug = i; */
		/* __max_row_debug = 1000; */
		test_panel_room(argc, argv, &rand_room);
}
	//test_grid(argc, argv);
	free_room(&rand_room);
}

