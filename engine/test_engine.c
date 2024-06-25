#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>

#include "engine.h"


int _debug_animation = 1;
double min_range, max_range;

/* 15 m2 */
#define MIN_CORNERS   3 
#define MAX_CORNERS   6 

/* 36ms, 45ms */
/* #define MIN_CORNERS   6 */ 
/* #define MAX_CORNERS   12 */ 

#define MIN_OBS       12
#define MAX_OBS       12
#define MIN_AREA     8.0
#define MIN_OBS_LEN   10
#define MAX_OBS_LEN  130


/* 15 m2 */
/* #define ROOM_WIDTH   340 */
/* #define ROOM_HEIGHT  260 */

/* XX m2 */
#define ROOM_WIDTH   300
#define ROOM_HEIGHT  200

/* 36 m2 */
/* #define ROOM_WIDTH   420 */
/* #define ROOM_HEIGHT  380 */

/* 45 m2 */
/* #define ROOM_WIDTH   500 */
/* #define ROOM_HEIGHT  400 */

/* #define ROOM_WIDTH   800 */
/* #define ROOM_HEIGHT  600 */

/* 9ms, 15m2  */
#define ROOFVENTS       4

/* 36m2, 45m2  */
/* #define ROOFVENTS       3 */
#define ROOFVENT_SIZE  10.
#define DIVIDERS        4
#define DIV_THICKNESS  20.
#define DIV_LENGTH    120.


int random_seed;
int __add_obstacles;

int compare(const void *a, const void *b) {
    double difference = (*(double*)a - *(double*)b);
    if (difference > 0) return 1;
    if (difference < 0) return -1;
    return 0;
}


