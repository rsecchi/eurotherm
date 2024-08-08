#ifndef ENGINE_H
#define ENGINE_H
#include <stdint.h>
#include "geometry.h"

#define PANEL_HEIGHT         60
#define PANEL_WIDTH         100

#define LUX_WIDTH           100.
#define LUX_HEIGHT           20.
#define EDGE                 10.
#define MAX_RAILS           256
#define MAX_LINES          2048
#define MAX_DORSALS         512
#define MAX_DORSAL_PANELS    64
#define MAX_LINE_SIZE        20
#define INTER_RAIL_GAP       50.
#define INTER_RAIL_STEPS     10
#define INTER_LINE_GAP        2
#define DIST_FROM_WALLS      18.
#define LID_STEPS            10

#define STEPS_RIGHT_GAP     200

#define NUM_OFFSETS          10
#define OFFSET_STEP           5.

#define HD_STEPS  PANEL_HEIGHT/INTER_LINE_GAP
#define INTER_DORSAL_GAP    16/INTER_LINE_GAP


#define ROTATE     0x00000001
#define INVERT     0x00000002
#define BACK_ROT   (ROTATE|INVERT)
#define ROT_MASK   (ROTATE|INVERT)
#define MIRROR     0x00000004



extern canvas_t* __debug_canvas;
extern int __max_row_debug;
extern uint32_t __score;

typedef struct {
	int enable_quarters;
} config_t;

extern config_t config;

typedef enum {
	FULL,    // panel 200 x 120 cm
	LUX,     // lux panel  200 x 120 cm
	SPLIT,   // panel 200 x 60  cm
	HALF,    // panel 100 x 120 cm
	QUARTER, // panel 100 x 60  cm
	NUM_PANEL_T
} ptype;

typedef enum {UP, DOWN} heading_t;
typedef enum {WIDE, NARROW} dorsal_width_t;

typedef struct{
	double width;
	double height; 
	double active_area;
	uint32_t score;
	uint32_t prev;
	char name[16];
	uint32_t x_steps;
	uint32_t y_steps;
	uint16_t done_fail;
	uint16_t done_ok;
} panel_desc_t;

extern panel_desc_t panel_desc[]; 

typedef struct{
	polygon_t walls;
	polygon_t* obstacles;
	int obs_num;
	point_t collector_pos;
} room_t;

typedef struct __panel {
	ptype type;
	point_t pos;
	grid_t* grid;
	uint32_t row;
	uint32_t col;
	heading_t heading;
	box_t pbox;
	uint32_t score;
	uint32_t orient_flags;
	uint32_t dorsal_row;
	struct __panel* next;
} panel_t;

typedef struct __dorsal {
	heading_t heading;
	dorsal_width_t width;
	uint32_t parity;
	panel_t panels[MAX_DORSAL_PANELS];
	int num_panels;
	uint32_t score;
	uint32_t offset_row;
	uint32_t offset_col;
	struct __dorsal* next;
} dorsal_t;

typedef struct {
	uint32_t score;
	dorsal_t* dorsal;
} dorsal_score_t;

typedef struct {
	room_t* room;
	grid_t wall_grid;
	uint32_t h_steps, v_steps;
	point_t offset;
	uint32_t offset_col;
	dorsal_t* _dors_up;
	dorsal_t* _dors_down;
	dorsal_score_t* _dorsal_score;
	dorsal_t* dorsals;
	double gap;
	panel_t* panels;
} allocation_t;



double active_area(panel_t*);
int fit(panel_t*, room_t*, uint16_t*);
int gap_ok(panel_t*, grid_pos_t, allocation_t*);

int count_panels(panel_t*);
void panel(panel_t*, ptype, grid_pos_t, heading_t);
uint32_t make_dorsal(allocation_t*, dorsal_t*);
uint32_t scanline(allocation_t*);
uint32_t search_offset(allocation_t*);
panel_t* panel_room(room_t*, uint32_t*);
panel_t* build_room(room_t*);

panel_t* copy_panels(allocation_t*);
void free_panels(panel_t*);

void draw_room(canvas_t*, room_t*);
void draw_panel(canvas_t*, panel_t*);
void draw_dorsal(canvas_t*, dorsal_t*);
void draw_panels(canvas_t*, panel_t*);

#endif