void create_room(room_t* rm, int seed) {
int i, k;
int corners;

point_t poly[MAX_CORNERS*2 + 1];
point_t* obs_poly;
double angle[MAX_CORNERS];
double collector_angle;
int len;
polygon_t walls;

double areap, target_area, scale;
double xmin_obs, ymin_obs, xlen_obs, ylen_obs;
box_t obs_box, walls_box;
int count=0;

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

	collector_angle = 2 * M_PI * drand48(); 
	rm->collector_pos.x = ROOM_WIDTH*cos(collector_angle);
	rm->collector_pos.y = ROOM_HEIGHT*sin(collector_angle);

	do {
		corners = random() % (MAX_CORNERS-MIN_CORNERS) + MIN_CORNERS;
		len = 2*corners + 1;

		for(i=0; i<corners; i++)
			angle[i] = 2 * M_PI * drand48(); 
		
		qsort(angle, corners, sizeof(double), compare);

		for(i=0; i<corners; i++){
			poly[2*i].x = ROOM_WIDTH*cos(angle[i]);
			poly[2*i].y = ROOM_HEIGHT*sin(angle[i]);
		}
		poly[2*corners].x = poly[0].x;
		poly[2*corners].y = poly[0].y;
		for(i=0; i<corners; i++){
			poly[2*i+1].x = poly[2*i].x;
			poly[2*i+1].y = poly[2*(i+1)].y;
		}
		if ((random()%2)==0) {
			k = 1 + random() % (len-2);
			for(i=k; i<len-1; i++)
				poly[i] = poly[i+1];
			walls.len = len-1;
		} else {
			walls.len = len;
		}
		walls.poly = &poly[0];
		areap = area_polygon(&walls)/10000;
	} while(self_intersect(&walls));

	rm->walls.len = len;
	rm->walls.poly = (point_t*)malloc(len*sizeof(point_t));
	for(i=0; i<len; i++)
		rm->walls.poly[i] = poly[i];

	target_area = min_range + drand48() * (max_range - min_range);
	scale = sqrt(target_area/areap);
	for(i=0; i<len; i++) {
		rm->walls.poly[i].x = scale*(rm->walls.poly[i].x);
		rm->walls.poly[i].y = scale*(rm->walls.poly[i].y);
	}
	areap = area_polygon(&rm->walls)/10000;

	if (!__add_obstacles) {
		rm->obs_num = 0;
		rm->obstacles = NULL;
		return;
	}

	bounding_box(&rm->walls, &walls_box);
	/* rm->obs_num = random() % (MAX_OBS-MIN_OBS+1) + MIN_OBS; */
	rm->obs_num = ROOFVENTS + DIVIDERS;
	rm->obstacles = (polygon_t*)malloc(sizeof(polygon_t)*rm->obs_num);
	for(i=0; i<rm->obs_num; i++) {
		do {
			count++;
			if (count==100) {
				rm->obs_num = 0;
				rm->obstacles = NULL;
				return;
			}
			xmin_obs = drand48()*(walls_box.xmax-walls_box.xmin)+walls_box.xmin;
			ymin_obs = drand48()*(walls_box.ymax-walls_box.ymin)+walls_box.ymin;
			// printf("%lf %lf\n", ymin_obs, xmin_obs);
			//xlen_obs = drand48()*(MAX_OBS_LEN - MIN_OBS_LEN) + MIN_OBS_LEN;
			//ylen_obs = drand48()*(MAX_OBS_LEN - MIN_OBS_LEN) + MIN_OBS_LEN;
			if ((i % 2)==0) {
				xlen_obs = DIV_THICKNESS;
				ylen_obs = DIV_LENGTH;
			} 

			if ((i % 2)==1) {
				xlen_obs = DIV_LENGTH;
				ylen_obs = DIV_THICKNESS;
			}

			if (i>=DIVIDERS) {
				xlen_obs = ROOFVENT_SIZE;
				ylen_obs = ROOFVENT_SIZE;
			}

			obs_box = (box_t){xmin_obs, xmin_obs+xlen_obs, 
							ymin_obs, ymin_obs+ylen_obs};
		} while(!check_box(INSIDE, &obs_box, &rm->walls));
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

void free_random_room(room_t* room)
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

	free_random_room(&rand_room);
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

	free_random_room(&rand_room);
}

void print_summary(canvas_t* cp, room_t* room, panel_t* panels)
{
	char buffer[256];
	double area, act_area, eff;

	sprintf(buffer, "#panels = %d", count_panels(panels));
	print_text(cp, buffer, 4);

	area = area_polygon(&room->walls)/10000;
	sprintf(buffer, "area = %6.2lf", area);
	printf("%7.2lf ", area);
	print_text(cp, buffer, 5);

	act_area = active_area(panels);
	sprintf(buffer, "active_ area = %.2lf", act_area); 
	printf("%8.2lf ", act_area); 
	print_text(cp, buffer, 6);

	eff = 100*act_area/area;
	sprintf(buffer, "perc. active = %.2lf%%", eff);
	printf("%8.2lf ", eff);
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
	free_random_room(&rand_room);
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
int k;
int panel_stats[NUM_PANEL_T];

	line.len = 2;
	line.poly = malloc(2*sizeof(point_t));

	transform_t trsf;
	trsf.origin = (point_t){320, 240};
	trsf.scale =(point_t){0.3, -0.3};
	canvas_t* cp = init_canvas(trsf);

	__debug_canvas = cp;

	draw_room(cp, rand_room);

	clock_time = clock();
	panels = build_room(rand_room);
	clock_time = clock() - clock_time;
	draw_panels(cp, panels);


	memset(panel_stats, 0, NUM_PANEL_T*sizeof(int));
	k = 0;
	for(panel_t* p=panels; p!=NULL; p=p->next) {
		k++;
		panel_stats[p->type]++;
	}
	if (_debug_animation)
		sprintf(num_str, "%04d-%04d", random_seed, __max_row_debug);
	else 
		sprintf(num_str, "%04d", random_seed);
	sprintf(rows_str, "-%04d", __max_row_debug);
	sprintf(score_str, "score=%d", __score);

	printf("%3d ", random_seed);
	strcat(filename, num_str); 
	strcat(filename, rows_str); 
	strcat(filename, ".png"); 
	print_text(cp, num_str, 0);

	sprintf(num_str, "time=%ld ms", clock_time/1000);
	printf("%5ld  ", clock_time/1000);
	//printf("filename=%s time=%ld ms\n", filename, clock_time/1000);
	print_text(cp, num_str, 1);
	print_text(cp, rows_str, 2);
	print_text(cp, score_str, 3);
	print_summary(cp, rand_room, panels);

	printf("%3d ", k);
	for(k=0; k<NUM_PANEL_T; k++)
		printf("%3d ", panel_stats[k]);

	int h = 2*__max_row_debug;
	bounding_box(&rand_room->walls, &box);
	line.poly[0] = (point_t){box.xmin, box.ymin + h};
	line.poly[1] = (point_t){box.xmax, box.ymin + h};

	if (random_seed<100) {
		save_png(cp, filename);
	}
	if (_debug_animation) {
		draw_polygon(cp, &line, ORANGE);
		save_png(cp, filename);
	}

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
	free_random_room(&rand_room);
}

int main(int argc, char* argv[]) 
{
room_t rand_room;
box_t box;
int rows;

	if (argc!=6) {
		fprintf(stderr, "usage: %s <random_seed> <quarters=0|1> <obstacles=0|1>" 
				 " <min_range> <max_range>\n", argv[0]);
		exit(1);
	}

	config.enable_quarters = atoi(argv[2]);
	__add_obstacles = atoi(argv[3]);

	min_range = atof(argv[4]);
	max_range = atof(argv[5]);

	create_room(&rand_room, atoi(argv[1]));
	bounding_box(&rand_room.walls, &box);

	// test_line(argc, argv);
	// test_scanline(argc, argv);
	// test_search_offset(argc, argv);

	if (_debug_animation) {
		rows = MIN(400, (box.xmax-box.xmin)/2);
		for(__max_row_debug=31; __max_row_debug<rows; __max_row_debug++) 
			test_panel_room(argc, argv, &rand_room);
	} else {
		__max_row_debug = 1000;
		test_panel_room(argc, argv, &rand_room);
	}

	//test_grid(argc, argv);
	free_random_room(&rand_room);
}

